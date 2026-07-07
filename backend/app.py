from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os
from utils.preprocess import preprocess

app = Flask(__name__)
CORS(app)

# Load model and scaler
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.pkl")


def _load_or_fallback_model():
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            return model, scaler
        except Exception as exc:
            print(f"Warning: failed to load model artifacts: {exc}")

    class FallbackModel:
        def predict(self, X):
            values = X[0]
            if len(values) == 0:
                return [0]
            score = sum(float(v) for v in values)
            if score < 6000:
                return [0]
            if score < 10000:
                return [1]
            return [2]

    class FallbackScaler:
        def transform(self, X):
            return X

    return FallbackModel(), FallbackScaler()


model, scaler = _load_or_fallback_model()

LABELS = ["Low Energy", "Medium Energy", "High Energy"]


@app.route("/")
def home():
    return """
    <h2>Energy Efficiency API is Running!</h2>
    <p>Use <b>POST /predict</b> to make predictions.</p>
    """


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    features = preprocess(data)
    features_scaled = scaler.transform([features])

    prediction = int(model.predict(features_scaled)[0])
    label = LABELS[prediction] if 0 <= prediction < len(LABELS) else "Unknown"

    return jsonify({
        "class": label,
        "class_index": prediction
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)