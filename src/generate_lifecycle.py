from pathlib import Path
import duckdb
import pandas as pd
import numpy as np

DUCKDB_PATH = "data/warehouse/auctionedge.duckdb"

np.random.seed(42)

conn = duckdb.connect(DUCKDB_PATH)

df = conn.sql("""
SELECT
    vin,
    year,
    make,
    model,
    state,
    condition,
    odometer,
    mmr,
    sellingprice
FROM raw.raw_auction_prices
WHERE vin IS NOT NULL
""").df()

# Convert numeric columns
for col in ["condition", "odometer", "mmr", "sellingprice", "year"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(
    subset=["condition", "odometer", "sellingprice"]
)

# Synthetic lifecycle variables

df["reconditioning_cost"] = (
    500
    + (50 - df["condition"]) * 20
    + df["odometer"] * 0.005
    + np.random.normal(0, 200, len(df))
).clip(300, 4000)

df["days_to_sale"] = (
    25
    + (df["odometer"] / 10000)
    - ((df["year"] - 2010) * 0.5)
    + np.random.normal(0, 10, len(df))
).clip(5, 120)

df["financing_attach"] = np.random.binomial(
    1,
    0.60,
    len(df)
)

df["warranty_attach"] = np.random.binomial(
    1,
    0.35,
    len(df)
)

df["finance_income"] = (
    df["financing_attach"]
    * np.random.uniform(300, 1200, len(df))
)

df["warranty_income"] = (
    df["warranty_attach"]
    * np.random.uniform(500, 2000, len(df))
)

df["sale_price"] = (
    df["sellingprice"]
    * np.random.uniform(1.08, 1.18, len(df))
)

df["gross_profit"] = (
    df["sale_price"]
    + df["finance_income"]
    + df["warranty_income"]
    - df["sellingprice"]
    - df["reconditioning_cost"]
)

conn.execute(
    "CREATE SCHEMA IF NOT EXISTS analytics"
)

conn.register("fact_lifecycle_df", df)

conn.execute("""
CREATE OR REPLACE TABLE analytics.fact_lifecycle AS
SELECT *
FROM fact_lifecycle_df
""")

print("fact_lifecycle created")
print(f"Rows: {len(df):,}")

conn.close()
