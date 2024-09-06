from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse
from models import ChatRequest, Message, Event
from utils import process_events, handle_exception
from config import cohere_client
from datetime import date
from events import preprocess_events, preprocess_google_calendar_events
from tools_utils import tools, functions_map

chat_route = APIRouter(prefix="/api/chat")

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