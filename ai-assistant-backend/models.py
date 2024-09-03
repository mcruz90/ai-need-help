from pydantic import BaseModel, Field
from typing import List, Dict

class Message(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="List of messages in the chat history")

class Event(BaseModel):
    date: str = Field(..., description="Date of the event in YYYY-MM-DD format")
    time: str = Field(..., description="Time of the event in HH:MM format, or a start and end time range, or None if not specified")
    location: str = Field(..., description="Venue or location of the event, or 'No location provided' if not specified")
    description: str = Field(..., description="Brief description of the event")