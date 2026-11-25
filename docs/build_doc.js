// Builds docs/Railway_Congestion_Analytics_Assignment.docx  — run: node docs/build_doc.js
const fs = require("fs");
const path = require("path");
const d = require("docx");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, ShadingType, LevelFormat, BorderStyle, PageBreak, Footer, PageNumber,
  TableOfContents } = d;

const ROOT = path.join(__dirname, "..");
const FIG = (f) => fs.readFileSync(path.join(ROOT, "outputs", "figures", f));
const S = JSON.parse(fs.readFileSync(path.join(ROOT, "data", "processed", "summary.json")));

const P = (text, opts = {}) => new Paragraph({ spacing: { after: 120, line: 300 }, alignment: AlignmentType.JUSTIFIED,
  children: (Array.isArray(text) ? text : [text]).map(t => typeof t === "string" ? new TextRun(t) : t), ...opts });
const B = (t) => new TextRun({ text: t, bold: true });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (t) => new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 60 },
  children: (Array.isArray(t) ? t : [t]).map(x => typeof x === "string" ? new TextRun(x) : x) });
const num = (t) => new Paragraph({ numbering: { reference: "n", level: 0 }, spacing: { after: 60 }, children: [new TextRun(t)] });
const img = (f, w, h, cap) => [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 },
    children: [new ImageRun({ type: "png", data: FIG(f), transformation: { width: w, height: h } })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: cap, italics: true, size: 20 })] })];

const TW = 9026; // A4 width minus 1" margins
const border = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(rows, widths) {
  return new Table({ width: { size: TW, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, children: r.map((c, j) => new TableCell({
      borders, width: { size: widths[j], type: WidthType.DXA },
      shading: i === 0 ? { type: ShadingType.CLEAR, fill: "E6E6E6", color: "auto" } : undefined,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({ children: [new TextRun({ text: String(c), bold: i === 0, size: 19 })] })] })) })) });
}
const fmt = (n) => Number(n).toLocaleString("en-IN");

const lit = [
  ["Sen et al. (2003)", "Modelled the Indian Railway Network as a graph of stations; showed small-world properties (few train changes between any two stations).", "Structural only; no timing, dwell or congestion analysis."],
  ["Ghosh et al. (2011)", "Weighted complex-network study of IRN with traffic (number of trains) as edge weights; identified hub stations.", "Uses traffic volume but not time-of-day peaking or halt behaviour."],
  ["Gaurav & Srivastava (2018)", "N-order Markov + regression models to predict late minutes for 135 trains through Mughal Sarai (MGS) using 2 years of running-status data.", "Limited to one hub and its trains; scheduled-timetable features not engineered network-wide."],
  ["Ghofrani et al. (2018)", "Survey of big-data analytics in railways: maintenance, operations and safety; taxonomy of descriptive / predictive / prescriptive analytics.", "General review; highlights data integration and quality as open challenges."],
  ["Goverde (2007)", "Max-plus algebra for timetable stability analysis; quantifies how buffer/dwell times absorb delay propagation.", "Analytical; needs clean, integrated timetable data as input - the gap this work prepares."],
  ["Tiong, Ma & Palmqvist (2023)", "Review of data-driven train delay prediction; notes preprocessing (cleaning, imbalance, feature construction) strongly affects accuracy.", "Mostly European datasets; Indian timetable data is under-represented."],
  ["Chowdhury et al. (2025)", "RSTGCN - spatio-temporal graph convolutional network for station-level delay prediction on Indian Railways; reports ~32 min average arrival delay (Sep 2024).", "Requires station-level features like traffic intensity and connectivity - exactly the features engineered here."],
  ["Johny, Vadivu & Jeevanand (2025)", "CHRIST University study using Decision Trees, XGBoost, Random Forest and LSTM to predict train delay from past running status.", "Train-level; does not address station congestion or schedule structure."],
  ["Troyanskaya et al. (2001)", "Proposed KNN imputation for missing values; shown to be more robust than mean imputation.", "Basis for the 5-NN geographic imputation of station state/zone used here."],
];

const top = S.top10.map((r, i) => [i + 1, r.station_code, r.station_name, r.state, r.trains_served, Number(r.avg_halt_min).toFixed(1), r.congestion_index]);

const steps = [
  ["Step", "Technique", "Applied to", "Result"],
  ["1", "Null normalisation", "Literal 'None' strings in arrival/departure", "27,835 arrival & 27,827 departure NaN made explicit"],
  ["2", "Duplicate removal", "Exact + (train, station, day, time) duplicates", "443 rows removed"],
  ["3", "Invalid record removal", "Stops with neither arrival nor departure", "22,508 rows dropped"],
  ["4", "Text standardisation", "Codes upper-case, names title-case, trimmed", "Consistent join keys"],
  ["5", "Type conversion", "HH:MM:SS to minutes; multi-day offset", "Numeric time features"],
  ["6", "Invalid coordinates / placeholders", "Stations outside India bbox; 'XX-' codes", "15 placeholder codes removed; 278 without coords"],
  ["7", "KNN imputation", "Missing state & zone (5 nearest stations by lat/lon)", "4,427 values filled for each column"],
  ["8", "Data integration", "stops - stations - trains joins", "Only 1,735 (0.4%) stops unmatched"],
  ["9", "Feature engineering", "Halt, stop type, hour, time band, segment km (haversine), speed", "12+ new features"],
  ["10", "Outlier detection", "IQR on halts; physical bounds 3-160 km/h on speed", "17,932 long halts flagged; 4,977 speeds nullified"],
  ["11", "Winsorisation", "Halt capped at 60 min for modelling", "Raw value kept for audit"],
  ["12", "Aggregation", "Stop-level to station-level", `${fmt(S.stations)} station profiles`],
  ["13", "Skew transform & scaling", "log1p, z-score, min-max", "Comparable feature ranges"],
  ["14", "Encoding", "One-hot encoding of railway zone", "Model-ready matrix"],
];

const children = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 200 },
    children: [new TextRun({ text: "DATA ANALYTICS ASSIGNMENT", bold: true, size: 28 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 },
    children: [new TextRun({ text: "Indian Railways Network Congestion & Schedule Efficiency Analytics", bold: true, size: 40 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "Problem Statement · Objectives · Literature Survey · Architecture · Data Preprocessing", size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 80 }, children: [new TextRun("Name: ____________________    Register No.: ____________")] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun("B.Tech Computer Science and Engineering")] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun("CHRIST (Deemed to be University), Bangalore")] }),
  new Paragraph({ children: [new PageBreak()] }),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),

  H1("1. Introduction"),
  P("Indian Railways is one of the largest railway systems in the world, running thousands of trains over more than 7,000 stations every day. A small set of junctions and terminals carry a disproportionate share of this traffic. When many trains are scheduled into the same station within the same hour, or when trains are given long halts at already busy stations, platforms and approach tracks become bottlenecks and a single late train can delay many others."),
  P("The timetable itself already contains the signals of this risk: how many trains each station handles, when they arrive, how long they stop and how fast they travel between stations. This assignment uses the openly published Indian Railways timetable data to build a data-analytics pipeline that turns raw schedule records into clean, model-ready station-level congestion features."),

  H1("2. Problem Statement"),
  P([B("Problem: "), "Indian Railways' timetable data is published in raw, nested JSON form with missing timestamps, placeholder station codes, duplicate stops, inconsistent naming and no derived operational measures. As a result, planners cannot directly answer which stations are structurally congested, at which hours the network is most loaded, and where scheduled halts are unusually long. There is a need for a reliable data-analytics pipeline that ingests, cleans, integrates and transforms the national timetable into a trustworthy dataset from which station congestion can be measured and compared."]),
  P([B("Why it is a real-time problem: "), "Congestion at hub stations is a daily operational issue that drives platform conflicts and delay propagation. Studies of Indian Railways data report average arrival delays of around 32 minutes, with some delays exceeding 12 hours (Chowdhury et al., 2025). Identifying structurally congested stations from the schedule allows planners to re-time trains, re-allocate platforms or prioritise infrastructure upgrades before delays occur."]),

  H1("3. Objectives"),
  num("To acquire a real, open-source national railway timetable dataset and profile its quality (types, missing values, cardinality)."),
  num("To clean the data by handling missing values, duplicates, invalid records, placeholder codes and inconsistent text."),
  num("To transform clock times into numeric features and correctly handle multi-day journeys and midnight roll-over."),
  num("To integrate stop, station and train data into a single analytical dataset."),
  num("To engineer operational features: halt duration, stop type, hour and time band, segment distance and segment speed."),
  num("To detect and treat outliers using statistical (IQR) and physical (speed bound) rules."),
  num("To aggregate, scale and encode station-level features and compute a composite Station Congestion Index (0-100)."),
  num("To design an end-to-end architecture that supports future clustering and delay-prediction models."),

  H1("4. Dataset Description"),
  P([B("Source: "), "DataMeet Indian Railways open data (github.com/datameet/railways), a community-maintained public dataset of Indian Railways timetables. No synthetic data is used."]),
  table([
    ["File", "Format", "Records", "Key fields"],
    ["schedules.json", "JSON list", fmt(S.raw_stop_rows), "train_number, station_code, arrival, departure, day"],
    ["stations.json", "GeoJSON", "8,990", "code, name, state, zone, latitude, longitude"],
    ["trains.json", "GeoJSON", "5,208", "number, type, zone, distance, duration, from/to station"],
  ], [1900, 1300, 1300, 4526]),
  P(""),
  P("Each schedule record represents one train stopping at (or passing through) one station. Origin stations have no arrival time and destination stations have no departure time, so missing values must be interpreted, not blindly removed."),

  H1("5. Literature Survey"),
  P("The survey covers three strands of prior work: (a) the Indian Railway network as a complex network, (b) data-driven delay prediction, and (c) data-quality and preprocessing in railway analytics."),
  table([["Author(s) & Year", "Contribution", "Gap / relevance to this work"], ...lit], [2000, 3900, 3126]),
  H2("5.1 Summary of Research Gap"),
  P("Network studies of Indian Railways focus on structure, and delay studies focus on individual trains or a single hub. Few works build a clean, network-wide, station-level feature set from the public timetable that captures traffic volume, hourly peaking and dwell behaviour together. Recent graph-based delay models (e.g. RSTGCN) need exactly such station features. This assignment fills that gap at the data-preparation stage by producing a reproducible preprocessing pipeline and a Station Congestion Index."),

  new Paragraph({ children: [new PageBreak()] }),
  H1("6. System Architecture"),
  P("Figure 1 shows the layered architecture of the system on a single A4 page. It has six layers: presentation, application, preprocessing pipeline, external sources, storage and governance. The preprocessing pipeline is the focus of this assignment and is implemented in full."),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60 },
    children: [new ImageRun({ type: "png", data: FIG("architecture.png"), transformation: { width: 543, height: 768 } })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "Figure 1. Layered architecture of the railway congestion analytics system", italics: true, size: 20 })] }),
  new Paragraph({ children: [new PageBreak()] }),
  H2("6.1 Layers"),
  table([
    ["Layer", "Role in this project"],
    ["Presentation", "Word report, station congestion ranking, hourly load view, and the figures and data summary."],
    ["Application", "Command-line entry point, an orchestrator that runs the stages in order, and a validation and audit service that records flags and dropped rows."],
    ["Preprocessing pipeline", "Six stages: ingestion, cleaning, integration, feature engineering, outlier treatment, and scaling and encoding. Tools are the library calls a stage uses (KNN imputer, IQR rule)."],
    ["External", "DataMeet open railway data (the only data source) and the reference literature."],
    ["Storage", "Raw JSON, profiling tables, the clean stop-level file and the run summary."],
    ["Governance", "Git version control, reproducible runs, data-quality monitoring and open-data licensing. There is no serving layer: the pipeline runs as a batch job."],
  ], [2600, 6426]),
  H1("7. Data Preprocessing - Implementation"),
  P("The pipeline is implemented in Python (pandas, NumPy, scikit-learn, matplotlib) in src/preprocess.py. Each step below was executed on the full dataset; the numbers are the actual outputs of the run."),
  H2("7.1 Steps and Results"),
  table(steps, [700, 2300, 3200, 2826]),
  H2("7.2 Handling Missing Values"),
  P("Missing arrival and departure times were stored as the text 'None', which pandas does not recognise as missing. These were converted to true nulls first. Missing values were then interpreted by meaning: a missing arrival marks an origin, a missing departure marks a destination, and records missing both were removed. Missing station state and zone were filled with K-Nearest-Neighbour imputation (k = 5) using station coordinates, since nearby stations almost always share a state and railway zone."),
  ...img("missing_values.png", 600, 210, "Figure 2. Missing-value percentages before and after integration"),
  H2("7.3 Feature Engineering"),
  bullet([B("halt_min: "), "departure minus arrival, with +1440 minutes when a halt crosses midnight."]),
  bullet([B("timing_point: "), `zero-halt intermediate rows (${fmt(S.timing_points)}) are pass-through timing points, kept for routing but excluded from halt statistics.`]),
  bullet([B("stop_type: "), "Origin, Intermediate or Destination."]),
  bullet([B("hour / time_band: "), "hour of activity and Night / Morning / Afternoon / Evening / Late-Evening bands."]),
  bullet([B("seg_km & seg_speed_kmph: "), "haversine distance between consecutive stops and the implied scheduled speed."]),
  bullet([B("Station-level: "), "trains served, peak-hour trains, peak ratio, night share, average halt, long-halt share."]),
  H2("7.4 Outlier Detection and Treatment"),
  P(`For halts at commercial intermediate stops, the interquartile-range rule gave an upper fence of 3.5 minutes; 17,932 halts above this were flagged (many are legitimate long halts at junctions for engine or crew changes, so they were flagged rather than deleted). For modelling, halts were capped at 60 minutes. Segment speeds above 160 km/h or below 3 km/h are not physically possible for scheduled Indian trains and usually come from wrong coordinates, so 4,977 such values were set to missing. The median scheduled segment speed after cleaning is ${S.median_seg_speed_kmph.toFixed(1)} km/h.`),
  ...img("halt_outliers.png", 600, 210, "Figure 3. Halt-duration distribution before and after capping"),
  H2("7.5 Transformation, Scaling and Encoding"),
  P("The number of trains per station is highly right-skewed (most stations serve only a few trains while a few hubs serve over 250). A log(1 + x) transform was applied before scaling. Features were then standardised (z-score) for clustering and min-max scaled for the congestion index. Railway zone was one-hot encoded."),
  ...img("log_transform.png", 600, 210, "Figure 4. Effect of log transform on trains-per-station"),
  H2("7.6 Station Congestion Index"),
  P("Congestion Index = 100 × (0.5 × traffic volume + 0.25 × peak-hour ratio + 0.25 × average halt), each component min-max scaled. Volume is weighted highest because it is the main driver of platform occupancy; peaking and dwell capture how tightly that volume is packed in time."),
  table([["#", "Code", "Station", "State", "Trains", "Avg halt (min)", "Index"], ...top], [500, 900, 2700, 1800, 900, 1226, 1000]),
  P(""),
  ...img("top_congested.png", 520, 325, "Figure 5. Top 15 stations by congestion index"),
  ...img("hourly_load.png", 600, 210, `Figure 6. Network load by hour - busiest hour is ${S.busiest_hour}:00`),

  H1("8. Results and Observations"),
  bullet(`Raw stop records: ${fmt(S.raw_stop_rows)}; clean stop records: ${fmt(S.clean_stop_rows)} across ${fmt(S.trains)} trains and ${fmt(S.stations)} stations.`),
  bullet("Major terminals and junctions - Howrah, Ahmedabad, Old Delhi, New Delhi, Chennai Central, Mughal Sarai, Allahabad and Vijayawada - rank highest, matching the hub stations reported in earlier network studies."),
  bullet("Miyagam Karjan Junction ranks first because of a very high average halt value; this is a data-quality signal to verify, showing why flagged values must be reviewed rather than trusted blindly."),
  bullet(`Network activity peaks at ${S.busiest_hour}:00, with a second evening peak, which gives planners candidate windows for re-timing.`),
  bullet("Most intermediate rows are timing points with zero halt; separating them prevents halt statistics from being pulled to zero."),

  H1("9. Conclusion and Future Scope"),
  P("A complete preprocessing pipeline was built on real, open Indian Railways timetable data. It converts nested and inconsistent raw JSON into clean stop-level and station-level datasets, handles missing values by meaning and by KNN imputation, treats outliers with statistical and physical rules, and produces a Station Congestion Index that correctly highlights known national hubs."),
  P("Future work: (1) cluster stations by their scaled profiles (K-Means / DBSCAN); (2) join live running-status data to predict delays from congestion features; (3) build a graph of stations for network models such as GCNs; (4) publish an interactive dashboard for zonal planners."),

  H1("10. Code Base"),
  table([["File", "Purpose"],
    ["src/preprocess.py", "Full pipeline: ingestion, profiling, cleaning, imputation, integration, feature engineering, outliers, scaling, encoding, plots"],
    ["src/architecture.py", "Generates the black-and-white A4 architecture diagram (matplotlib)"],
    ["data/raw/", "Original DataMeet JSON files (unchanged)"],
    ["data/processed/", "stops_clean.csv, station_features.csv, profile_*.csv, summary.json"],
    ["outputs/figures/", "All figures used in this report"],
    ["docs/build_doc.js", "Generates this Word report"]], [2600, 6426]),
  P(""),
  P("Run: pip install -r requirements.txt, then python src/preprocess.py and python src/architecture.py."),

  H1("References"),
  ...[
    "Sen, P., Dasgupta, S., Chatterjee, A., Sreeram, P. A., Mukherjee, G., & Manna, S. S. (2003). Small-world properties of the Indian railway network. Physical Review E, 67(3), 036106.",
    "Ghosh, S., Banerjee, A., Sharma, N., Agarwal, S., & Ganguly, N. (2011). Statistical analysis of the Indian Railway Network: a complex network approach. Acta Physica Polonica B Proceedings Supplement, 4(2).",
    "Gaurav, R., & Srivastava, B. (2018). Estimating train delays in a large rail network using a zero shot Markov model. IEEE International Conference on Intelligent Transportation Systems (ITSC).",
    "Ghofrani, F., He, Q., Goverde, R. M. P., & Liu, X. (2018). Recent applications of big data analytics in railway transportation systems: A survey. Transportation Research Part C, 90, 226-246.",
    "Goverde, R. M. P. (2007). Railway timetable stability analysis using max-plus system theory. Transportation Research Part B, 41(2), 179-201.",
    "Tiong, K. Y., Ma, Z., & Palmqvist, C.-W. (2023). A review of data-driven approaches to predict train delays. Transportation Research Part C, 148, 104027.",
    "Chowdhury, K., Koley, P., Chakraborty, A., & Ghosh, S. (2025). RSTGCN: Railway-centric spatio-temporal graph convolutional network for train delay prediction. arXiv:2510.01262.",
    "Johny, A., Senthil Vadivu, M., & Jeevanand, E. S. (2025). Predictive analytics for train timeliness using long short term memory and machine learning techniques. IEEE conference paper, CHRIST (Deemed to be University).",
    "Troyanskaya, O., et al. (2001). Missing value estimation methods for DNA microarrays. Bioinformatics, 17(6), 520-525.",
    "DataMeet. Indian Railways open data. https://github.com/datameet/railways",
  ].map(r => new Paragraph({ numbering: { reference: "r", level: 0 }, spacing: { after: 80 }, children: [new TextRun({ text: r, size: 20 })] })),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 30, bold: true }, paragraph: { spacing: { before: 360, after: 160 }, keepNext: true, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "000000", space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Arial", size: 25, bold: true }, paragraph: { spacing: { before: 240, after: 120 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "n", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "r", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "[%1]", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 540 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then(b => {
  const out = path.join(__dirname, "Railway_Congestion_Analytics_Assignment.docx");
  fs.writeFileSync(out, b); console.log("Saved", out);
});
