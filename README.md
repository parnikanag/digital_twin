# Smart Building Digital Twin

An AI-driven smart home energy management platform that combines a real-time digital twin, ML-powered anomaly detection, what-if simulation, and SMS alerting into a single full-stack application.

---

## Overview

This project simulates a smart home environment with per-room, per-appliance sensor data. It exposes a FastAPI backend for data ingestion and ML inference, a Flask API for building energy classification, and a Streamlit frontend that renders a live floor plan with appliance controls, energy analytics, and notification management.

Real IoT devices (ESP32, Raspberry Pi, etc.) can push live readings to the backend, which seamlessly switches from simulation to real sensor data.

---

## Features

- **Digital Twin Floor Plan** — Live SVG floor plan showing per-room temperature, power draw, and appliance states
- **Appliance Monitoring & Control** — Toggle appliances ON/OFF in real time with instant power feedback
- **ML Power Prediction** — Linear regression model predicts next-tick power consumption
- **Anomaly Detection** — Isolation Forest flags abnormal power readings
- **What-If Simulation** — Model the impact of adding extra appliances before turning them on
- **Energy Budget Tracker** — Set a monthly kWh budget and track estimated usage
- **SMS Alerts via Twilio** — Automatic notifications for overload, overheat, and appliances left on
- **Building Energy Classification** — Separate Flask API classifies buildings as Low / Medium / High energy based on structural features
- **Real IoT Sensor Support** — `/sensor/push` endpoint accepts live readings from any HTTP-capable device
- **User Authentication** — Sign-up / login with bcrypt-hashed passwords stored in SQLite

---

## Project Structure

```
.
├── backend/
│   ├── main.py                  # FastAPI app — core API endpoints
│   ├── app.py                   # Flask app — building energy classification API
│   ├── auth.py                  # Password hashing and verification
│   ├── database.py              # SQLAlchemy models (User, SensorReading) + SQLite setup
│   ├── simulator.py             # Room/appliance simulation engine
│   ├── ml_models.py             # Power prediction (LinearRegression) + anomaly detection (IsolationForest)
│   ├── notifications.py         # Twilio SMS alert service
│   ├── run.py                   # Entry point for Flask app
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Environment variables (Twilio credentials, thresholds)
│   ├── config/
│   │   └── config.py            # App config (debug mode, port)
│   ├── models/
│   │   ├── model.pkl            # Trained energy classification model
│   │   └── scaler.pkl           # Feature scaler for classification model
│   ├── services/
│   │   ├── prediction_service.py
│   │   └── simulation_service.py
│   └── utils/
│       └── preprocess.py        # Feature preprocessing for classification
├── frontend/
│   └── app.py                   # Streamlit dashboard
├── simulations/
│   └── simulator.py             # Standalone simulation script (hits Flask /predict)
├── notebooks/
│   └── model_training.py        # Model training script (generates model.pkl + scaler.pkl)
├── data/
│   └── raw/
│       └── ENB2012_data.xlsx    # Energy efficiency dataset (UCI)
└── digital-twin/
    └── README.md
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Core API | FastAPI + Uvicorn |
| Classification API | Flask |
| Frontend | Streamlit + Plotly |
| Database | SQLite via SQLAlchemy |
| ML | scikit-learn (LinearRegression, IsolationForest) |
| SMS Alerts | Twilio |
| Auth | bcrypt |
| IoT Integration | HTTP POST (ESP32 / Raspberry Pi compatible) |

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### 1. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment variables

Create or edit `backend/.env`:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1xxxxxxxxxx
OVERHEAT_TEMP=30
OVERLOAD_WATTS=6000
```

SMS alerts are optional. The app runs fully without Twilio credentials — alerts are simply skipped.

### 3. Train the classification model

Run this once to generate `model.pkl` and `scaler.pkl`:

```bash
python notebooks/model_training.py
```

### 4. Start the FastAPI backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Start the Flask classification API (optional)

```bash
cd backend
python run.py
```

Runs on `http://127.0.0.1:5000` by default.

### 6. Start the Streamlit frontend

```bash
cd frontend
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## API Reference

### FastAPI (port 8000)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/signup` | Create a new user account |
| `POST` | `/login` | Authenticate and log in |
| `GET` | `/generate` | Generate a simulated sensor snapshot and persist to DB |
| `GET` | `/generate/live` | Return real sensor data if available, else simulate |
| `GET` | `/data` | Fetch recent sensor readings (default: last 50) |
| `POST` | `/predict` | Predict next power value + anomaly flag |
| `GET` | `/anomaly` | Run anomaly detection on last 100 readings |
| `POST` | `/retrain` | Retrain ML models on latest DB data |
| `POST` | `/simulate` | What-if simulation for extra appliance load |
| `POST` | `/toggle` | Toggle an appliance ON or OFF |
| `POST` | `/sensor/push` | Accept live readings from IoT devices |
| `GET` | `/sensor/mode` | Check if system is using real or simulated data |
| `POST` | `/sensor/reset` | Reset to simulation mode |
| `POST` | `/notify/check` | Run alert checks and send SMS if conditions met |
| `POST` | `/notify/test` | Send a test SMS to verify Twilio setup |
| `GET` | `/notify/status` | Check Twilio configuration status |

### Flask Classification API (port 5000)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API status page with endpoint documentation |
| `POST` | `/predict` | Classify building energy efficiency |

**Example `/predict` request (Flask):**

```json
{
  "surface_area": 700,
  "wall_area": 300,
  "roof_area": 200,
  "overall_height": 6,
  "glazing_area": 25,
  "orientation": 2
}
```

**Response:**

```json
{
  "class": "Low Energy",
  "class_index": 0
}
```

---

## IoT Device Integration

Any HTTP-capable device can push live sensor readings to the backend. Once the first real reading arrives, the system automatically switches from simulation to real data.

**Endpoint:** `POST /sensor/push`

```json
{
  "room": "Living Room",
  "appliance": "AC",
  "power_w": 1480.5,
  "temp_c": 27.3,
  "is_on": true
}
```

Valid room names: `Living Room`, `Bedroom 1`, `Bedroom 2`, `Kitchen`, `Washroom`, `Utility`

**Example ESP32 / Arduino sketch:**

```cpp
HTTPClient http;
http.begin("http://YOUR_PC_IP:8000/sensor/push");
http.addHeader("Content-Type", "application/json");
String body = "{\"room\":\"Living Room\",\"appliance\":\"AC\","
              "\"power_w\":1480.5,\"temp_c\":27.3,\"is_on\":true}";
http.POST(body);
```

To revert to simulation mode: `POST /sensor/reset`

---

## Simulated Rooms & Appliances

| Room | Appliances |
|---|---|
| Living Room | AC, TV, Iron Box, Lights |
| Bedroom 1 | AC, Lights |
| Bedroom 2 | AC, Lights |
| Kitchen | Fridge, Grinder, Mixer, Microwave, Lights |
| Washroom | Geyser, Lights |
| Utility | Washing Machine, Lights |

Appliances are categorized as `continuous` (always on), `moderate`, or `occasional` (15% random chance per tick). Temperature per room is derived from base temperature plus load factor.

---

## Alert Thresholds

| Condition | Default Threshold | Configurable via `.env` |
|---|---|---|
| Overload | 6000 W total | `OVERLOAD_WATTS` |
| Overheat | 30 °C | `OVERHEAT_TEMP` |
| Fire risk | 8000 W total | Hardcoded in `main.py` |

Alerts are deduplicated in memory — the same condition won't trigger repeated SMS messages until it clears and re-triggers.

---

## What-If Simulation

The `/simulate` endpoint models the effect of adding extra appliances to the current load:

```json
{
  "current_power": 3200,
  "extra_appliances": ["Geyser", "Washing Machine"]
}
```

Returns total projected power, load level (`LOW` / `NORMAL` / `HIGH`), safety advice, hazard risk flag, and anomaly detection result.

---

## Dataset

The building energy classification model is trained on the [ENB2012 dataset](https://archive.ics.uci.edu/ml/datasets/Energy+efficiency) (UCI Machine Learning Repository). Features include surface area, wall area, roof area, overall height, glazing area, and orientation. The target is a three-class energy label: Low, Medium, or High.

---

## License

This project is for educational and research purposes.
