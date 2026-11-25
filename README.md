# Indian Railways Network Congestion & Schedule Efficiency Analytics

Data analytics assignment: problem statement, objectives, literature survey, architecture and **data preprocessing** on real open data.

**Dataset:** DataMeet Indian Railways open data — https://github.com/datameet/railways (417,080 stop records, 8,990 stations, 5,208 trains).

## Run
```bash
pip install -r requirements.txt
python src/download_data.py     # fetches raw JSON into data/raw/
python src/preprocess.py        # full preprocessing pipeline -> data/processed/, outputs/figures/
python src/architecture.py      # architecture diagram (needs Graphviz)
node docs/build_doc.js          # optional: rebuild the Word report (npm i docx)
```

## Structure
```
src/download_data.py   data acquisition
src/preprocess.py      ingestion, profiling, cleaning, KNN imputation, integration,
                       feature engineering, outliers, scaling, encoding, congestion index
src/architecture.py    black & white architecture diagram
data/processed/        stops_clean.csv, station_features.csv, profile_*.csv, summary.json
outputs/figures/       all figures
docs/                  Word report + builder script
```
