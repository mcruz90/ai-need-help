import json
from attr import attributes
import html_sanitizer
from fastapi import HTTPException
from config import cohere_client


sanitizer = html_sanitizer.Sanitizer({
    'tags': ('a', 'b', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'i', 'u', 'em', 'strong', 'p', 'span', 'br', 'ul', 'ol', 'li', 'hr', 'sup'),
    'attributes': {
        'a': ('href', 'name', 'target', 'title', 'id', 'rel'),
        'span': ('class', 'style'),
        'p': ('class', 'style'),
        'li': ('class', 'style'),
        'ul': ('class', 'style'),
        'ol': ('class', 'style'),
        'h1': ('class', 'style'),
        'h2': ('class', 'style'),
        'h3': ('class', 'style'),
        'h4': ('class', 'style'),
        'h5': ('class', 'style'),
        'h6': ('class', 'style'),
        'span': ('class', 'style'),
    },
    "empty": {"hr", "a", "br"},
    "separate": {"a", "p", "li"},
    
    }
)


def sanitize_html_content(html_content: str) -> str:
    """
    Sanitizes the HTML content to prevent XSS attacks.
    """
    return sanitizer.sanitize(html_content)


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