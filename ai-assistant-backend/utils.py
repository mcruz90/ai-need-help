import json
from fastapi import HTTPException

def process_events(messages: list):
    for msg in messages:
        if msg.role == "Events":
            return json.loads(msg.content)
    return {}

def handle_exception(error):
    print(f"Error: {error}")
    raise HTTPException(status_code=500, detail=str(error))