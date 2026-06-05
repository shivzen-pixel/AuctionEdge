from pathlib import Path

import duckdb
import joblib
import pandas as pd


DUCKDB_PATH = "data/warehouse/auctionedge.duckdb"
MODEL_PATH = Path("models/xgboost_profit_model.joblib")

TARGET_GPU = 2500
SAFETY_BUFFER = 500

print("Loading model...")
model = joblib.load(MODEL_PATH)

print("Loading lifecycle data...")
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
    sellingprice,
    gross_profit
FROM analytics.fact_lifecycle
WHERE
    year IS NOT NULL
    AND make IS NOT NULL
    AND model IS NOT NULL
    AND state IS NOT NULL
    AND condition IS NOT NULL
    AND odometer IS NOT NULL
    AND mmr IS NOT NULL
    AND sellingprice IS NOT NULL
    AND gross_profit IS NOT NULL
""").df()

features = [
    "year",
    "make",
    "model",
    "state",
    "condition",
    "odometer",
    "mmr",
    "sellingprice",
]

print("Scoring vehicles...")
df["predicted_gpu"] = model.predict(df[features])

df["recommended_max_bid"] = (
    df["sellingprice"]
    + df["predicted_gpu"]
    - TARGET_GPU
    - SAFETY_BUFFER
)

df["bid_delta_vs_actual"] = df["recommended_max_bid"] - df["sellingprice"]

df["opportunity_flag"] = df["predicted_gpu"].apply(
    lambda x: "Target" if x >= TARGET_GPU else "Avoid"
)

df["opportunity_score"] = (
    df["predicted_gpu"] / TARGET_GPU
).clip(0, 3)

output_cols = [
    "vin",
    "year",
    "make",
    "model",
    "state",
    "condition",
    "odometer",
    "mmr",
    "sellingprice",
    "gross_profit",
    "predicted_gpu",
    "recommended_max_bid",
    "bid_delta_vs_actual",
    "opportunity_flag",
    "opportunity_score",
]

recommendations = df[output_cols]

print("Writing recommendations to DuckDB...")

conn.execute("CREATE SCHEMA IF NOT EXISTS analytics")
conn.register("recommendations_df", recommendations)

conn.execute("""
CREATE OR REPLACE TABLE analytics.model_bid_recommendations AS
SELECT *
FROM recommendations_df
""")

print("Recommendation summary:")
print(
    conn.sql("""
    SELECT
        COUNT(*) AS rows,
        ROUND(AVG(predicted_gpu), 2) AS avg_predicted_gpu,
        ROUND(AVG(recommended_max_bid), 2) AS avg_recommended_max_bid,
        ROUND(AVG(bid_delta_vs_actual), 2) AS avg_bid_delta_vs_actual,
        SUM(CASE WHEN opportunity_flag = 'Target' THEN 1 ELSE 0 END) AS target_count
    FROM analytics.model_bid_recommendations
    """).df()
)

conn.close()

print("\nCreated analytics.model_bid_recommendations")
