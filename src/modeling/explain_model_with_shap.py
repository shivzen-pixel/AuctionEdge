from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
import shap


DUCKDB_PATH = "data/warehouse/auctionedge.duckdb"
MODEL_PATH = Path("models/xgboost_profit_model.joblib")
OUTPUT_DIR = Path("models")
OUTPUT_DIR.mkdir(exist_ok=True)

print("Loading trained model...")
pipeline = joblib.load(MODEL_PATH)

preprocessor = pipeline.named_steps["preprocessor"]
model = pipeline.named_steps["model"]

print("Loading sample data for SHAP...")

conn = duckdb.connect(DUCKDB_PATH)

df = conn.sql("""
SELECT
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
USING SAMPLE 10000 ROWS
""").df()

conn.close()

print(f"Rows sampled: {len(df):,}")

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

X = df[features]

print("Transforming features...")
X_transformed = preprocessor.transform(X)

print("Getting feature names...")
feature_names = preprocessor.get_feature_names_out()

print("Computing SHAP values...")
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_transformed)

mean_abs_shap = np.abs(shap_values).mean(axis=0)

importance = pd.DataFrame(
    {
        "feature": feature_names,
        "mean_abs_shap": mean_abs_shap,
    }
).sort_values("mean_abs_shap", ascending=False)

importance.to_csv(
    OUTPUT_DIR / "shap_feature_importance.csv",
    index=False,
)

print("\nTop 20 SHAP Features")
print("---------------------")
print(importance.head(20))

print("\nSaved:")
print("- models/shap_feature_importance.csv")
