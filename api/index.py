from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
import math

app = FastAPI()

class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

# Load the data once
json_path = os.path.join(os.path.dirname(__file__), 'q-vercel-latency.json')
with open(json_path, 'r') as f:
    raw_data = json.load(f)
    if isinstance(raw_data, dict):
        for key, value in raw_data.items():
            if isinstance(value, list):
                ALL_DATA = value
                break
        else:
            ALL_DATA = []
    else:
        ALL_DATA = raw_data

def calculate_percentile(data, percentile):
    if not data: return 0
    data.sort()
    k = (len(data) - 1) * (percentile / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c: return data[int(k)]
    return data[int(f)] * (c - k) + data[int(c)] * (k - f)

# 1. Answer the invisible OPTIONS preflight check with the hardcoded header
@app.options("/api")
@app.options("/api/")
@app.options("/")
async def preflight():
    return JSONResponse(
        content={"message": "CORS allowed"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

# 2. Answer the actual POST test with the hardcoded header
@app.post("/api")
@app.post("/api/")
@app.post("/")
async def get_analytics(request: AnalyticsRequest):
    results = {}

    for region in request.regions:
        region_data = [row for row in ALL_DATA if isinstance(row, dict) and str(row.get('region', '')).lower() == str(region).lower()]
        
        if not region_data:
            continue

        latencies = [float(r['latency']) for r in region_data if 'latency' in r]
        uptimes = [float(r['uptime']) for r in region_data if 'uptime' in r]
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p95_latency = calculate_percentile(latencies, 95) if latencies else 0
        avg_uptime = sum(uptimes) / len(uptimes) if uptimes else 0
        
        breaches = sum(1 for l in latencies if l > request.threshold_ms)

        results[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    # 3. Manually pack the math results AND the required headers together
    return JSONResponse(
        content=results,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )
