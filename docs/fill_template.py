"""Fills the CSE631P CIA-1 Component-2 Word template with the assignment content.
Usage: python docs/fill_template.py <template.docx> <output.docx>
Keeps the template's cover page and fills only the sections the template lists."""
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "outputs", "figures")
S = json.load(open(os.path.join(ROOT, "data", "processed", "summary.json")))
TNR = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
USABLE_IN = 6.5  # Letter page, 1" margins


def run(text, bold=False, italic=False, size=24):
    rpr = TNR + ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "") + \
        f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    return f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def para(runs, jc="both", after=120, keep=False, before=0, ind=""):
    if not runs.startswith("<w:"):
        runs = run(runs)
    k = "<w:keepNext/>" if keep else ""
    return (f'<w:p><w:pPr>{k}<w:spacing w:before="{before}" w:after="{after}" w:line="360" '
            f'w:lineRule="auto"/>{ind}<w:jc w:val="{jc}"/></w:pPr>{runs}</w:p>')


def heading(text):
    return para(run(text, bold=True, size=28), jc="left", after=120, keep=True, before=240)


def sub(text):
    return para(run(text, bold=True, size=24), jc="left", after=80, keep=True)


def bullet(text, bold_lead=None):
    r = (run(bold_lead, bold=True) if bold_lead else "") + run(text)
    return (f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/>'
            f'<w:numId w:val="1"/></w:numPr><w:spacing w:after="60" w:line="360" w:lineRule="auto"/>'
            f'<w:jc w:val="both"/></w:pPr>{r}</w:p>')


def numbered(n, text):
    return para(run(f"{n}. ") + run(text), ind='<w:ind w:left="360" w:hanging="360"/>', after=60)


def table(rows, widths):
    tw = sum(widths)
    b = '<w:top w:val="single" w:sz="4" w:color="000000"/><w:left w:val="single" w:sz="4" w:color="000000"/>' \
        '<w:bottom w:val="single" w:sz="4" w:color="000000"/><w:right w:val="single" w:sz="4" w:color="000000"/>' \
        '<w:insideH w:val="single" w:sz="4" w:color="000000"/><w:insideV w:val="single" w:sz="4" w:color="000000"/>'
    x = (f'<w:tbl><w:tblPr><w:tblW w:w="{tw}" w:type="dxa"/><w:tblBorders>{b}</w:tblBorders>'
         f'<w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar>'
         f'</w:tblPr><w:tblGrid>' + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>')
    for i, r in enumerate(rows):
        x += '<w:tr>' + ('<w:trPr><w:tblHeader/></w:trPr>' if i == 0 else '')
        for c, w in zip(r, widths):
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="E6E6E6"/>' if i == 0 else ''
            x += (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shade}</w:tcPr>'
                  f'<w:p><w:pPr><w:spacing w:after="0"/></w:pPr>{run(str(c), bold=(i == 0), size=20)}</w:p></w:tc>')
        x += '</w:tr>'
    return x + '</w:tbl>' + para("", after=60)


IMGS = []


def image(fname, width_in, caption):
    w, h = Image.open(os.path.join(FIG, fname)).size
    cx = int(width_in * 914400)
    cy = int(cx * h / w)
    rid = f"rIdFig{len(IMGS) + 1}"
    n = len(IMGS) + 100
    IMGS.append((rid, fname))
    drawing = (
        f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{n}" name="Figure {n}"/>'
        f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="{n}" name="{fname}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData>'
        f'</a:graphic></wp:inline></w:drawing></w:r>')
    return (para(drawing, jc="center", after=60, keep=True) +
            para(run(caption, italic=True, size=20), jc="center", after=200))


PAGE_BREAK = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
fmt = lambda n: f"{int(n):,}"

# ------------------------------------------------------------------ content
body = []
A = body.append

A(heading("Abstract"))
A(para(
    "Indian Railways runs thousands of passenger and freight trains every day across more than 7,000 "
    "stations, and a small number of junctions and terminals carry a large share of that traffic. When "
    "many trains are timetabled into the same station in the same hour, or are given long halts at an "
    "already busy station, platforms and approach tracks become bottlenecks and one late train can delay "
    "many others. The public timetable already contains signals of this risk, but it is published as "
    "raw, nested JSON with missing timestamps stored as text, placeholder station codes, duplicate stop "
    "records, missing state and zone values, inconsistent naming and no derived operational measures. "
    "This work applies data analytics to that problem. Using the open DataMeet Indian Railways dataset "
    f"({fmt(S['raw_stop_rows'])} stop records, 8,990 stations and 5,208 trains), we design a six-layer "
    "architecture and implement a complete data preprocessing pipeline in Python. The pipeline converts "
    "text nulls to true missing values, removes duplicate and empty records, standardises station codes "
    "and names, converts clock times into minutes while handling multi-day journeys and midnight "
    "roll-over, fills missing state and zone values with K-Nearest-Neighbour imputation on station "
    "coordinates, integrates stops with station and train attributes, and engineers features such as "
    "halt duration, stop type, hour of day, segment distance and scheduled speed. Outliers are flagged "
    "with the interquartile-range rule and physically impossible speeds are removed. Station-level "
    "features are log-transformed, scaled and one-hot encoded, and combined into a Station Congestion "
    f"Index from 0 to 100. After preprocessing, {fmt(S['clean_stop_rows'])} clean stop records across "
    f"{fmt(S['stations'])} stations remain. The index ranks Howrah, Ahmedabad, Old Delhi, New Delhi, "
    "Chennai Central and Mughal Sarai among the most congested stations, which agrees with hub stations "
    f"reported in earlier network studies, and shows that network activity peaks at {S['busiest_hour']}:00. "
    "The resulting dataset is ready for clustering and delay-prediction models."))

A(para(run("Keywords: ", bold=True) + run(
    "Indian Railways, data preprocessing, railway congestion, KNN imputation, outlier detection, "
    "feature engineering, timetable analytics, data analytics")))

A(heading("Introduction"))
A(para(
    "Railway congestion is a daily operational problem. A station that handles many trains in a short "
    "window has fewer free platforms, so any disturbance spreads quickly to other trains. Recent work on "
    "Indian Railways data reports an average arrival delay of around 32 minutes in September 2024, with "
    "some delays exceeding 12 hours (Chowdhury et al., 2025). Knowing which stations are structurally "
    "congested lets planners re-time trains, re-allocate platforms or plan infrastructure upgrades "
    "before delays happen."))
A(para(
    "Earlier research has studied the Indian Railway network from two main angles. Network studies model "
    "stations as nodes and show that the network has small-world properties (Sen et al., 2003) and a set "
    "of heavily used hub stations (Ghosh et al., 2011). Delay studies predict how late individual trains "
    "will be, using Markov and regression models at Mughal Sarai (Gaurav and Srivastava, 2018), machine "
    "learning and LSTM models (Johny et al., 2025), and graph neural networks over the whole network "
    "(Chowdhury et al., 2025). Reviews of railway analytics point out that data integration and data "
    "quality are open challenges and that preprocessing strongly affects model accuracy (Ghofrani et al., "
    "2018; Tiong et al., 2023)."))
A(para(
    "Few of these works build a clean, network-wide, station-level dataset from the public timetable that "
    "captures traffic volume, hourly peaking and halt behaviour together. This assignment addresses that "
    "gap at the data preparation stage. It defines the problem and objectives, designs a layered system "
    "architecture, and implements and evaluates the preprocessing techniques needed to turn the raw "
    "timetable into model-ready data."))

A(heading("Problem Statement"))
A(para(
    "Indian Railways timetable data is publicly available, but only in a raw, nested JSON form with "
    "missing timestamps stored as text, placeholder station codes, duplicate stops, missing state and "
    "zone values, inconsistent naming and no derived operational measures. Because of this, planners and "
    "analysts cannot directly answer which stations are structurally congested, at which hours the "
    "network is most heavily loaded, and where scheduled halts are unusually long. A reliable data "
    "analytics pipeline is needed that ingests, cleans, integrates and transforms the national timetable "
    "into a trustworthy dataset from which station congestion can be measured and compared."))

A(heading("Challenges Identified"))
for lead, txt in [
    ("Hidden missing values: ", "arrival and departure times are stored as the text 'None', which analysis tools do not treat as missing."),
    ("Meaningful gaps: ", "a missing arrival marks a train's origin and a missing departure marks its destination, so missing values cannot simply be deleted."),
    ("Duplicate and empty records: ", f"443 duplicate stops and 22,508 stops with no time at all."),
    ("Placeholder and invalid stations: ", "station codes starting with 'XX-' and 278 stations without coordinates."),
    ("Missing attributes: ", "4,427 stations have no state or railway zone."),
    ("Time arithmetic: ", "journeys run over several days and halts can cross midnight, so clock times cannot be subtracted directly."),
    ("Data spread over three files: ", "stops, stations and trains must be joined on codes that are not always consistent."),
    ("Outliers and errors: ", "very long halts, and impossible scheduled speeds caused by wrong coordinates."),
    ("Skewed distributions: ", "most stations serve a few trains while a few hubs serve more than 250."),
    ("Data size: ", f"{fmt(S['raw_stop_rows'])} stop records must be processed efficiently."),
]:
    A(bullet(txt, lead))

A(heading("Objectives"))
for i, o in enumerate([
    "To acquire a real, open-source national railway timetable dataset and profile its quality.",
    "To clean the data by handling missing values, duplicates, invalid records, placeholder codes and inconsistent text.",
    "To transform clock times into numeric features, handling multi-day journeys and midnight roll-over.",
    "To integrate stop, station and train data into a single analytical dataset.",
    "To engineer operational features: halt duration, stop type, hour of day, segment distance and scheduled speed.",
    "To detect and treat outliers using statistical (IQR) and physical (speed bound) rules.",
    "To scale and encode station-level features and compute a Station Congestion Index (0-100).",
    "To design a layered architecture that supports future clustering and delay-prediction models.",
], 1):
    A(numbered(i, o))

A(heading("Implemented Preprocessing Technique"))
A(para(
    "The system is organised into six layers, shown in Figure 1: presentation, application, "
    "preprocessing pipeline, external sources, storage and governance. The preprocessing pipeline is "
    "implemented in Python (pandas, NumPy, scikit-learn and matplotlib) and every step was run on the full "
    "dataset; the numbers below are the actual outputs of that run."))
A(PAGE_BREAK)
A(image("architecture.png", 6.1, "Figure 1. Layered architecture of the railway congestion analytics system"))
A(PAGE_BREAK)
A(sub("Steps and results"))
A(table([
    ["Step", "Technique", "Applied to", "Result"],
    ["1", "Null normalisation", "Text 'None' in arrival / departure", "27,835 arrival and 27,827 departure values made truly missing"],
    ["2", "Duplicate removal", "Exact and (train, station, day, time) duplicates", "443 rows removed"],
    ["3", "Invalid record removal", "Stops with no arrival and no departure", "22,508 rows dropped"],
    ["4", "Text standardisation", "Station codes upper-case, names title-case", "Consistent join keys"],
    ["5", "Type conversion", "HH:MM:SS to minutes, day offset", "Numeric time features"],
    ["6", "Invalid station handling", "Placeholder codes, coordinates outside India", "15 codes removed; 278 without coordinates"],
    ["7", "KNN imputation", "Missing state and zone (5 nearest stations)", "4,427 values filled per column"],
    ["8", "Data integration", "Stops joined to stations and trains", "1,735 stops (0.4%) unmatched"],
    ["9", "Feature engineering", "Halt, stop type, hour, time band, segment km and speed", "12+ new features"],
    ["10", "Outlier detection", "IQR on halts; 3-160 km/h speed bounds", "17,932 long halts flagged; 4,977 speeds removed"],
    ["11", "Capping", "Halt capped at 60 minutes for modelling", "Raw value kept for audit"],
    ["12", "Aggregation", "Stop level to station level", f"{fmt(S['stations'])} station profiles"],
    ["13", "Transformation and scaling", "log(1+x), z-score, min-max", "Comparable feature ranges"],
    ["14", "Encoding", "One-hot encoding of railway zone", "Model-ready matrix"],
], [600, 2200, 3300, 3260]))

A(sub("Handling missing values"))
A(para(
    "Text 'None' values were converted to true missing values first. Missing values were then read by "
    "meaning: a missing arrival marks an origin, a missing departure marks a destination, and records "
    "missing both were removed. Missing station state and zone were filled with K-Nearest-Neighbour "
    "imputation (k = 5) on station latitude and longitude, because nearby stations almost always share a "
    "state and railway zone (Troyanskaya et al., 2001)."))
A(image("missing_values.png", 6.0, "Figure 2. Missing values before and after integration"))

A(sub("Feature engineering"))
A(para(
    "Halt duration is departure minus arrival, adding 1,440 minutes when a halt crosses midnight. "
    f"Intermediate rows with zero halt ({fmt(S['timing_points'])}) are pass-through timing points; they "
    "are kept for routing but excluded from halt statistics. Each stop is labelled as origin, intermediate "
    "or destination and given an hour and a time band. Segment distance between consecutive stops is "
    "computed with the haversine formula, and dividing it by the scheduled running time gives the "
    "scheduled speed."))

A(sub("Outlier detection and treatment"))
A(para(
    "For halts at commercial intermediate stops, the interquartile-range rule gave an upper fence of 3.5 "
    "minutes. The 17,932 halts above it were flagged rather than deleted, because many are genuine long "
    "halts at junctions for engine or crew changes. For modelling, halts were capped at 60 minutes. "
    "Scheduled speeds above 160 km/h or below 3 km/h are not possible for Indian trains and usually come "
    "from wrong coordinates, so 4,977 such values were set to missing. The median scheduled speed after "
    f"cleaning is {S['median_seg_speed_kmph']:.1f} km/h."))
A(image("halt_outliers.png", 6.0, "Figure 3. Halt duration before and after capping"))

A(sub("Transformation, scaling and encoding"))
A(para(
    "Trains per station is strongly right-skewed, so a log(1 + x) transform was applied before scaling. "
    "Features were standardised with z-scores for clustering and min-max scaled for the congestion index, "
    "and railway zone was one-hot encoded. The Station Congestion Index is 100 x (0.5 x traffic volume + "
    "0.25 x peak-hour ratio + 0.25 x average halt), with each part min-max scaled."))
A(image("log_transform.png", 6.0, "Figure 4. Effect of the log transform on trains per station"))

A(sub("Results"))
A(table([["#", "Code", "Station", "State", "Trains", "Avg halt (min)", "Index"]] +
        [[i + 1, r["station_code"], r["station_name"], r["state"], r["trains_served"],
          f"{float(r['avg_halt_min']):.1f}", r["congestion_index"]] for i, r in enumerate(S["top10"])],
        [500, 900, 2900, 1800, 900, 1360, 1000]))
A(para(
    "Major terminals and junctions rank highest, matching hub stations found in earlier network studies. "
    "Miyagam Karjan Junction ranks first only because of a very high average halt value, which is a "
    "data-quality signal to verify. Network activity peaks at "
    f"{S['busiest_hour']}:00, with a second peak in the evening."))
A(image("top_congested.png", 5.0, "Figure 5. Top 15 stations by congestion index"))
A(image("hourly_load.png", 6.0, f"Figure 6. Network load by hour of day"))

A(heading("Data Set Details"))
A(para(run("Source: ", bold=True) + run(
    "DataMeet Indian Railways open data, https://github.com/datameet/railways. This is a public, "
    "community-maintained dataset of Indian Railways timetables. No synthetic data is used.")))
A(table([
    ["File", "Format", "Records", "Key fields"],
    ["schedules.json", "JSON list", fmt(S["raw_stop_rows"]), "train_number, station_code, arrival, departure, day"],
    ["stations.json", "GeoJSON", "8,990", "code, name, state, zone, latitude, longitude"],
    ["trains.json", "GeoJSON", "5,208", "number, type, zone, distance, duration, from / to station"],
], [1900, 1300, 1300, 4860]))
A(para(
    "Each schedule record is one train stopping at, or passing through, one station. After preprocessing, "
    f"the stop-level dataset has {fmt(S['clean_stop_rows'])} rows covering {fmt(S['trains'])} trains, "
    f"and the station-level dataset has {fmt(S['stations'])} stations with 37 features."))


# ------------------------------------------------------------------ assemble
def main(src, dst):
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(src) as z:
        z.extractall(tmp)
    dp = os.path.join(tmp, "word", "document.xml")
    xml = open(dp, encoding="utf-8").read()

    xml = xml.replace("Title of the Research Article ",
                      "Indian Railways Network Congestion and Schedule Efficiency Analytics: "
                      "Data Preprocessing of Open Timetable Data")
    # Replace everything after the cover's page break with the content
    start = xml.index("For Document Preparation")
    start = xml.rindex("<w:p ", 0, start)
    end = xml.index("<w:sectPr")
    xml = xml[:start] + "".join(body) + xml[end:]
    if "xmlns:wp=" not in xml[:3000] or "xmlns:r=" not in xml[:3000]:
        raise SystemExit("template is missing drawing namespaces")
    open(dp, "w", encoding="utf-8").write(xml)

    media = os.path.join(tmp, "word", "media")
    os.makedirs(media, exist_ok=True)
    rels_p = os.path.join(tmp, "word", "_rels", "document.xml.rels")
    rels = open(rels_p, encoding="utf-8").read()
    add = ""
    for rid, f in IMGS:
        shutil.copy(os.path.join(FIG, f), os.path.join(media, f))
        add += (f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/'
                f'2006/relationships/image" Target="media/{f}"/>')
    open(rels_p, "w", encoding="utf-8").write(rels.replace("</Relationships>", add + "</Relationships>"))

    ct_p = os.path.join(tmp, "[Content_Types].xml")
    ct = open(ct_p, encoding="utf-8").read()
    if 'Extension="png"' not in ct:
        ct = ct.replace("<Default ", '<Default Extension="png" ContentType="image/png"/><Default ', 1)
    open(ct_p, "w", encoding="utf-8").write(ct)

    if os.path.exists(dst):
        os.remove(dst)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for d, _, files in os.walk(tmp):
            for f in files:
                full = os.path.join(d, f)
                z.write(full, os.path.relpath(full, tmp))
    shutil.rmtree(tmp)
    print("Saved", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
