"""
Indian Railways Network Congestion & Schedule Efficiency Analytics
Data Preprocessing Pipeline

Dataset : DataMeet Indian Railways open data (https://github.com/datameet/railways)
          schedules.json, stations.json, trains.json
Run     : python src/preprocess.py   (from the project root)
"""
import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, MinMaxScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "processed")
FIG = os.path.join(ROOT, "outputs", "figures")
os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

LOG = []


def log(msg):
    print(msg)
    LOG.append(msg)


# ---------------------------------------------------------------- 1. INGESTION
def load_raw():
    sched = pd.DataFrame(json.load(open(os.path.join(RAW, "schedules.json"))))

    st = json.load(open(os.path.join(RAW, "stations.json")))["features"]
    stations = pd.DataFrame([{
        **f["properties"],
        "lon": f["geometry"]["coordinates"][0] if f["geometry"] else np.nan,
        "lat": f["geometry"]["coordinates"][1] if f["geometry"] else np.nan,
    } for f in st])

    tr = json.load(open(os.path.join(RAW, "trains.json")))["features"]
    trains = pd.DataFrame([f["properties"] for f in tr])
    log(f"[Ingest] schedules={sched.shape}, stations={stations.shape}, trains={trains.shape}")
    return sched, stations, trains


# ------------------------------------------------------------ 2. PROFILING
def profile(df, name):
    p = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "missing_pct": (df.isna().mean() * 100).round(2),
        "unique": df.nunique(),
    })
    p.to_csv(os.path.join(OUT, f"profile_{name}.csv"))
    return p


# ------------------------------------------------------------ 3. CLEANING
def to_minutes(t):
    """'HH:MM:SS' -> minutes since midnight; 'None'/invalid -> NaN"""
    if t is None or not isinstance(t, str) or t.strip() in ("None", "", "null"):
        return np.nan
    try:
        h, m, s = t.split(":")
        return int(h) * 60 + int(m) + int(s) / 60
    except ValueError:
        return np.nan


def clean_schedules(s):
    n0 = len(s)
    # 3a. Literal "None" strings -> real missing values
    s = s.replace({"None": np.nan, "": np.nan})
    log(f"[Clean] 'None' strings converted -> arrival NaN={s.arrival.isna().sum()}, departure NaN={s.departure.isna().sum()}")

    # 3b. Exact duplicates and duplicate (train, station, day) stops
    s = s.drop_duplicates()
    s = s.drop_duplicates(subset=["train_number", "station_code", "day", "arrival", "departure"])
    log(f"[Clean] duplicates removed: {n0 - len(s)}")

    # 3c. Rows with neither arrival nor departure carry no timing info
    both = s.arrival.isna() & s.departure.isna()
    s = s[~both]
    log(f"[Clean] rows with no arrival & no departure dropped: {both.sum()}")

    # 3d. Standardise text columns
    s["station_code"] = s["station_code"].str.strip().str.upper()
    s["station_name"] = s["station_name"].str.strip().str.title()
    s["train_name"] = s["train_name"].str.strip()
    s["train_number"] = s["train_number"].astype(str).str.strip()

    # 3e. Type conversion: clock strings -> numeric minutes
    s["arr_min"] = s["arrival"].map(to_minutes)
    s["dep_min"] = s["departure"].map(to_minutes)
    s["day"] = pd.to_numeric(s["day"], errors="coerce")
    s = s.dropna(subset=["day"])
    s["day"] = s["day"].astype(int)
    return s


def clean_stations(st):
    n0 = len(st)
    st = st[~st["code"].str.startswith("XX-", na=False)]   # placeholder codes
    st = st.drop_duplicates(subset="code")
    st["code"] = st["code"].str.strip().str.upper()
    # Coordinates outside India's bounding box are treated as errors
    bad = ~st.lat.between(6, 37.5) | ~st.lon.between(68, 98)
    st.loc[bad, ["lat", "lon"]] = np.nan
    # KNN imputation of missing state/zone from the 5 nearest stations with known values
    from sklearn.neighbors import KNeighborsClassifier
    for col in ["state", "zone"]:
        known = st[col].notna() & st.lat.notna()
        target = st[col].isna() & st.lat.notna()
        if target.any():
            knn = KNeighborsClassifier(n_neighbors=5).fit(st.loc[known, ["lat", "lon"]], st.loc[known, col])
            st.loc[target, col] = knn.predict(st.loc[target, ["lat", "lon"]])
            log(f"[Impute] {col}: {target.sum()} values filled by 5-NN on coordinates")
    # Remaining (no coordinates) -> 'Unknown'
    st["state"] = st["state"].fillna("Unknown")
    st["zone"] = st["zone"].fillna("Unknown")
    log(f"[Clean] stations: {n0} -> {len(st)} (placeholder/duplicate codes removed); "
        f"missing coords={st.lat.isna().sum()}")
    return st


# ------------------------------------------------------------ 4. INTEGRATION + 5. FEATURE ENGINEERING
def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def engineer(s, st, trains):
    # Absolute time across multi-day journeys
    s["arr_abs"] = s["arr_min"] + (s["day"] - 1) * 1440
    s["dep_abs"] = s["dep_min"] + (s["day"] - 1) * 1440

    # Halt duration at a station (handles midnight roll-over)
    halt = s["dep_min"] - s["arr_min"]
    halt = np.where(halt < 0, halt + 1440, halt)
    s["halt_min"] = halt
    # Zero-halt intermediate rows are pass-through timing points, not commercial stops
    s["timing_point"] = (s["halt_min"] == 0)

    # Stop role
    s["stop_type"] = np.select(
        [s.arrival.isna(), s.departure.isna()], ["Origin", "Destination"], "Intermediate")

    # Hour of activity (departure, else arrival) and time-of-day band
    s["event_min"] = s["dep_min"].fillna(s["arr_min"])
    s["hour"] = (s["event_min"] // 60).astype(int)
    s["time_band"] = pd.cut(s["hour"], [-1, 5, 11, 16, 20, 23],
                            labels=["Night", "Morning", "Afternoon", "Evening", "Late-Evening"])

    # Integrate station attributes
    s = s.merge(st[["code", "state", "zone", "lat", "lon"]],
                left_on="station_code", right_on="code", how="left").drop(columns="code")
    log(f"[Integrate] stop rows without station match: {s.lat.isna().sum()} "
        f"({s.lat.isna().mean()*100:.1f}%)")

    # Integrate train attributes
    tcols = ["number", "type", "zone", "distance", "duration_h", "duration_m"]
    t = trains[tcols].drop_duplicates("number").rename(
        columns={"number": "train_number", "type": "train_type", "zone": "train_zone",
                 "distance": "route_km"})
    s = s.merge(t, on="train_number", how="left")
    s["train_type"] = s["train_type"].replace("", np.nan).fillna("Unknown")

    # Order stops within each train and compute segment-level features
    s["sort_t"] = s["arr_abs"].fillna(s["dep_abs"])
    s = s.sort_values(["train_number", "sort_t"]).reset_index(drop=True)
    s["stop_seq"] = s.groupby("train_number").cumcount() + 1
    g = s.groupby("train_number")
    s["prev_lat"], s["prev_lon"] = g["lat"].shift(), g["lon"].shift()
    s["prev_dep"] = g["dep_abs"].shift()
    s["seg_km"] = haversine(s.prev_lat, s.prev_lon, s.lat, s.lon)
    s["seg_min"] = s["arr_abs"] - s["prev_dep"]
    s.loc[s.seg_min <= 0, "seg_min"] = np.nan
    s["seg_speed_kmph"] = s["seg_km"] / (s["seg_min"] / 60)
    s = s.drop(columns=["prev_lat", "prev_lon", "prev_dep", "sort_t"])
    return s


# ------------------------------------------------------------ 6. OUTLIERS
def handle_outliers(s):
    # Halt durations: IQR rule on intermediate stops
    mid = (s.stop_type == "Intermediate") & ~s.timing_point
    q1, q3 = s.loc[mid, "halt_min"].quantile([.25, .75])
    upper = q3 + 1.5 * (q3 - q1)
    s["halt_outlier"] = mid & (s.halt_min > upper)
    log(f"[Outlier] halt IQR upper fence={upper:.1f} min; flagged={s.halt_outlier.sum()}")
    # Capped (winsorised) copy for modelling, raw value kept for audit
    s["halt_min_capped"] = s["halt_min"].clip(upper=max(upper, 60))

    # Segment speed: physically impossible values (> 160 km/h or < 3 km/h) set to NaN
    bad = (s.seg_speed_kmph > 160) | (s.seg_speed_kmph < 3)
    log(f"[Outlier] impossible segment speeds nullified: {bad.sum()}")
    s.loc[bad, "seg_speed_kmph"] = np.nan
    return s


# ------------------------------------------------------------ 7. AGGREGATION + TRANSFORMATION
def station_features(s):
    mid = s[(s.stop_type == "Intermediate") & ~s.timing_point]
    agg = s.groupby("station_code").agg(
        station_name=("station_name", "first"), state=("state", "first"),
        zone=("zone", "first"), lat=("lat", "first"), lon=("lon", "first"),
        trains_served=("train_number", "nunique"),
        peak_hour_trains=("hour", lambda h: h.value_counts().max()),
        night_share=("time_band", lambda b: (b == "Night").mean()),
    )
    halt = mid.groupby("station_code").agg(avg_halt_min=("halt_min_capped", "mean"),
                                           long_halt_share=("halt_outlier", "mean"))
    agg = agg.join(halt).fillna({"avg_halt_min": 0, "long_halt_share": 0})
    agg["peak_ratio"] = agg.peak_hour_trains / agg.trains_served

    # Missing-value imputation for numeric station features: median by zone
    for c in ["avg_halt_min"]:
        agg[c] = agg.groupby("zone")[c].transform(lambda x: x.fillna(x.median()))

    # Skew handling + scaling
    agg["log_trains_served"] = np.log1p(agg.trains_served)
    num = ["log_trains_served", "peak_ratio", "avg_halt_min", "night_share", "long_halt_share"]
    agg[[c + "_z" for c in num]] = StandardScaler().fit_transform(agg[num])
    mm = MinMaxScaler().fit_transform(agg[["log_trains_served", "peak_ratio", "avg_halt_min"]])
    # Composite congestion index (0-100): volume 50%, peaking 25%, dwell 25%
    agg["congestion_index"] = (100 * (0.5 * mm[:, 0] + 0.25 * mm[:, 1] + 0.25 * mm[:, 2])).round(2)
    # One-hot encode zone for downstream models
    agg = pd.concat([agg, pd.get_dummies(agg.zone, prefix="zone", dtype=int)], axis=1)
    return agg.sort_values("congestion_index", ascending=False)


# ------------------------------------------------------------ 8. VISUALS
def plots(raw, s, stf):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    # Missing values before vs after
    before = (raw.replace("None", np.nan)[["arrival", "departure", "station_code"]].isna().mean() * 100)
    after = s[["arrival", "departure", "lat", "seg_speed_kmph"]].isna().mean() * 100
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
    before.plot.bar(ax=ax[0], color="#444"); ax[0].set_title("Missing % - raw schedules")
    after.plot.bar(ax=ax[1], color="#888"); ax[1].set_title("Missing % - after integration")
    for a in ax: a.tick_params(axis="x", rotation=0)
    plt.tight_layout(); plt.savefig(f"{FIG}/missing_values.png", dpi=200); plt.close()

    # Halt distribution before / after capping
    mid = s[(s.stop_type == "Intermediate") & ~s.timing_point]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
    ax[0].boxplot(mid.halt_min.dropna(), orientation="horizontal"); ax[0].set_title("Halt minutes - raw")
    ax[1].boxplot(mid.halt_min_capped.dropna(), orientation="horizontal"); ax[1].set_title("Halt minutes - capped")
    plt.tight_layout(); plt.savefig(f"{FIG}/halt_outliers.png", dpi=200); plt.close()

    # Hourly network load
    fig, ax = plt.subplots(figsize=(10, 3.5))
    s.groupby("hour").size().plot.bar(ax=ax, color="#333")
    ax.set_title("Train stop events by hour of day (network load)"); ax.set_xlabel("Hour")
    ax.tick_params(axis="x", rotation=0)
    plt.tight_layout(); plt.savefig(f"{FIG}/hourly_load.png", dpi=200); plt.close()

    # Top congested stations
    top = stf.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top.station_name + " (" + top.index + ")", top.congestion_index, color="#222")
    ax.set_title("Top 15 stations by congestion index"); ax.set_xlabel("Index (0-100)")
    plt.tight_layout(); plt.savefig(f"{FIG}/top_congested.png", dpi=200); plt.close()

    # Skew transform
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
    ax[0].hist(stf.trains_served, bins=60, color="#444"); ax[0].set_title("Trains/station - raw (skewed)")
    ax[1].hist(stf.log_trains_served, bins=60, color="#444"); ax[1].set_title("log(1+x) transformed")
    plt.tight_layout(); plt.savefig(f"{FIG}/log_transform.png", dpi=200); plt.close()


# ------------------------------------------------------------ MAIN
def main():
    sched_raw, stations_raw, trains_raw = load_raw()
    profile(sched_raw.replace("None", np.nan), "schedules_raw")
    profile(stations_raw, "stations_raw")

    s = clean_schedules(sched_raw.copy())
    st = clean_stations(stations_raw.copy())
    s = engineer(s, st, trains_raw)
    s = handle_outliers(s)
    stf = station_features(s)

    s.to_csv(f"{OUT}/stops_clean.csv", index=False)
    stf.to_csv(f"{OUT}/station_features.csv")
    profile(s, "stops_clean")
    plots(sched_raw, s, stf)

    summary = {
        "raw_stop_rows": len(sched_raw), "clean_stop_rows": len(s),
        "trains": s.train_number.nunique(), "stations": len(stf),
        "median_halt_min": float(s.loc[(s.stop_type == "Intermediate") & ~s.timing_point, "halt_min"].median()),
        "timing_points": int(((s.stop_type == "Intermediate") & s.timing_point).sum()),
        "median_seg_speed_kmph": float(s.seg_speed_kmph.median()),
        "busiest_hour": int(s.groupby("hour").size().idxmax()),
        "top10": stf.head(10)[["station_name", "state", "trains_served", "avg_halt_min",
                                "congestion_index"]].reset_index().to_dict("records"),
        "log": LOG,
    }
    json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=2, default=str)
    log(f"[Done] clean rows={len(s)}, stations={len(stf)}")


if __name__ == "__main__":
    main()
