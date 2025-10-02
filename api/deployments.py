from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from pathlib import Path
import numpy as np

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_telemetry_data():
    """Load telemetry data from q-vercel-latency.json"""
    # Try multiple possible paths
    possible_paths = [
        Path("q-vercel-latency.json"),
        Path("../q-vercel-latency.json"),
        Path("/var/task/q-vercel-latency.json"),
    ]
    
    for path in possible_paths:
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
    
    # If file not found, return empty list
    return []

def calculate_metrics(data, regions, threshold_ms):
    """Calculate per-region metrics"""
    results = {}
    
    for region in regions:
        # Filter data for this region
        region_data = [item for item in data if item.get('region', '').lower() == region.lower()]
        
        if not region_data:
            results[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            }
            continue
        
        # Extract latency and uptime values
        latencies = [item.get('latency_ms', 0) for item in region_data]
        uptimes = [item.get('uptime_pct', 0) for item in region_data]
        
        # Calculate metrics
        avg_latency = np.mean(latencies) if latencies else 0
        p95_latency = np.percentile(latencies, 95) if latencies else 0
        avg_uptime = np.mean(uptimes) if uptimes else 0
        breaches = sum(1 for latency in latencies if latency > threshold_ms)
        
        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches
        }
    
    return results

@app.post("/api/deployments")
async def deployments(request: Request):
    try:
        # Parse request body
        body = await request.json()
        regions = body.get('regions', [])
        threshold_ms = body.get('threshold_ms', 180)
        
        # Validate inputs
        if not regions:
            return {
                "success": False,
                "error": "regions parameter is required"
            }
        
        # Load telemetry data
        telemetry_data = load_telemetry_data()
        
        if not telemetry_data:
            return {
                "success": False,
                "error": "No telemetry data available"
            }
        
        # Calculate metrics
        metrics = calculate_metrics(telemetry_data, regions, threshold_ms)
        
        return {
            "success": True,
            "metrics": metrics
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
