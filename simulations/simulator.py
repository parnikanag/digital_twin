import time
import requests
import random

URL = "http://127.0.0.1:5000/predict"

while True:
    data = {
        "surface_area": random.uniform(500, 1000),
        "wall_area": random.uniform(200, 500),
        "roof_area": random.uniform(100, 300),
        "overall_height": random.uniform(3, 10),
        "glazing_area": random.uniform(0, 50),
        "orientation": random.randint(1, 4),
    }
    try:
        r = requests.post(URL, json=data, timeout=5)
        r.raise_for_status()
        print(r.json())
    except requests.exceptions.ConnectionError:
        print("Server not reachable, retrying in 5s...")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    time.sleep(5)
