from pathlib import Path
import os

import pandas as pd
import requests
from dotenv import load_dotenv


FRED_SERIES = {
    "used_car_cpi": "CUSR0000SETA02",
    "auto_loan_rate_48mo": "TERMCBAUTO48NS",
    "consumer_sentiment": "UMCSENT",
}


def fetch_fred_series(series_id: str, api_key: str) -> pd.DataFrame:
    url = "https://api.stlouisfed.org/fred/series/observations"

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": "2010-01-01",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    payload = response.json()

    if "observations" not in payload:
        raise ValueError(f"No observations returned for {series_id}: {payload}")

    df = pd.DataFrame(payload["observations"])
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["series_id"] = series_id

    return df[["date", "series_id", "value"]]


def main() -> None:
    load_dotenv()

    api_key = os.getenv("FRED_API_KEY")
    if not api_key or api_key == "replace_with_your_fred_key":
        raise ValueError("Set a valid FRED_API_KEY in your .env file.")

    out_dir = Path(os.getenv("RAW_MACRO_DIR", "data/raw/macro"))
    out_dir.mkdir(parents=True, exist_ok=True)

    frames = []

    for name, series_id in FRED_SERIES.items():
        print(f"Fetching {name}: {series_id}")
        df = fetch_fred_series(series_id, api_key)
        df["series_name"] = name
        frames.append(df)

    macro = pd.concat(frames, ignore_index=True)

    parquet_path = out_dir / "fred_macro.parquet"
    csv_path = out_dir / "fred_macro.csv"

    macro.to_parquet(parquet_path, index=False)
    macro.to_csv(csv_path, index=False)

    print("\nFRED macro data saved:")
    print(f"- {parquet_path}")
    print(f"- {csv_path}")
    print("\nRows by series:")
    print(macro.groupby(["series_name", "series_id"]).size())


if __name__ == "__main__":
    main()