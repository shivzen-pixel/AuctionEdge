import duckdb
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

conn = duckdb.connect("data/warehouse/auctionedge.duckdb")

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
""").df()

df = df.dropna()

X = df.drop(columns=["gross_profit"])
y = df["gross_profit"]

categorical = [
    "make",
    "model",
    "state",
]

numeric = [
    "year",
    "condition",
    "odometer",
    "mmr",
    "sellingprice",
]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "num",
            SimpleImputer(strategy="median"),
            numeric,
        ),
        (
            "cat",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]),
            categorical,
        ),
    ]
)

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    n_jobs=-1,
)

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", model),
])

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
)

pipeline.fit(X_train, y_train)

preds = pipeline.predict(X_test)

print("\nRandom Forest Results")
print("----------------------")
print("MAE:", round(mean_absolute_error(y_test, preds), 2))
print("RMSE:", round(mean_squared_error(y_test, preds) ** 0.5, 2))
print("R2:", round(r2_score(y_test, preds), 4))
