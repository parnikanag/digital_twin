"""
model_training.py
─────────────────
Trains ML models from LIVE sensor data stored in the SQLite database.
No external datasets (ENB2012 or otherwise) are used.

Run this script after the system has collected at least ~50 readings:

    python notebooks/model_training.py

Saved artefacts
───────────────
    backend/models/model.pkl       RandomForest classifier (Low/Medium/High energy)
    backend/models/scaler.pkl      StandardScaler fitted on live data

The backend's /retrain endpoint does the same thing in-process; this
script is provided for offline / scheduled retraining.
"""

import os
import sys
import sqlite3
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH    = os.path.join(ROOT_DIR, "backend", "smarthome.db")
MODEL_DIR  = os.path.join(ROOT_DIR, "backend", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
SCALER_PATH= os.path.join(MODEL_DIR, "scaler.pkl")

os.makedirs(MODEL_DIR, exist_ok=True)

# ── Load data from SQLite ─────────────────────────────────────────────────────
print(f"Loading sensor readings from: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("ERROR: Database not found. Start the backend and let it collect readings first.")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
df   = pd.read_sql_query(
    """
    SELECT
        power_w,
        temp_c,
        is_on,
        COALESCE(humidity,   65.0) AS humidity,
        COALESCE(smoke_ppm,   0.0) AS smoke_ppm,
        COALESCE(smoke_alert, 0)   AS smoke_alert,
        COALESCE(motion,      0)   AS motion,
        strftime('%H', timestamp)  AS hour
    FROM sensor_readings
    WHERE power_w IS NOT NULL
      AND temp_c  IS NOT NULL
    ORDER BY id DESC
    LIMIT 5000
    """,
    conn,
    parse_dates=["timestamp"] if False else None,
)
conn.close()

print(f"Loaded {len(df)} rows from database.")

if len(df) < 20:
    print("ERROR: Need at least 20 readings to train. Keep the system running and retry.")
    sys.exit(1)

# ── Feature engineering ───────────────────────────────────────────────────────
df["hour"] = df["hour"].astype(float)

# Features: power, temp, humidity, smoke, motion, hour, is_on
FEATURES = ["power_w", "temp_c", "humidity", "smoke_ppm", "smoke_alert", "motion", "hour", "is_on"]
X = df[FEATURES].astype(float)

# Label: bin power_w into 3 classes — Low / Medium / High
#   Low    < 500 W
#   Medium  500–2000 W
#   High   > 2000 W
def power_label(w):
    if w < 500:   return 0   # Low
    if w < 2000:  return 1   # Medium
    return 2                 # High

y = df["power_w"].apply(power_label)

label_names = ["Low Energy", "Medium Energy", "High Energy"]
print(f"\nClass distribution:\n{y.value_counts().rename({0:'Low',1:'Medium',2:'High'}).to_string()}")

# Drop classes with fewer than 2 samples (can't split)
valid_classes = y.value_counts()[y.value_counts() >= 2].index.tolist()
mask = y.isin(valid_classes)
X, y = X[mask], y[mask]

if len(X) < 10:
    print("ERROR: Not enough samples after filtering. Collect more data and retry.")
    sys.exit(1)

# ── Train / test split ────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y if y.nunique() > 1 else None
)

# ── Scale ─────────────────────────────────────────────────────────────────────
scaler      = StandardScaler()
X_train_sc  = scaler.fit_transform(X_train)
X_test_sc   = scaler.transform(X_test)

# ── Train RandomForest ────────────────────────────────────────────────────────
model = RandomForestClassifier(
    n_estimators = 100,
    max_depth    = 8,
    random_state = 42,
    class_weight = "balanced",   # handles uneven class distribution from live data
)
model.fit(X_train_sc, y_train)

# ── Evaluate ──────────────────────────────────────────────────────────────────
acc = model.score(X_test_sc, y_test)
print(f"\nTest accuracy : {acc:.4f}")
print("\nClassification report:")
present_labels = sorted(y_test.unique())
present_names  = [label_names[i] for i in present_labels]
print(classification_report(y_test, model.predict(X_test_sc),
                             labels=present_labels, target_names=present_names))

# ── Feature importance ────────────────────────────────────────────────────────
importance_df = pd.DataFrame({
    "feature":   FEATURES,
    "importance": model.feature_importances_,
}).sort_values("importance", ascending=False)
print("Feature importances:")
print(importance_df.to_string(index=False))

# ── Save ──────────────────────────────────────────────────────────────────────
joblib.dump(model,  MODEL_PATH)
joblib.dump(scaler, SCALER_PATH)
print(f"\nSaved model  → {MODEL_PATH}")
print(f"Saved scaler → {SCALER_PATH}")
print("Done. Restart the backend to pick up the new models.")
