from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat_route
from dotenv import load_dotenv
from config import CORS_ORIGINS

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the chat route
app.include_router(chat_route)