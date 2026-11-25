"""Draws the layered, black-and-white architecture diagram on one A4 portrait page.
Output: outputs/figures/architecture.png (300 dpi, 8.27 x 11.69 in).
Run: python src/architecture.py   (needs matplotlib only)"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "outputs", "figures")
os.makedirs(FIG, exist_ok=True)

# Coordinate system: 100 units wide, 141.4 high, so 1 unit is the same size in x and y on A4.
fig = plt.figure(figsize=(8.27, 11.69))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 141.4)
ax.axis("off")


def rect(x, y, w, h, lw=0.8, facecolor="white", z=3):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=facecolor, edgecolor="black",
                           linewidth=lw, zorder=z))


def box(x, y, w, h, title, sub="", double=False, thick=False):
    rect(x, y, w, h, lw=1.8 if thick else 0.8)
    if double:
        rect(x + 0.9, y + 0.9, w - 1.8, h - 1.8, lw=0.6)
    cy = y + h / 2
    if sub:
        ax.text(x + w / 2, cy + h * 0.17, title, ha="center", va="center",
                fontsize=6.2, weight="bold", zorder=5)
        ax.text(x + w / 2, cy - h * 0.2, sub, ha="center", va="center",
                fontsize=4.6, zorder=5, linespacing=1.25)
    else:
        ax.text(x + w / 2, cy, title, ha="center", va="center",
                fontsize=6.2, weight="bold", zorder=5)


def arrow(p, q, both=False, dashed=False, lw=0.7):
    style = "<|-|>" if both else "-|>"
    ax.annotate("", xy=q, xytext=p, zorder=4,
                arrowprops=dict(arrowstyle=style, lw=lw, color="black",
                                linestyle="--" if dashed else "-",
                                shrinkA=0, shrinkB=0, mutation_scale=6))


def poly(pts, dashed=False, lw=0.7):
    """Polyline whose last segment carries an arrowhead."""
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color="black", lw=lw,
                ls="--" if dashed else "-", zorder=4)
    arrow(pts[-2], pts[-1], dashed=dashed, lw=lw)


def note(x, y, text, ha="left", size=4.6, rotation=0):
    ax.text(x, y, text, ha=ha, va="center", fontsize=size, style="italic",
            rotation=rotation, zorder=5)


def band(y0, y1, label, desc=""):
    rect(2, y0, 95, y1 - y0, lw=0.8, z=1)
    rect(2, y0, 5.5, y1 - y0, lw=0.8, facecolor="black", z=2)
    ax.text(4.75, (y0 + y1) / 2, label, rotation=90, ha="center", va="center",
            color="white", fontsize=6.2, weight="bold", zorder=5)
    if desc:
        note(96.2, y1 - 2.3, desc, ha="right")


# ---------------------------------------------------------------- title
ax.text(2, 137.8, "Fig. 1  System architecture: Indian Railways congestion analytics",
        fontsize=8.5, weight="bold", va="center")
ax.plot([2, 97], [135.5, 135.5], color="black", lw=0.9)

# ---------------------------------------------------------------- 1. PRESENTATION
band(112, 131, "PRESENTATION", "Report and static dashboards")
box(9, 116, 19.5, 10, "Planner report", "Word report: problem to results")
box(32, 116, 19.5, 10, "Station ranking", "Congestion index, top-15 table")
box(55, 116, 19.5, 10, "Hourly load view", "Stop events by hour of day")
box(77.5, 116, 18.5, 10, "Figures & summary", "Charts, profiles, summary.json", double=True)
arrow((18, 116), (18, 107), both=True)
note(19.5, 111.5, "reads outputs")
arrow((86, 116), (86, 105.5))

# ---------------------------------------------------------------- 2. APPLICATION
band(90, 109, "APPLICATION", "Python command-line services")
box(9, 101, 65, 6, "Pipeline entry point", "src/download_data.py  ·  src/preprocess.py")
box(9, 93, 65, 6, "Preprocessing orchestrator", "ordered stages, row counts logged per step")
box(76.5, 93, 19.5, 12.5, "Validation & audit", "flags, dropped rows, speed bounds", double=True)
arrow((40, 101), (40, 99))
arrow((74, 104), (76.5, 104))

# ---------------------------------------------------------------- 3. PREPROCESSING PIPELINE
band(50, 88, "PREPROCESSING PIPELINE", "pandas, NumPy, scikit-learn; CPU only")
xs = [9, 23.8, 38.6, 53.4, 68.2, 83]
titles = ["1 Ingestion", "2 Cleaning", "3 Integration", "4 Features", "5 Outliers", "6 Scaling"]
subs = ["JSON to DataFrames", "None to NaN, dedupe", "stops-stations-trains",
        "halt, km, speed, hour", "IQR flags, capping", "log1p, z-score, 1-hot"]
for x, t, s in zip(xs, titles, subs):
    box(x, 72, 12.8, 10, t, s)
for a, b in zip(xs[:-1], xs[1:]):
    arrow((a + 12.8, 77), (b, 77))
poly([(15.4, 93), (15.4, 82)])
note(17, 86.3, "runs stages")
box(23.8, 57, 12.8, 8, "Tools", "sklearn KNN imputer")
box(68.2, 57, 12.8, 8, "Tools", "IQR rule, physical bounds")
arrow((30.2, 72), (30.2, 65))
arrow((74.6, 72), (74.6, 65))
note(38.6, 53.5, "Stage = fixed transform; Tools = library calls it uses")

# ---------------------------------------------------------------- 4. EXTERNAL
band(38, 48, "EXTERNAL")
box(16, 40, 30, 6, "DataMeet railways repo", "GitHub: schedules, stations, trains JSON")
box(66, 40, 26, 6, "Reference literature", "9 papers: Sen (2003) to RSTGCN (2025)")
arrow((20, 46), (20, 72))

# ---------------------------------------------------------------- 5. STORAGE
band(22, 36, "STORAGE")
note(92.5, 33.7, "Files on disk (CSV, JSON, PNG)", ha="right")
box(9, 25, 18, 8, "Raw JSON", "data/raw, 95 MB")
box(30, 25, 20, 8, "Profiling tables", "profile_*.csv")
box(53, 25, 20, 8, "stops_clean.csv", "394,129 stop rows")
box(76, 25, 20, 8, "Run summary", "summary.json, figures")
poly([(10, 72), (10, 33)])
arrow((60, 72), (60, 33))
arrow((94, 72), (94, 33))
poly([(96, 100), (98.5, 100), (98.5, 29), (96, 29)])
note(99.3, 60, "audit trail", ha="center", size=4.5, rotation=90)

# ---------------------------------------------------------------- 6. GOVERNANCE
band(3, 18, "GOVERNANCE", "Git, reproducibility, data-quality checks")
box(9, 6, 15, 9, "Version control", "GitHub repository, commits")
box(27, 6, 15, 9, "Reproducible runs", "requirements.txt, README")
box(45, 6, 15, 9, "Quality monitoring", "rows dropped, flags, speeds")
box(63, 6, 15, 9, "Licensing & privacy", "open public data only")
box(81, 6, 15, 9, "Serving", "none: batch run only")
poly([(63, 25), (63, 21), (52.5, 21), (52.5, 15)], dashed=True)
note(64.5, 20.2, "quality flags")

out = os.path.join(FIG, "architecture.png")
fig.savefig(out, dpi=300, facecolor="white")
print("Saved", out)
