from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models import ChatRequest
from utils import handle_exception, summarize_conversation, extract_key_info
from calendar_tools import get_google_calendar_events
from db import store_conversation, get_relevant_conversations, get_recent_conversations
from router_agent import router_agent
import logging
import json

# Define the APIRouter for the chat route
chat_route = APIRouter(prefix="/api/chat")

# Define the APIRouter for the calendar route
calendar_route = APIRouter(prefix="/api/calendar")

logger = logging.getLogger(__name__)

MAX_CONTEXT_TURNS = 5
SUMMARY_INTERVAL = 10

@chat_route.post("/")
async def chat(request: ChatRequest):
    try:
        chat_history = []
        full_history = []
        previous_agent_type = None
        turn_count = 0

        for msg in request.messages[:-1]:
            full_history.append({"role": msg.role, "message": msg.content})
            if len(chat_history) < MAX_CONTEXT_TURNS:
                chat_history.append({"role": msg.role, "message": msg.content})
            if msg.role == "Chatbot" and hasattr(msg, 'agent_type'):
                previous_agent_type = msg.agent_type

        user_message = request.messages[-1].content
        turn_count = len(full_history) + 1

        if turn_count % SUMMARY_INTERVAL == 0:
            summary = summarize_conversation(full_history)
            chat_history = [{"role": "System", "message": f"Conversation summary: {summary}"}] + chat_history[-MAX_CONTEXT_TURNS:]

        key_info = extract_key_info(user_message)
        if key_info:
            chat_history.append({"role": "System", "message": f"Key information: {key_info}"})

        async def event_stream():
            full_response = ""
            agent_type = "unknown"
            
            for chunk in router_agent(user_message, chat_history, previous_agent_type, key_info):
                if chunk.get('role') == 'Chatbot':
                    full_response += chunk.get('message', '')
                    logger.info(f"Full response: {full_response}")
                    agent_type = chunk.get('agent_type', agent_type)
                    yield f"data: {json.dumps({'role': 'Chatbot', 'message': chunk.get('message', ''), 'agent_type': agent_type})}\n\n"

            # Update conversation history after full response is received
            full_history.append({"role": "User", "content": user_message})
            full_history.append({"role": "Chatbot", "message": full_response, "agent_type": agent_type})
            
            # Update chat_history for next turn
            updated_chat_history = full_history[-MAX_CONTEXT_TURNS:]

            store_conversation(user_message, full_response)
            
            logger.debug(f"Final response: {full_response}")

            yield f"data: {json.dumps({'updated_history': updated_chat_history})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

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
        events = get_google_calendar_events(date)
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
                "title": conv["document"].split("\n")[0][:50] + "...",  # Use first 50 chars of user input as title
                "timestamp": conv["metadata"]["timestamp"]
            }
            for conv in recent_convs
        ]
        return {"conversations": formatted_convs}
    except Exception as e:
        return handle_exception(e)

all_routes = [chat_route, calendar_route]