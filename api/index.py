from fastapi import FastAPI, Request
from pydantic import BaseModel
import json
import os
import math

app = FastAPI()

# 1. THE SLEDGEHAMMER: Force the header on absolutely every response
@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# 2. Handle the preflight OPTIONS request the bot might send
@app.options("/{path:path}")
async def options_handler(path: str):
    return {"message": "CORS allowed"}

class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

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

# 3. Prevent Redirect Traps by answering to all variations of the URL
@app.post("/api")
@app.post("/api/")
@app.post("/")
def get_analytics(request: AnalyticsRequest):
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

    return results
