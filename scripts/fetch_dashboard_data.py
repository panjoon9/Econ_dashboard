"""
scripts/fetch_dashboard_data.py
CPI·기준금리(밴드)·실업률을 FRED에서 받아와,
docs/dashboard_example.html이 그대로 읽을 수 있는 구조로 저장한다.
"""
import requests
import pandas as pd
import json
import os

FRED_API_KEY = os.environ["FRED_API_KEY"]


def fetch_fred(series_id: str) -> pd.DataFrame:
    """FRED에서 시계열을 받아 날짜순 정렬된 DataFrame으로 반환"""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json"}
    obs = requests.get(url, params=params).json()["observations"]
    df = pd.DataFrame(obs)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["value"]).sort_values("date").reset_index(drop=True)


def build_dashboard_json():
    cutoff = pd.Timestamp.today() - pd.DateOffset(years=3)

    # 1) 기준금리를 먼저 계산한다 - 이 월별 타임라인이 CPI 차트의 x축 기준이 된다
    rate = fetch_fred("DFEDTARL")
    rate = rate[rate["date"] >= cutoff]
    rate_m = rate.set_index("date").resample("MS").last().reset_index()
    rate_labels = rate_m["date"].dt.strftime("%Y-%m").tolist()
    rate_lower = rate_m["value"].round(2).tolist()
    rate_upper = (rate_m["value"] + 0.25).round(2).tolist()

    # 2) CPI - YoY를 계산한 뒤, rate_labels와 같은 타임라인에 맞춰 정렬한다.
    #    CPI는 YoY 계산 때문에 앞쪽 12개월 값이 없는데, 그 달은 null로 채워
    #    Chart.js가 있는 부분만 선으로 이어 그리도록 한다.
    cpi_raw = fetch_fred("CPIAUCSL")
    cpi_raw["yoy"] = cpi_raw["value"].pct_change(12) * 100
    cpi_raw["ym"] = cpi_raw["date"].dt.strftime("%Y-%m")
    cpi_map = dict(zip(cpi_raw["ym"], cpi_raw["yoy"]))
    cpi_vals = [
        round(cpi_map[ym], 2) if (ym in cpi_map and pd.notna(cpi_map[ym])) else None
        for ym in rate_labels
    ]

    # 3) 실업률 - 자체 타임라인 유지(별도 차트라서 금리·CPI와 맞출 필요 없음)
    unrate = fetch_fred("UNRATE")
    unrate = unrate[unrate["date"] >= cutoff]
    un_labels = unrate["date"].dt.strftime("%Y-%m").tolist()
    un_vals = unrate["value"].round(2).tolist()

    return {
        "cpi_labels": rate_labels,
        "cpi_vals": cpi_vals,
        "rate_labels": rate_labels,
        "rate_lower": rate_lower,
        "rate_upper": rate_upper,
        "un_labels": un_labels,
        "un_vals": un_vals,
    }


if __name__ == "__main__":
    result = build_dashboard_json()

    # GitHub Pages는 docs 폴더 "안"만 공개하므로, 반드시 docs/data 안에 저장한다
    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/dashboard_data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    print(f"저장 완료: CPI {len(result['cpi_labels'])}개월, "
          f"실업률 {len(result['un_labels'])}개월")
