from fastapi import APIRouter, BackgroundTasks
from models import ChatRequest
from utils import handle_exception
from agents.calendar.google_calendar_api import GoogleCalendarAPI
from db import get_relevant_conversations, get_recent_conversations
#from agents.router.router_agent import router_agent
from agents.triage.triage_agent import triage_agent
from utils import logger

# Define the APIRouter for the chat route
chat_route = APIRouter(prefix="/api/chat")

# Define the APIRouter for the calendar route
calendar_route = APIRouter(prefix="/api/calendar")

MAX_CONTEXT_TURNS = 20
SUMMARY_INTERVAL = 20

@chat_route.post("/")
async def chat(client_request: ChatRequest, background_tasks: BackgroundTasks):
    try:
        chat_history = []
        
         # Process incoming messages and build chat history
        for msg in client_request.messages:
            if len(chat_history) < MAX_CONTEXT_TURNS:
                chat_history.append({"role": msg.role, "content": msg.content})
        
        user_message = client_request.messages[-1].content

        if not client_request.messages:
            logger.error("No messages provided from the client")
            return {"error": "No messages provided from the client"}
        
        logger.info(f"User message: {user_message}")
        logger.info(f"Chat history: {chat_history}")

        return await triage_agent(user_message, chat_history, background_tasks)

    except Exception as e:
        logger.error(f"Error in chat route: {str(e)}", exc_info=True)
        return handle_exception(e)

@chat_route.get("/history")
async def get_chat_history(query: str):
    """
    This route retrieves relevant conversations from the database based on the user's query.
    params:
        query: str
    returns:
        conversations: list of relevant conversations
    """
    try:
        relevant_convs = get_relevant_conversations(query)
        return {"conversations": relevant_convs}
    except Exception as e:
        return handle_exception(e)

@calendar_route.get("/events")
async def get_events(date: str):
    """
    This route retrieves events from the user's Google Calendar for a given date.
    params:
        date: str
    returns:
        events: list of events
    """
    try:
        calendar_api = GoogleCalendarAPI()
        events = calendar_api.get_google_calendar_events(date)
        return {"events": events}
    except Exception as e:
        return handle_exception(e)

@chat_route.get("/past-conversations")
async def get_past_conversations():
    """
    This route retrieves recent conversations from the database.
    returns:
        conversations: list of recent conversations
    """
    try:
        recent_convs = get_recent_conversations(n_results=10)
        formatted_convs = [
            {
                "id": conv["id"],
                "title": conv["document"].split("\n")[0][:100] + "...",  # Use first 50 chars of user input as title
                "timestamp": conv["metadata"]["timestamp"]
            }
            for conv in recent_convs
        ]
        return {"conversations": formatted_convs}
    except Exception as e:
        return handle_exception(e)
all_routes = [chat_route, calendar_route]
