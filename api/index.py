from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: int

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

# Listen to both /api and / to prevent Vercel routing quirks
@app.post("/api")
@app.post("/")
def get_analytics(request: AnalyticsRequest):
    results = {}

    for region in request.regions:
        region_data = [row for row in ALL_DATA if row.get('region') == region]
        
        if not region_data:
            continue

        latencies = [r['latency'] for r in region_data]
        uptimes = [r['uptime'] for r in region_data]
        
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = calculate_percentile(latencies, 95)
        avg_uptime = sum(uptimes) / len(uptimes)
        
        breaches = sum(1 for l in latencies if l > request.threshold_ms)

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return results
