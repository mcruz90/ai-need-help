from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models import ChatRequest
from utils import handle_exception
from datetime import date
from calendar_tools import get_google_calendar_events
from db import store_conversation, get_relevant_conversations, get_recent_conversations
from router_agent import router_agent

# Define the APIRouter for the chat route
chat_route = APIRouter(prefix="/api/chat")

# Define the APIRouter for the calendar route
calendar_route = APIRouter(prefix="/api/calendar")

model='command-r-plus-08-2024'

preamble=f'''
        ## Task & Context
        You are an expert personal assistant named 'Aiko'with 10 years experience who helps users with their calendar and are also an expert at answering general questions from your internal knowledge.
        When answering questions related to calendars, you must make sure that a new event does not overlap with any existing event.vent and
        You are very precise and detail-oriented with your responses. For example, you cannot just
        say "You have an event scheduled for tomorrow", you must state the description, date and time.
        If you cannot find the event given only the description, you must say so. Do not make up the event or search every single date, as this is not efficient.
        
        Do not refuse questions that are not related to scheduling, you have access to your internal knowledge if there are no available tools.
        
        Today is  {str(date.today())}.
        
        You are very helpful to a very busy user, who needs to balance scheduling work, parental duties, studies, and personal time, and needs a personal tutor.
        '''

@chat_route.post("/")
async def chat(request: ChatRequest):
    """
    This is the main chat route that handles the chat history, retrieves relevant conversations, generates tool calls, and streams the response.
    params:
        request: ChatRequest from the client
    returns:
        response: StreamingResponse to the client
    """
    try:
        chat_history = []

        # use model Message to format the current chat turn
        for msg in request.messages[:-1]:
            role = "User" if msg.role == "User" else "Chatbot"
            chat_history.append({"role": role, "message": msg.content})
        
        # Get the last message (user's input)
        user_message = request.messages[-1].content
        
        # Retrieve relevant past conversations from the database and add to preamble
        relevant_conversations = get_relevant_conversations(user_message)
        relevant_context = "\n\nRelevant past conversations:\n" + "\n".join(relevant_conversations)
        updated_preamble = preamble + relevant_context

        # Route the user message to the appropriate agent and get the response
        router_response = router_agent(user_message, chat_history, updated_preamble)
                
        # Append the current chat turn to the chat history
        chat_history.append(router_response)

        # Store the conversation in the database
        store_conversation(user_message, router_response["message"])

        print("Final response:")
        print(router_response["message"])
        print("="*50)

        # Define the event stream generator function to stream the response to the client
        async def event_stream():
            if router_response:
                for chunk in router_response["message"]:
                    yield chunk
            else:
                yield "No response generated."

        # Return the StreamingResponse with the event_stream generator
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
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