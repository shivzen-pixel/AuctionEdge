from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import os

import duckdb
from dotenv import load_dotenv


PACKAGES = [
    "pandas",
    "numpy",
    "duckdb",
    "dbt-core",
    "dbt-duckdb",
    "scikit-learn",
    "xgboost",
    "statsmodels",
    "shap",
    "scipy",
]


REQUIRED_AUCTION_COLUMNS = [
    "year",
    "make",
    "model",
    "state",
    "condition",
    "odometer",
    "mmr",
    "sellingprice",
    "saledate",
]


def print_package_versions() -> None:
    print("Package versions:")
    for package in PACKAGES:
        try:
            print(f"- {package}: {version(package)}")
        except PackageNotFoundError:
            raise RuntimeError(f"Missing package: {package}")


def main() -> None:
    load_dotenv()

    print_package_versions()

    duckdb_path = Path(os.getenv("DUCKDB_PATH", "data/warehouse/auctionedge.duckdb"))

    if not duckdb_path.exists():
        raise FileNotFoundError(f"DuckDB file not found: {duckdb_path}")

    con = duckdb.connect(str(duckdb_path), read_only=True)

    auction_count = con.execute(
        "SELECT COUNT(*) FROM raw.raw_auction_prices"
    ).fetchone()[0]

    macro_count = con.execute(
        "SELECT COUNT(*) FROM raw.raw_macro_fred"
    ).fetchone()[0]

    auction_columns = [
        row[1].lower()
        for row in con.execute("PRAGMA table_info('raw.raw_auction_prices')").fetchall()
    ]

    missing = sorted(set(REQUIRED_AUCTION_COLUMNS) - set(auction_columns))

    print("\nDuckDB checks:")
    print(f"- DuckDB path: {duckdb_path}")
    print(f"- raw.raw_auction_prices rows: {auction_count:,}")
    print(f"- raw.raw_macro_fred rows: {macro_count:,}")
    print(f"- missing required auction columns: {missing}")

    if auction_count < 500_000:
        raise AssertionError("Auction table has fewer than 500K rows.")

    if macro_count == 0:
        raise AssertionError("Macro table is empty.")

    if missing:
        raise AssertionError(f"Missing required columns: {missing}")

    sample = con.execute(
        """
        SELECT year, make, model, state, condition, odometer, mmr, sellingprice, saledate
        FROM raw.raw_auction_prices
        LIMIT 5
        """
    ).fetchdf()

    print("\nSample raw auction rows:")
    print(sample)

    print("\nPhase 0 verification passed.")


if __name__ == "__main__":
    main()