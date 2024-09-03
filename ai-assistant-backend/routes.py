from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse
from models import ChatRequest, Message, Event
from utils import process_events, handle_exception
from config import cohere_client
from datetime import date, datetime, timedelta
from events import preprocess_events, preprocess_google_calendar_events
from calendar_tools import get_google_calendar_events, create_google_calendar_event, edit_google_calendar_event, delete_google_calendar_event

chat_route = APIRouter(prefix="/api/chat")

def get_calendar_events(date: str = None):
    events = get_google_calendar_events()

    if date:
        events_on_date = [event for event in events if event['date'] == date]
        return {
            "existing_events": events_on_date
        }
    else:
        return {
            "existing_events": events
        }

def create_calendar_event(date: str, time: str, description: str, location: str = None, duration: int = 1):
    def parse_time(time_str):

        # Try parsing 24-hour format
        try:
            return datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            # Else, try parsing 12-hour format
            return datetime.strptime(time_str, "%I%p").time()

    # If time is provided as a range (e.g., "09:00-17:00" or "9am-5pm"), use it directly
    if '-' in time:
        start_time, end_time = map(parse_time, time.split('-'))
        start_datetime = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), start_time)
        end_datetime = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), end_time)
        duration = (end_datetime - start_datetime).total_seconds() / 3600
        time = f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
    else:
        # If only start time is provided, calculate end time based on duration
        start_time = parse_time(time)
        start_datetime = datetime.combine(datetime.strptime(date, "%Y-%m-%d").date(), start_time)
        end_datetime = start_datetime + timedelta(hours=duration)
        time = f"{start_time.strftime('%H:%M')}-{end_datetime.time().strftime('%H:%M')}"

    return create_google_calendar_event(date, time, description, location, duration)

def edit_calendar_event(date: str, time: str, description: str, location: str = None, duration: int = None):
    def parse_time(time_str: str) -> time:
        # Try parsing 24-hour format
        try:
            return datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            # If that fails, try parsing 12-hour format
            return datetime.strptime(time_str, "%I%p").time()

    # First, get the events for the given date
    events = get_calendar_events(date)["existing_events"]
    
    # Find the event that matches the given description
    event_id = None
    original_event = None
    for event in events:
        if event['description'] == description:
            event_id = event['event_id']
            original_event = event
            break
    
    if event_id is None:
        return {"is_success": False, "message": "Event not found"}
    
    # Parse the time string
    if '-' in time:
        start_time, end_time = map(parse_time, time.split('-'))
    else:
        start_time = parse_time(time)
        if duration is None:
            duration = original_event['duration']
        end_time = (datetime.combine(datetime.min, start_time) + timedelta(hours=duration)).time()
    
    # Format times as strings
    start_time_str = start_time.strftime("%H:%M")
    end_time_str = end_time.strftime("%H:%M")
    
    # Now call edit_google_calendar_event with the found event_id
    result = edit_google_calendar_event(
        event_id, 
        date=date, 
        time=f"{start_time_str}-{end_time_str}", 
        description=description, 
        location=location, 
        duration=duration
    )
    
    if not result["is_success"]:
        return {"is_success": False, "message": f"Failed to edit event: {result['message']}"}
    
    return {"is_success": True, "message": f"Successfully edited event: {description}"}

def delete_calendar_event(date: str, time: str, description: str):
    # First, get the events for the given date
    events = get_calendar_events(date)["existing_events"]
    
    # Find the event that matches the given time and description
    event_id = None
    for event in events:
        if event['time'] == time and event['description'] == description:
            event_id = event['event_id']
            break
    
    if event_id is None:
        return {"is_success": False, "message": "Event not found"}
    
    # Now call delete_google_calendar_event with the found event_id
    return delete_google_calendar_event(event_id)



# define tool schema
tools = [
   {
       "name": "get_calendar_events",
       "description": "Gets the user's events for the current month, or for a specific date if provided. Includes date, time, location, and description.",
       "parameter_definitions": {
            "date": {
                "description": "Date of the event in YYYY-MM-DD format. If not provided, returns events for the current month.",
                "type": "str",
                "required": False
            },
        }
   }, 
    {
      "name": "create_calendar_event",
      "description": "Creates a new calendar event of the specified duration at the specified time and date. A new event cannot be created on the same time as an existing event.",
      "parameter_definitions": {
            "date": {
                "description": "Date of the event in YYYY-MM-DD format",
                "type": "str",
                "required": True
            },
            "time": {
                "description": "Time of the event in HH:MM format, or a start and end time range, or 9am-5pm if not specified",
                "type": "str",
                "required": True
            },
            "description": {
                "description": "Brief description of the event",
                "type": "str",
                "required": True
            },
            "location": {
                "description": "Venue or location of the event, or 'None' if not specified",
                "type": "str",
                "required": False
            },
            "duration": {
                "description": "Duration of the event in hours, or 1 if not specified",
                "type": "int",
                "required": False
            }
      }
    },
    {
      "name": "edit_calendar_event",
      "description": "Edits an existing calendar event. The event is identified by its date, time, and description.",
      "parameter_definitions": {
            "date": {
                "description": "Date of the event in YYYY-MM-DD format",
                "type": "str",
                "required": True
            },
            "time": {
                "description": "Time of the event in HH:MM format",
                "type": "str",
                "required": True
            },
            "description": {
                "description": "Brief description of the event",
                "type": "str",
                "required": True
            },
            "location": {
                "description": "New venue or location of the event, or 'None' if not specified",
                "type": "str",
                "required": False
            },
            "duration": {
                "description": "New duration of the event in hours",
                "type": "int",
                "required": False
            }
      }
    },
    {
      "name": "delete_calendar_event",
      "description": "Deletes an existing calendar event. The event is identified by its date, time, and description.",
      "parameter_definitions": {
            "date": {
                "description": "Date of the event in YYYY-MM-DD format",
                "type": "str",
                "required": True
            },
            "time": {
                "description": "Time of the event in HH:MM format",
                "type": "str",
                "required": True
            },
            "description": {
                "description": "Brief description of the event",
                "type": "str",
                "required": True
            }
      }
    }
]

functions_map = {
    "get_calendar_events": get_calendar_events,
    "create_calendar_event": create_calendar_event,
    "edit_calendar_event": edit_calendar_event,
    "delete_calendar_event": delete_calendar_event
}

model='command-r-plus-08-2024'

preamble=f'''
        ## Task & Context
        You are an expert calendar assistant with 10 years experiencewho helps people schedule events on their calendar.
        You must make sure that a new event does not overlap with any existing event and
        be very precise and incredibly detail-oriented with your responses. For example, you cannot just
        say "You have an event scheduled for tomorrow", you must state the description, date and time.
        Today is  {str(date.today())}. You are very helpful to a very
        busy user, who needs to balance scheduling work, parental duties, studies,and personal time.
        '''


@chat_route.post("/")
async def chat(request: ChatRequest):
    try:
        chat_history = []

        for msg in request.messages[:-1]:
            role = "User" if msg.role == "User" else "Chatbot"
            chat_history.append({"role": role, "message": msg.content})
        
        # Step 1: Get the last message (user's input)
        user_message = request.messages[-1].content

        # Step 2: Generate tool calls (if any)    
        response = cohere_client.chat(
            message=user_message,
            model=model,
            preamble=preamble,
            tools=tools,
            chat_history=chat_history
        )

        while True:
            if response.tool_calls:
                tool_calls = response.tool_calls
                print(f'Tool calls: {tool_calls}')
                
                if response.text:
                    print("Tool plan:")
                    print(response.text,"\n")
                print("Tool calls:")
                for call in tool_calls:
                    print(f"Tool name: {call.name} | Parameters: {call.parameters}")
                print("="*50)
                
                # Step 3: Get tool results
                tool_results = []
                for tc in tool_calls:
                    tool_call = {"name": tc.name, "parameters": tc.parameters}
                    tool_output = functions_map[tc.name](**tc.parameters)
                    tool_results.append({"call": tool_call, "outputs": [tool_output]})

                # Step 4: Generate response and citations
                response = cohere_client.chat(
                    message="",
                    model=model,
                    preamble=preamble,
                    tools=tools,
                    tool_results=tool_results,
                    chat_history=response.chat_history
                )
            else:
                # No tool calls, break the loop
                break
                
        # Append the current chat turn to the chat history
        chat_history = response.chat_history

        print("Final response:")
        print(response.text)
        print("="*50)

        # Define the event stream generator function
        async def event_stream():
            if response.text:
                for chunk in response.text:
                    yield chunk
            else:
                yield "No response generated."

        # Return the StreamingResponse with the event_stream generator
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        return handle_exception(e)