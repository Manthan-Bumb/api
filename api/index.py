from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime

app = FastAPI()

# Enable CORS - Allow all origins, methods, and headers for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including POST
    allow_headers=["*"],  # Allow all headers
)

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
