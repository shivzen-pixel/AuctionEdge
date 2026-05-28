from pathlib import Path
import os
import subprocess
import sys

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    dataset = os.getenv("KAGGLE_DATASET", "syedanwarafridi/vehicle-sales-data")
    raw_dir = Path(os.getenv("RAW_AUCTION_DIR", "data/raw/auction"))
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading Kaggle dataset: {dataset}")
    print(f"Destination: {raw_dir}")

    cmd = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        dataset,
        "-p",
        str(raw_dir),
        "--unzip",
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print("\nKaggle download failed.")
        print("Check that:")
        print("1. Your Kaggle credentials are configured.")
        print("2. You accepted the dataset terms on Kaggle.")
        print("3. KAGGLE_DATASET in .env is the correct slug.")
        raise exc

    csv_files = sorted(raw_dir.rglob("*.csv"))

    if not csv_files:
        print("No CSV files found after download.")
        sys.exit(1)

    print("\nCSV files found:")
    for file in csv_files:
        print(f"- {file} ({file.stat().st_size / 1_000_000:.1f} MB)")

    print("\nKaggle download complete.")


if __name__ == "__main__":
    main()