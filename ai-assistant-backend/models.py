from pydantic import BaseModel, Field
from typing import List, Dict
from langchain_core.pydantic_v1 import BaseModel as LangchainBaseModel, Field as LangchainField

class Message(BaseModel):
    role: str = Field(description="Role of the message sender")
    content: str = Field(description="Content of the message")

    model_config = {
        "populate_by_name": True
    }

class ChatRequest(BaseModel):
    messages: List[Message] = Field(description="List of messages in the chat history")

    model_config = {
        "populate_by_name": True
    }

class Event(BaseModel):
    date: str = Field(description="Date of the event in YYYY-MM-DD format")
    time: str = Field(description="Time of the event in HH:MM format, or a start and end time range, or None if not specified")
    location: str = Field(description="Venue or location of the event, or 'No location provided' if not specified")
    description: str = Field(description="Brief description of the event")

    model_config = {
        "populate_by_name": True
    }

class TavilySearchInput(LangchainBaseModel):
    query: str = LangchainField(description="Query to search the internet with")