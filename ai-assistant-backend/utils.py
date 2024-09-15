import json
from fastapi import HTTPException
from config import cohere_client

def process_events(messages: list):
    for msg in messages:
        if msg.role == "Events":
            return json.loads(msg.content)
    return {}

def handle_exception(error):
    print(f"Error: {error}")
    raise HTTPException(status_code=500, detail=str(error))

def summarize_conversation(history):
    conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    summary = cohere_client.summarize(text=conversation, length='short', format='paragraph', model='command')
    return summary.summary

def extract_key_info(message):
    # This is a simple implementation. You might want to use NER or other techniques for more sophisticated extraction.
    key_words = ["date", "time", "location", "person", "event"]
    extracted = []
    for word in key_words:
        if word in message.lower():
            extracted.append(word)
    return ", ".join(extracted) if extracted else None