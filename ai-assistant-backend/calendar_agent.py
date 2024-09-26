from config import cohere_client, cohere_model as model
from tools_utils import tools, functions_map
from datetime import date
from functools import lru_cache
from datetime import datetime, timedelta

preamble=f"""
        ## Task & Context
        You are an expert calendar assistant named 'Aiko' with over 10 years experience who helps users with their scheduling.
        You must make sure that a new event does not overlap with any existing event.
        You are very precise and detail-oriented with your responses. For example, you cannot just
        say "You have an event scheduled for tomorrow", you must state the description, date and time.
        If you cannot find the event given only the description, you must say so. Do not make up the event or search every single date, as this is not efficient.
        
        Today is  {str(date.today())}.
        """

@lru_cache(maxsize=100)
def get_cached_calendar_events(date: str):
    # Your existing get_calendar_events logic here
    ...

def get_calendar_events(date: str):
    # Check if the cache is still valid (e.g., within the last minute)
    cache_key = f"calendar_events_{date}"
    cached_result = get_cached_calendar_events(date)
    if cached_result and (datetime.now() - cached_result['timestamp']) < timedelta(minutes=1):
        return cached_result['events']
    
    # If not cached or cache expired, fetch new data
    events = get_cached_calendar_events(date)
    return {'timestamp': datetime.now(), 'events': events}

def calendar_agent(user_message, chat_history) -> dict:
    # Ensure all elements in chat_history have a 'message' field
    formatted_history = []
    for msg in chat_history:
        if isinstance(msg, dict):
            formatted_msg = {
                'role': msg.get('role', ''),
                'message': msg.get('message', msg.get('content', ''))
            }
        else:
            formatted_msg = {
                'role': getattr(msg, 'role', ''),
                'message': getattr(msg, 'message', getattr(msg, 'content', ''))
            }
        formatted_history.append(formatted_msg)

    response = cohere_client.chat(
        message=user_message,
        model=model,
        preamble=preamble,
        tools=tools,
        chat_history=formatted_history
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
            
            tool_results = []
            for tc in tool_calls:
                tool_call = {"name": tc.name, "parameters": tc.parameters}
                tool_output = functions_map[tc.name](**tc.parameters)
                tool_results.append({"call": tool_call, "outputs": [tool_output]})

            response = cohere_client.chat(
                message="",
                model=model,
                preamble=preamble,
                tools=tools,
                tool_results=tool_results,
                chat_history=response.chat_history
            )
        else:
            break
    
    # Return only the text content
    return {"response": response.text}