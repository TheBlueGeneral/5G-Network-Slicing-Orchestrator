# orchestrator.py
import time, requests, numpy as np
from statsmodels.tsa.arima.model import ARIMA

# Configure slices
slices = {"sliceA": {"min_rate": 1000000}, "sliceB": {"min_rate": 500000}}
model = {}  # placeholder for trained models (ARIMA, etc)

def fetch_metrics(slice_name):
    # Query Prometheus for total bytes in last minute for slice
    url = f"http://localhost:9090/api/v1/query"
    query = f'rate(slice_bytes{{slice="{slice_name}"}}[1m])'
    res = requests.get(url, params={'query': query}).json()
    return float(res['data']['result'][0]['value'][1])

# Initialize ARIMA model for each slice (example)
for slice_name in slices:
    model[slice_name] = ARIMA([0], order=(1,1,1))  # dummy initialization

while True:
    new_rates = {}
    # Collect metrics for each slice
    for slice_name in slices:
        try:
            rate = fetch_metrics(slice_name)
        except Exception:
            rate = slices[slice_name].get("last_rate", 0)
        slices[slice_name]["last_rate"] = rate

        # Simple forecasting (could be replaced with more complex ML)
        # Use last N points from Prometheus (this is a simplification)
        arima_model = model[slice_name].fit()
        forecast = arima_model.forecast(steps=1)[0]  # next step
        new_rate = max(slices[slice_name]["min_rate"], int(forecast))
        new_rates[slice_name] = new_rate

    # Update controller via REST API
    for slice_name, rate in new_rates.items():
        data = {"slice": slice_name, "max_rate": rate}
        try:
            requests.post("http://localhost:8080/update_slice", json=data)
        except Exception as e:
            print("Failed to update slice:", e)

    time.sleep(5)
