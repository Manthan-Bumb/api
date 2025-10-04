from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime
from pathlib import Path
import numpy as np

app = FastAPI()

# Enable CORS - Allow all origins, methods, and headers for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["*"],  # Allow all methods including POST
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"]  # Expose all headers
)

@app.options("/{full_path:path}")
async def options_handler(request: Request):
    return Response(
        content="",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
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

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/api/python")
def hello_world():
    return {"message": "Hello World"}

@app.post("/api/latency")
async def log_latency(request: Request):
    try:
        data = await request.json()
        
        # Get the latency data
        latency = data.get('latency', 0)
        timestamp = datetime.utcnow().isoformat()
        
        # Create the log entry
        log_entry = {
            "timestamp": timestamp,
            "latency_ms": latency,
            "user_agent": request.headers.get('user-agent', 'unknown'),
            "data": data
        }
        
        # In a production environment, you would save this to a database
        # For now, we'll just log it
        print(f"Latency logged: {json.dumps(log_entry)}")
        
        return {
            "success": True,
            "message": "Latency data received",
            "logged_at": timestamp
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/analytics")
async def post_analytics(request: Request):
    """Analytics endpoint for processing latency metrics data"""
    try:
        data = await request.json()
        timestamp = datetime.utcnow().isoformat()
        
        # Process analytics data
        # The data should contain region, service, latency_ms, uptime_pct, timestamp
        analytics_log = {
            "received_at": timestamp,
            "data": data,
            "user_agent": request.headers.get('user-agent', 'unknown')
        }
        
        # In a production environment, you would save this to a database
        print(f"Analytics data logged: {json.dumps(analytics_log)}")
        
        return {
            "success": True,
            "message": "Analytics data received and processed",
            "received_at": timestamp,
            "records_count": len(data) if isinstance(data, list) else 1
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

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
