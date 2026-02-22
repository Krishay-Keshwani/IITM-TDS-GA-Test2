# Add BOTH of these lines right above your function
@app.post("/api")
@app.post("/")
def get_analytics(request: AnalyticsRequest):
    # ... rest of your code ...
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import math

app = FastAPI()

# 1. Enable CORS so the dashboard can talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Define the shape of the data we expect to receive
class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: int

# 3. Load the data once when the server "wakes up"
# We use os.path to find the JSON file sitting right next to this script
json_path = os.path.join(os.path.dirname(__file__), 'q-vercel-latency.json')
with open(json_path, 'r') as f:
    ALL_DATA = json.load(f)

def calculate_percentile(data, percentile):
    if not data: return 0
    data.sort()
    k = (len(data) - 1) * (percentile / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c: return data[int(k)]
    return data[int(f)] * (c - k) + data[int(c)] * (k - f)

@app.post("/api")
def get_analytics(request: AnalyticsRequest):
    # This dictionary will hold our results
    results = {}

    # Loop through each region the user asked for
    for region in request.regions:
        # Filter: Find all rows in the big dataset that match this region
        region_data = [row for row in ALL_DATA if row.get('region') == region]
        
        if not region_data:
            continue

        # Extract just the numbers we need
        latencies = [r['latency'] for r in region_data]
        uptimes = [r['uptime'] for r in region_data]
        
        # Calculate the 4 required metrics
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = calculate_percentile(latencies, 95)
        avg_uptime = sum(uptimes) / len(uptimes)
        
        # Count how many times latency went over the threshold
        breaches = sum(1 for l in latencies if l > request.threshold_ms)

        # Add to our results
        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }


    return results
