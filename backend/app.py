
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import joblib
import os
from utils.preprocess import preprocess

app = Flask(__name__)
CORS(app)

# Load model and scaler relative to this file's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    model = joblib.load(os.path.join(BASE_DIR, "models", "model.pkl"))
    scaler = joblib.load(os.path.join(BASE_DIR, "models", "scaler.pkl"))
except FileNotFoundError as e:
    raise RuntimeError(
        f"Model files not found: {e}. Run notebooks/model_training.py first."
    )

LABELS = ["Low Energy", "Medium Energy", "High Energy"]

@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Energy Efficiency API</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 24px;
    }
    .card {
      background: #1e293b;
      border-radius: 16px;
      padding: 40px;
      max-width: 600px;
      width: 100%;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    .status-dot {
      display: inline-block;
      width: 10px; height: 10px;
      background: #22c55e;
      border-radius: 50%;
      margin-right: 8px;
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50%       { opacity: 0.4; }
    }
    h1 { font-size: 1.6rem; margin-bottom: 6px; color: #f8fafc; }
    .subtitle { color: #94a3b8; margin-bottom: 28px; font-size: 0.95rem; }
    .section-title {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: #64748b;
      margin-bottom: 12px;
    }
    .endpoint {
      background: #0f172a;
      border-radius: 10px;
      padding: 16px 20px;
      margin-bottom: 12px;
    }
    .method {
      display: inline-block;
      padding: 2px 10px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 700;
      margin-right: 10px;
    }
    .get  { background: #166534; color: #86efac; }
    .post { background: #1e3a5f; color: #93c5fd; }
    .path { font-family: monospace; font-size: 0.95rem; color: #e2e8f0; }
    .desc { color: #94a3b8; font-size: 0.85rem; margin-top: 6px; }
    .payload {
      background: #0f172a;
      border-radius: 8px;
      padding: 14px 18px;
      font-family: monospace;
      font-size: 0.82rem;
      color: #7dd3fc;
      margin-top: 20px;
      white-space: pre;
      overflow-x: auto;
    }
    .label { color: #64748b; font-size: 0.8rem; margin-top: 20px; margin-bottom: 6px; }
  </style>
</head>
<body>
  <div class="card">
    <h1><span class="status-dot"></span>Energy Efficiency API</h1>
    <p class="subtitle">ML-powered building energy classification backend</p>

    <p class="section-title">Available Endpoints</p>

    <div class="endpoint">
      <span class="method get">GET</span>
      <span class="path">/</span>
      <p class="desc">API status and documentation</p>
    </div>

    <div class="endpoint">
      <span class="method post">POST</span>
      <span class="path">/predict</span>
      <p class="desc">Predict energy efficiency class from building features</p>
    </div>

    <p class="label">Example request body for /predict</p>
    <div class="payload">{
  "surface_area":   700,
  "wall_area":      300,
  "roof_area":      200,
  "overall_height": 6,
  "glazing_area":   25,
  "orientation":    2
}</div>

    <p class="label">Example response</p>
    <div class="payload">{
  "class":       "Low Energy",
  "class_index": 0
}</div>
  </div>
</body>
</html>
"""

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    features = preprocess(data)
    features_scaled = scaler.transform([features])
    prediction = int(model.predict(features_scaled)[0])
    label = LABELS[prediction] if 0 <= prediction < len(LABELS) else "Unknown"
    return jsonify({"class": label, "class_index": prediction})
