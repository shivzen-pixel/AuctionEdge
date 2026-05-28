from pathlib import Path
import os

import duckdb
from dotenv import load_dotenv


EXPECTED_AUCTION_COLUMNS = {
    "year",
    "make",
    "model",
    "trim",
    "body",
    "transmission",
    "vin",
    "state",
    "condition",
    "odometer",
    "color",
    "interior",
    "seller",
    "mmr",
    "sellingprice",
    "saledate",
}


def find_auction_csv(raw_dir: Path) -> Path:
    csv_files = sorted(raw_dir.rglob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")

    # Prefer the known file name if present.
    for file in csv_files:
        if file.name.lower() == "car_prices.csv":
            return file

    # Otherwise use the largest CSV as the likely auction file.
    return max(csv_files, key=lambda p: p.stat().st_size)


def main() -> None:
    load_dotenv()

    raw_auction_dir = Path(os.getenv("RAW_AUCTION_DIR", "data/raw/auction"))
    raw_macro_dir = Path(os.getenv("RAW_MACRO_DIR", "data/raw/macro"))
    duckdb_path = Path(os.getenv("DUCKDB_PATH", "data/warehouse/auctionedge.duckdb"))

    duckdb_path.parent.mkdir(parents=True, exist_ok=True)

    auction_csv = find_auction_csv(raw_auction_dir)
    macro_parquet = raw_macro_dir / "fred_macro.parquet"

    if not macro_parquet.exists():
        raise FileNotFoundError(
            f"{macro_parquet} not found. Run: python -m src.fetch_fred"
        )

    print(f"Using auction CSV: {auction_csv}")
    print(f"Using macro parquet: {macro_parquet}")
    print(f"Writing DuckDB: {duckdb_path}")

    con = duckdb.connect(str(duckdb_path))

    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    # Keep all auction fields as varchar in raw.
    # Type casting and cleaning happen later in dbt.
    con.execute(
        f"""
        CREATE OR REPLACE TABLE raw.raw_auction_prices AS
        SELECT *
        FROM read_csv_auto(
            '{auction_csv.as_posix()}',
            header = true,
            all_varchar = true,
            sample_size = -1,
            ignore_errors = true
        )
        """
    )

    con.execute(
        f"""
        CREATE OR REPLACE TABLE raw.raw_macro_fred AS
        SELECT *
        FROM read_parquet('{macro_parquet.as_posix()}')
        """
    )

    auction_count = con.execute(
        "SELECT COUNT(*) FROM raw.raw_auction_prices"
    ).fetchone()[0]

    macro_count = con.execute(
        "SELECT COUNT(*) FROM raw.raw_macro_fred"
    ).fetchone()[0]

    auction_columns = {
        row[1].lower()
        for row in con.execute("PRAGMA table_info('raw.raw_auction_prices')").fetchall()
    }

    missing_columns = sorted(EXPECTED_AUCTION_COLUMNS - auction_columns)

    con.execute(
        """
        CREATE OR REPLACE TABLE raw.load_audit AS
        SELECT
            current_timestamp AS loaded_at,
            ? AS auction_csv_path,
            ? AS auction_row_count,
            ? AS macro_row_count
        """,
        [auction_csv.as_posix(), auction_count, macro_count],
    )

    print("\nRaw load summary:")
    print(f"- auction rows: {auction_count:,}")
    print(f"- macro rows: {macro_count:,}")
    print(f"- missing expected auction columns: {missing_columns}")

    if auction_count < 500_000:
        raise ValueError(
            "Auction row count is unexpectedly low. Expected roughly 550K rows."
        )

    if missing_columns:
        raise ValueError(
            f"Missing expected auction columns: {missing_columns}"
        )

    print("\nDuckDB raw load complete.")


if __name__ == "__main__":
    main()