import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
import joblib
import os

os.makedirs("ml", exist_ok=True)

UN_TO_ISO = {
    "156": "CHN", "276": "DEU", "392": "JPN", "410": "KOR",
    "826": "GBR", "764": "THA", "458": "MYS",
}

print("Building feature dataset...")

ct = pd.read_csv("data/comtrade_clean.csv")
lpi = pd.read_csv("data/lpi_clean.csv")
gdelt = pd.read_csv("data/gdelt_clean.csv")

# Build the LABEL from real trade value drops (year-over-year)
ct["reporter_code"] = ct["reporter_code"].astype(str)
ct["iso_code"] = ct["reporter_code"].map(UN_TO_ISO)

ct_sorted = ct.sort_values(["iso_code", "product_code", "year"])
ct_sorted["prev_value"] = ct_sorted.groupby(["iso_code", "product_code"])["value_usd"].shift(1)
ct_sorted["pct_change"] = (ct_sorted["value_usd"] - ct_sorted["prev_value"]) / ct_sorted["prev_value"]
ct_sorted["disruption_risk"] = (ct_sorted["pct_change"] < -0.15).astype(int)
ct_sorted = ct_sorted.dropna(subset=["pct_change"])

print(f"  Rows with valid year-over-year comparison: {len(ct_sorted)}")
print(f"  Years available: {sorted(ct_sorted['year'].unique())}")

# Build FEATURES from GDELT + LPI
gdelt_agg = gdelt.groupby("actor1_country").agg(
    event_count=("event_id", "count"),
    avg_tone=("avg_tone", "mean"),
    avg_goldstein=("goldstein", "mean")
).reset_index()
gdelt_agg.columns = ["code", "event_count", "avg_tone", "avg_goldstein"]

lpi["code"] = lpi["code"].astype(str)

features = ct_sorted.merge(lpi, left_on="iso_code", right_on="code", how="left")
features = features.merge(gdelt_agg, left_on="iso_code", right_on="code",
                          how="left", suffixes=("", "_gdelt"))

features["lpi_score"] = features["lpi_score"].fillna(features["lpi_score"].mean())
features["event_count"] = features["event_count"].fillna(0)
features["avg_tone"] = features["avg_tone"].fillna(0)
features["avg_goldstein"] = features["avg_goldstein"].fillna(0)

feature_cols = ["prev_value", "lpi_score", "event_count", "avg_tone", "avg_goldstein"]
X = features[feature_cols].fillna(0)
y = features["disruption_risk"]
years = features["year"]

print(f"\n  Final dataset: {X.shape[0]} rows, {X.shape[1]} features")
print(f"  Risk distribution: {y.value_counts().to_dict()}")

# ── TIME-BASED SPLIT ──────────────────────────────────
max_year = years.max()
train_mask = years < max_year
test_mask = years == max_year

X_train, X_test = X[train_mask], X[test_mask]
y_train, y_test = y[train_mask], y[test_mask]

print(f"\n  Train years: {sorted(years[train_mask].unique())} -> {len(X_train)} rows")
print(f"  Test year:   {sorted(years[test_mask].unique())} -> {len(X_test)} rows")
print(f"  Train label distribution: {y_train.value_counts().to_dict()}")
print(f"  Test label distribution:  {y_test.value_counts().to_dict()}")

if y_train.nunique() < 2 or y_test.nunique() < 2:
    print("ERROR: Need both classes present in both train and test sets.")
    exit()

# ── Train Random Forest ───────────────────────────────
print("\nTraining Random Forest...")
rf = RandomForestClassifier(n_estimators=200, random_state=42,
                             n_jobs=-1, class_weight="balanced")
rf.fit(X_train, y_train)
rf_preds = rf.predict(X_test)
print(f"  Accuracy: {accuracy_score(y_test, rf_preds):.3f}")
print(f"  F1:       {f1_score(y_test, rf_preds):.3f}")
print(classification_report(y_test, rf_preds))

# ── Train XGBoost ─────────────────────────────────────
print("\nTraining XGBoost...")
scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
xgb = XGBClassifier(n_estimators=200, learning_rate=0.05,
                     random_state=42, eval_metric="logloss",
                     scale_pos_weight=scale_pos_weight,
                     verbosity=0)
xgb.fit(X_train, y_train)
xgb_preds = xgb.predict(X_test)
print(f"  Accuracy: {accuracy_score(y_test, xgb_preds):.3f}")
print(f"  F1:       {f1_score(y_test, xgb_preds):.3f}")
print(classification_report(y_test, xgb_preds))

# ── Train CatBoost ────────────────────────────────────
print("\nTraining CatBoost...")
cat = CatBoostClassifier(
    iterations=200,
    learning_rate=0.05,
    depth=6,
    random_seed=42,
    verbose=0,
    auto_class_weights="Balanced"
)
cat.fit(X_train, y_train)
cat_preds = cat.predict(X_test)
print(f"  Accuracy: {accuracy_score(y_test, cat_preds):.3f}")
print(f"  F1:       {f1_score(y_test, cat_preds):.3f}")
print(classification_report(y_test, cat_preds))

# ── Save all models ───────────────────────────────────
joblib.dump(rf, "ml/model_rf.pkl")
joblib.dump(xgb, "ml/model_xgb.pkl")
joblib.dump(cat, "ml/model_cat.pkl")
X.to_csv("ml/features.csv", index=False)
y.to_csv("ml/labels.csv", index=False)
print("\nAll models saved to ml/ folder")

# ── Summary comparison ────────────────────────────────
print("\n" + "="*50)
print("MODEL COMPARISON SUMMARY")
print("="*50)
print(f"Random Forest: Accuracy={accuracy_score(y_test, rf_preds):.3f}  F1={f1_score(y_test, rf_preds):.3f}")
print(f"XGBoost:       Accuracy={accuracy_score(y_test, xgb_preds):.3f}  F1={f1_score(y_test, xgb_preds):.3f}")
print(f"CatBoost:      Accuracy={accuracy_score(y_test, cat_preds):.3f}  F1={f1_score(y_test, cat_preds):.3f}")
print("="*50)
print("\nBest model: " + max(
    [("Random Forest", f1_score(y_test, rf_preds)),
     ("XGBoost",       f1_score(y_test, xgb_preds)),
     ("CatBoost",      f1_score(y_test, cat_preds))],
    key=lambda x: x[1]
)[0])
