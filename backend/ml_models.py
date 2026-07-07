import numpy as np
import joblib, os
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest

MODEL_PATH  = "backend/models/power_model.pkl"
ANOMALY_PATH = "backend/models/anomaly_model.pkl"
os.makedirs("backend/models", exist_ok=True)

# ── Train / load regression model ────────────────────────────────────────────
def _train_regression():
    rng = np.random.default_rng(42)
    X = rng.uniform(0, 8000, (500, 1))
    y = X.flatten() * 1.02 + rng.normal(0, 50, 500)
    m = LinearRegression().fit(X, y)
    joblib.dump(m, MODEL_PATH)
    return m

def load_regression():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return _train_regression()

# ── Train / load anomaly model ────────────────────────────────────────────────
def _train_anomaly():
    rng = np.random.default_rng(42)
    X = rng.uniform(500, 6000, (300, 1))
    m = IsolationForest(contamination=0.05, random_state=42).fit(X)
    joblib.dump(m, ANOMALY_PATH)
    return m

def load_anomaly():
    if os.path.exists(ANOMALY_PATH):
        return joblib.load(ANOMALY_PATH)
    return _train_anomaly()

# ── Predict ───────────────────────────────────────────────────────────────────
def predict_power(current_w: float) -> float:
    m = load_regression()
    return round(float(m.predict([[current_w]])[0]), 2)

def detect_anomaly(current_w: float) -> bool:
    m = load_anomaly()
    result = m.predict([[current_w]])
    return bool(result[0] == -1)

def retrain(readings: list[float]):
    X = np.array(readings).reshape(-1, 1)
    y = np.array(readings) * 1.02
    m = LinearRegression().fit(X, y)
    joblib.dump(m, MODEL_PATH)
    am = IsolationForest(contamination=0.05, random_state=42).fit(X)
    joblib.dump(am, ANOMALY_PATH)
    return {"status": "retrained", "samples": len(readings)}
