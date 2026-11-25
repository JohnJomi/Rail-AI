"""Downloads the DataMeet Indian Railways open data into data/raw/.  Run: python src/download_data.py"""
import os, urllib.request
RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
os.makedirs(RAW, exist_ok=True)
BASE = "https://raw.githubusercontent.com/datameet/railways/master/"
for f in ["schedules.json", "stations.json", "trains.json"]:
    print("Downloading", f); urllib.request.urlretrieve(BASE + f, os.path.join(RAW, f))
