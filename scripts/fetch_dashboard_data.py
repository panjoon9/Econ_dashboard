# scripts/fetch_dashboard_data.py
import requests
import pandas as pd
import json
import os

FRED_API_KEY = os.environ["FRED_API_KEY"]  # GitHub Secrets에서 안전하게 불러옴

SERIES = {
    "cpi": "CPIAUCSL",
    "fedfunds": "DFEDTARL",
    "unrate": "UNRATE",
}

def fetch_series(series_id: str) -> list:
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json"}
    data = requests.get(url, params=params).json()["observations"]
    return [{"date": d["date"], "value": d["value"]} for d in data if d["value"] != "."]

result = {name: fetch_series(code) for name, code in SERIES.items()}

os.makedirs("data", exist_ok=True)
with open("data/dashboard_data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("데이터 저장 완료")
