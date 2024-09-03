import json
from models import Event  

def preprocess_google_calendar_events(google_events):
    """
    Preprocess a list of events from Google Calendar and return a list of Event objects.
    """
    preprocessed_events = []
    for event in google_events:
        preprocessed_event = {
            "date": event["start"]["dateTime"][:10],
            "time": event["start"]["dateTime"][11:16],
            "location": event["location"],
            "description": event["summary"]
        }
        preprocessed_events.append(Event(**preprocessed_event))
    return preprocessed_events

def preprocess_events(event_data):
    """
    Preprocess event data from various sources and return a list of Event objects.
    
    This function can be extended to handle events from different platforms.
    """
    if "google" in event_data:
        return preprocess_google_calendar_events(event_data["google"])
    # Add more preprocessing functions for other event sources here...

# Example usage:
'''
google_event = {
    "summary": "Software Engineering Exam",
    "start": {
        "dateTime": "2024-11-03T09:00:00",
        "timeZone": "America/New_York"
    },
    "end": {
        "dateTime": "2024-11-03T10:30:00",
        "timeZone": "America/New_York"
    },
    "location": "University Campus, Lecture Hall A"
}
'''

# google_events = [...]  # List of raw events from Google Calendar API
# events = preprocess_events({"google": google_events})