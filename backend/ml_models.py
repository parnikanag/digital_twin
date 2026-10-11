import numpy as np
import joblib, os
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier

os.makedirs("backend/models", exist_ok=True)

MODEL_PATH   = "backend/models/power_model.pkl"
ANOMALY_PATH = "backend/models/anomaly_model.pkl"
RF_PATH      = "backend/models/rf_model.pkl"
KMEANS_PATH  = "backend/models/kmeans_model.pkl"
DT_PATH      = "backend/models/dt_model.pkl"

# ── Linear Regression ─────────────────────────────────────────────────────────
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

def predict_power(current_w: float) -> float:
    m = load_regression()
    return round(float(m.predict([[current_w]])[0]), 2)

# ── Isolation Forest (Anomaly Detection) ──────────────────────────────────────
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

def detect_anomaly(current_w: float) -> bool:
    m = load_anomaly()
    return bool(m.predict([[current_w]])[0] == -1)

# ── Random Forest Regression (Better Power Prediction) ───────────────────────
def _train_random_forest():
    """
    Trains on synthetic data with multiple features:
    power_w, temperature, humidity, hour_of_day
    """
    rng = np.random.default_rng(42)
    n = 1000
    power   = rng.uniform(200, 8000, n)
    temp    = rng.uniform(22, 35, n)
    humidity= rng.uniform(40, 90, n)
    hour    = rng.integers(0, 24, n)
    X = np.column_stack([power, temp, humidity, hour])
    # Target: next reading with realistic variation
    y = power * 1.02 + (temp - 28) * 20 + rng.normal(0, 80, n)
    m = RandomForestRegressor(n_estimators=100, random_state=42)
    m.fit(X, y)
    joblib.dump(m, RF_PATH)
    return m

def load_random_forest():
    if os.path.exists(RF_PATH):
        return joblib.load(RF_PATH)
    return _train_random_forest()

def predict_power_rf(current_w: float, temp: float = 28.0,
                     humidity: float = 65.0, hour: int = 12) -> float:
    """
    Random Forest prediction using power + temp + humidity + hour.
    More accurate than linear regression.
    """
    m = load_random_forest()
    X = np.array([[current_w, temp, humidity, hour]])
    return round(float(m.predict(X)[0]), 2)

# ── K-Means Clustering (Usage Pattern Detection) ──────────────────────────────
def _train_kmeans():
    """
    Clusters power readings into 3 groups:
    Low (0-2000W), Normal (2000-5000W), Peak (5000W+)
    """
    rng = np.random.default_rng(42)
    low    = rng.uniform(100,  2000, 200)
    normal = rng.uniform(2000, 5000, 400)
    peak   = rng.uniform(5000, 8000, 200)
    X = np.concatenate([low, normal, peak]).reshape(-1, 1)
    m = KMeans(n_clusters=3, random_state=42, n_init=10)
    m.fit(X)
    joblib.dump(m, KMEANS_PATH)
    return m

def load_kmeans():
    if os.path.exists(KMEANS_PATH):
        return joblib.load(KMEANS_PATH)
    return _train_kmeans()

def cluster_readings(readings: list[float]) -> dict:
    """
    Classifies a list of power readings into usage clusters.
    Returns counts and labels for Low / Normal / Peak.
    """
    if not readings:
        return {"error": "No readings provided"}

    m      = load_kmeans()
    X      = np.array(readings).reshape(-1, 1)
    labels = m.predict(X)

    # Map cluster IDs to human labels based on centroid values
    centers       = m.cluster_centers_.flatten()
    sorted_ids    = np.argsort(centers)
    label_map     = {sorted_ids[0]: "Low", sorted_ids[1]: "Normal", sorted_ids[2]: "Peak"}
    named_labels  = [label_map[l] for l in labels]

    counts = {"Low": 0, "Normal": 0, "Peak": 0}
    for l in named_labels:
        counts[l] += 1

    current_cluster = label_map[int(labels[-1])]

    return {
        "current_cluster":  current_cluster,
        "counts":           counts,
        "total_readings":   len(readings),
        "percentages": {
            k: round(v / len(readings) * 100, 1)
            for k, v in counts.items()
        },
        "advice": _cluster_advice(current_cluster),
    }

def _cluster_advice(cluster: str) -> str:
    return {
        "Low":    "Energy usage is low. Good time to run heavy appliances.",
        "Normal": "Energy usage is normal. System operating efficiently.",
        "Peak":   "Peak energy usage detected. Consider turning off non-essential appliances.",
    }.get(cluster, "")

# ── Decision Tree (Automation Rules) ─────────────────────────────────────────
def _train_decision_tree():
    """
    Trains a decision tree to recommend automation actions based on:
    temperature, motion detected, power usage, hour of day, smoke alert

    Actions (labels):
    0 = No action
    1 = Turn off lights (no motion, daytime)
    2 = Turn on AC (high temp)
    3 = Send alert (high power)
    4 = EMERGENCY - smoke detected
    """
    rng = np.random.default_rng(42)
    n   = 2000

    temp        = rng.uniform(18, 40, n)
    motion      = rng.integers(0, 2, n)
    power       = rng.uniform(100, 9000, n)
    hour        = rng.integers(0, 24, n)
    smoke       = rng.integers(0, 2, n)

    X = np.column_stack([temp, motion, power, hour, smoke])

    # Rule-based labels for training
    y = np.zeros(n, dtype=int)
    y[smoke == 1]                                          = 4  # Emergency
    y[(power > 6000) & (smoke == 0)]                      = 3  # High power alert
    y[(temp > 30)    & (smoke == 0) & (power <= 6000)]    = 2  # Turn on AC
    y[(motion == 0)  & (hour >= 8)  & (hour <= 20)
      & (smoke == 0) & (power <= 6000) & (temp <= 30)]    = 1  # Turn off lights

    m = DecisionTreeClassifier(max_depth=6, random_state=42)
    m.fit(X, y)
    joblib.dump(m, DT_PATH)
    return m

def load_decision_tree():
    if os.path.exists(DT_PATH):
        return joblib.load(DT_PATH)
    return _train_decision_tree()

ACTION_LABELS = {
    0: "No action needed",
    1: "Turn off lights — no motion detected",
    2: "Turn on AC — room temperature is high",
    3: "Reduce load — power usage is too high",
    4: "EMERGENCY — Smoke/gas detected! Evacuate!",
}

ACTION_COLORS = {
    0: "success",
    1: "info",
    2: "warning",
    3: "warning",
    4: "danger",
}

def get_automation_action(temp: float, motion: bool, power: float,
                          hour: int, smoke: bool) -> dict:
    """
    Returns the recommended automation action based on current sensor state.
    Uses Decision Tree classifier.
    """
    m = load_decision_tree()
    X = np.array([[temp, int(motion), power, hour, int(smoke)]])
    action_id = int(m.predict(X)[0])
    proba     = m.predict_proba(X)[0]
    confidence = round(float(max(proba)) * 100, 1)

    return {
        "action_id":   action_id,
        "action":      ACTION_LABELS[action_id],
        "confidence":  confidence,
        "color":       ACTION_COLORS[action_id],
        "inputs": {
            "temperature": temp,
            "motion":      motion,
            "power_w":     power,
            "hour":        hour,
            "smoke_alert": smoke,
        },
    }

# ── Retrain all models ────────────────────────────────────────────────────────
def retrain(readings: list[float]):
    X = np.array(readings).reshape(-1, 1)
    y = np.array(readings) * 1.02

    # Linear regression
    m = LinearRegression().fit(X, y)
    joblib.dump(m, MODEL_PATH)

    # Isolation Forest
    am = IsolationForest(contamination=0.05, random_state=42).fit(X)
    joblib.dump(am, ANOMALY_PATH)

    # K-Means
    if len(readings) >= 3:
        km = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X)
        joblib.dump(km, KMEANS_PATH)

    return {
        "status":  "retrained",
        "samples": len(readings),
        "models":  ["LinearRegression", "IsolationForest", "KMeans"],
    }
