from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional  # Add Optional here
from langchain_core.pydantic_v1 import BaseModel as LangchainBaseModel, Field as LangchainField


# Common configuration for all models
common_config = ConfigDict(populate_by_name=True)

class Message(BaseModel):
    model_config = common_config
    role: str = Field(description="Role of the message sender")
    content: str = Field(description="Content of the message")

class ChatRequest(BaseModel):
    model_config = common_config
    messages: List[Message] = Field(description="List of messages in the chat history")
    conversation_id: Optional[str] = Field(default=None, description="ID of the conversation if continuing an existing one")

class Event(BaseModel):
    model_config = common_config
    date: str = Field(description="Date of the event in YYYY-MM-DD format")
    time: str = Field(description="Time of the event in HH:MM format, or a start and end time range, or None if not specified")
    location: str = Field(description="Venue or location of the event, or 'No location provided' if not specified")
    description: str = Field(description="Brief description of the event")

class TavilySearchInput(LangchainBaseModel):
    query: str = LangchainField(description="Query to search the internet with")