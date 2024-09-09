from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import all_routes
from dotenv import load_dotenv
from config import CORS_ORIGINS
from db import client as db_client
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize ChromaDB client
    db_client.heartbeat()
    print("ChromaDB client initialized")
    yield
    # Shutdown: Perform any cleanup if necessary
    print("Shutting down")

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Initialize ChromaDB client
    db_client.heartbeat()

# Include all routes
for route in all_routes:
    print(f"Registering routes with prefix: {route.prefix}")
    app.include_router(route)
    for r in route.routes:
        print(f"  - {r.methods} {r.path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)