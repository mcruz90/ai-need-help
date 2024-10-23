from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from models import ChatRequest
from agents.calendar.google_calendar_api import GoogleCalendarAPI
from db import get_relevant_conversations, get_recent_conversations
from agents.triage.triage_agent import triage_agent
from utils.utils import logger, handle_exception
from fileupload.file_handler import FileProcessor
from typing import Optional, List
import json

# APIRouter for the chat route
chat_route = APIRouter(prefix="/api/chat")

# APIRouter for the calendar route
calendar_route = APIRouter(prefix="/api/calendar")

# APIRouter for the file upload route
file_upload_route = APIRouter(prefix="/api/files")

MAX_CONTEXT_TURNS = 20
SUMMARY_INTERVAL = 20

@chat_route.post("/")
async def chat(
    background_tasks: BackgroundTasks,
    request: ChatRequest
):
    try:
        logger.info(f"Received request: {request}")
        messages = request.messages
        
        if not messages:
            logger.error("No messages provided from the client")
            raise ValueError("No messages provided")

        # Find the last user message
        for msg in reversed(messages):
            if msg.role == 'user':
                user_message = msg.content
                break
        else:
            raise ValueError("No user message found")

        logger.info(f"Processing user message: {user_message}")

        # Format chat history excluding empty messages and the current message
        formatted_chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[:-1]
            if msg.content.strip()  # Only include messages with content
        ]

        # Add current message to chat history
        formatted_chat_history.append({"role": "user", "content": user_message})

        # Log the formatted history for debugging
        logger.debug(f"Formatted chat history: {formatted_chat_history}")

        # Get response from triage agent
        triage_response = await triage_agent(user_message, formatted_chat_history, background_tasks)

        async def event_stream():
            if isinstance(triage_response, StreamingResponse):
                async for chunk in triage_response.body_iterator:
                    if isinstance(chunk, bytes):
                        text = chunk.decode('utf-8')
                        
                        if text.strip() == '__CITATIONS_START__':
                            yield text.encode('utf-8')
                            continue
                        
                        if '"raw_response"' in text:
                            yield text.encode('utf-8')
                            continue
                        
                        try:
                            yield json.dumps({"content": text.strip()}) + "\n"
                        except Exception as e:
                            logger.error(f"Error encoding chunk: {e}")
                            yield json.dumps({"content": str(text)}) + "\n"
            else:
                yield json.dumps({"content": str(triage_response)}) + "\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream"
        )

    except Exception as e:
        logger.error(f"Error in chat route: {str(e)}", exc_info=True)
        return handle_exception(e)

@chat_route.post("/upload")
async def chat_with_file(
    background_tasks: BackgroundTasks,
    message: str = Form(...),
    chat_history: str = Form(default="[]"),
    files: List[UploadFile] = File(None)
):
    try:
        logger.info(f"Received message: {message}")
        logger.info(f"Number of files received: {len(files) if files else 0}")
        
        chat_history_list = json.loads(chat_history)
        formatted_chat_history = [
            {"role": msg.get("role"), "content": msg.get("content")}
            for msg in chat_history_list
            if len(chat_history) < MAX_CONTEXT_TURNS
        ]
        
        file_processor = FileProcessor()
        processed_files = []

        # Process and store files in ChromaDB
        if files:
            for file in files:
                logger.info(f"Processing file: {file.filename}")
                file_content = await file.read()
                # Store chunks and embeddings in ChromaDB
                await file_processor.process_and_store_file(file_content, file.filename)
                processed_files.append(file.filename)

        # Only include filenames in the user message for context
        if processed_files:
            file_context = f"I've uploaded these files: {', '.join(processed_files)}. "
            user_message = f"{file_context}{message}"
            logger.info(f"Added file context to query: {user_message}")
        else:
            user_message = message

        # Add current message to chat history
        formatted_chat_history.append({"role": "user", "content": user_message})

        # Pass to triage agent with just the query and file context
        response = await triage_agent(user_message, formatted_chat_history, background_tasks)

        async def event_stream():
            if isinstance(response, StreamingResponse):
                async for chunk in response.body_iterator:
                    if isinstance(chunk, bytes):
                        text = chunk.decode('utf-8')
                        
                        if text.strip() == '__CITATIONS_START__':
                            yield text.encode('utf-8')
                            continue
                        
                        if '"raw_response"' in text:
                            yield text.encode('utf-8')
                            continue
                        
                        try:
                            yield json.dumps({"content": text.strip()}) + "\n"
                        except Exception as e:
                            logger.error(f"Error encoding chunk: {e}")
                            yield json.dumps({"content": str(text)}) + "\n"
            else:
                yield json.dumps({"content": str(response)}) + "\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream"
        )

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
    
all_routes = [chat_route, calendar_route, file_upload_route]
