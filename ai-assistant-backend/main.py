from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import all_routes
from config import Config
from db import client as db_client
from contextlib import asynccontextmanager
from prometheus_client import Counter, Summary, Gauge
from prometheus_client.openmetrics.exposition import generate_latest
from starlette.responses import Response

# Create metrics
REQUEST_COUNT = Counter('request_count', 'Total request count')
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
DB_CONNECTION_GAUGE = Gauge('db_connection', 'Database connection status')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize ChromaDB client
    db_client.heartbeat()
    DB_CONNECTION_GAUGE.set(1)  # Set to 1 when connected
    print("ChromaDB client initialized")
    yield
    # Shutdown: Perform any cleanup if necessary
    DB_CONNECTION_GAUGE.set(0)  # Set to 0 when disconnected
    print("Shutting down")

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

# Middleware to count requests and measure request time
@app.middleware("http")
async def metrics_middleware(request, call_next):
    REQUEST_COUNT.inc()
    with REQUEST_TIME.time():
        response = await call_next(request)
    return response

# Include all routes
for route in all_routes:
    print(f"Registering routes with prefix: {route.prefix}")
    app.include_router(route)
    for r in route.routes:
        print(f"  - {r.methods} {r.path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
