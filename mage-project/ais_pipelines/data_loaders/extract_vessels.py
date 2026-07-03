import json
import os

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

USE_LIVE_API = False
SAMPLE_FILE = "/home/src/sample_vessels_panama.json"

@data_loader
def extract_vessels(*args, **kwargs):
    if USE_LIVE_API:
        import requests
        API_KEY = os.environ.get("DATADOCKED_API_KEY", "831569d1b89cc99f1af788ad7996ab40")
        headers = {"accept": "application/json", "x-api-key": API_KEY}
        params = {"latitude": 9.08, "longitude": -79.68, "circle_radius": 50}
        resp = requests.get(
            "https://datadocked.com/api/vessels_operations/get-vessels-by-area",
            headers=headers, params=params, timeout=15
        )
        resp.raise_for_status()
        return resp.json()["vessels"]
    else:
        with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["vessels"]