from pathlib import Path

import duckdb
import joblib
import pandas as pd

from xgboost import XGBRegressor

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DUCKDB_PATH = "data/warehouse/auctionedge.duckdb"
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

print("Loading full lifecycle dataset...")

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
""").df()

conn.close()

print(f"Rows loaded: {len(df):,}")

X = df.drop(columns=["gross_profit"])
y = df["gross_profit"]

categorical_features = ["make", "model", "state"]
numeric_features = ["year", "condition", "odometer", "mmr", "sellingprice"]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "num",
            SimpleImputer(strategy="median"),
            numeric_features,
        ),
        (
            "cat",
            Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    (
                        "encoder",
                        OneHotEncoder(
                            handle_unknown="ignore",
                            sparse_output=True,
                        ),
                    ),
                ]
            ),
            categorical_features,
        ),
    ]
)

model = XGBRegressor(
    n_estimators=800,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.85,
    colsample_bytree=0.85,
    objective="reg:squarederror",
    random_state=42,
    n_jobs=-1,
    tree_method="hist",
    eval_metric="rmse",
)

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model),
    ]
)

print("Creating train/test split...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
)

print(f"Training rows: {len(X_train):,}")
print(f"Testing rows: {len(X_test):,}")

print("Training XGBoost model...")

pipeline.fit(X_train, y_train)

print("Generating predictions...")

preds = pipeline.predict(X_test)

mae = mean_absolute_error(y_test, preds)
rmse = mean_squared_error(y_test, preds) ** 0.5
r2 = r2_score(y_test, preds)

print("\nXGBoost Profit Model Results")
print("-----------------------------")
print(f"MAE:  {mae:,.2f}")
print(f"RMSE: {rmse:,.2f}")
print(f"R2:   {r2:.4f}")

results = pd.DataFrame(
    {
        "metric": ["MAE", "RMSE", "R2"],
        "value": [mae, rmse, r2],
    }
)

results.to_csv(MODEL_DIR / "xgboost_profit_model_metrics.csv", index=False)

joblib.dump(pipeline, MODEL_DIR / "xgboost_profit_model.joblib")

print("\nSaved artifacts:")
print("- models/xgboost_profit_model.joblib")
print("- models/xgboost_profit_model_metrics.csv")
