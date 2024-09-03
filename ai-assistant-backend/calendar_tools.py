import datetime
import os.path
import logging
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# logging.basicConfig(level=logging.DEBUG)

def get_google_calendar_events():
    """Fetches events from all of the user's Google Calendars for the current month."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        
        # Calculate the start and end of the current month
        today = datetime.datetime.now(pytz.UTC)
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = start_of_month + datetime.timedelta(days=32)
        end_of_month = next_month.replace(day=1) - datetime.timedelta(seconds=1)

        # Convert to RFC3339 format
        time_min = start_of_month.isoformat()
        time_max = end_of_month.isoformat()

        # Get the user's primary calendar to retrieve the timezone
        calendar = service.calendars().get(calendarId='primary').execute()
        user_timezone = calendar['timeZone']

        # Get list of all calendars
        calendar_list = service.calendarList().list().execute()

        events_list = []  # Initialize a list to hold event dictionaries
        for calendar in calendar_list['items']:
            calendar_id = calendar['id']
            events_result = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))
                
                # Handle timezone-aware datetime strings
                if 'T' in start:
                    start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                    
                    # Convert to user's timezone
                    start_dt = start_dt.astimezone(pytz.timezone(user_timezone))
                    end_dt = end_dt.astimezone(pytz.timezone(user_timezone))
                    
                    duration = (end_dt - start_dt).total_seconds() / 3600
                    formatted_time = f"{start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"
                else:
                    start_dt = datetime.datetime.strptime(start, "%Y-%m-%d")
                    formatted_time = "All day"
                    duration = 24  # All-day event

                event_info = {
                    "event_id": event["id"],
                    "calendar_id": calendar_id,
                    "calendar_name": calendar['summary'],
                    "date": start_dt.date().isoformat(),
                    "time": formatted_time,
                    "duration": round(duration, 2),
                    "location": event.get("location", "No location provided"),
                    "description": event["summary"]
                }
                events_list.append(event_info)

        # Sort events by date and time
        events_list.sort(key=lambda x: (x['date'], x['time']))

        return events_list  # Return all events for the current month

    except HttpError as error:
        logging.error(f"An error occurred: {error}")
        return []


def create_google_calendar_event(date: str, time: str, description: str, location: str = None, duration: float = 1):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        
        # Get the user's timezone
        calendar = service.calendars().get(calendarId='primary').execute()
        user_timezone = calendar['timeZone']

        # Check if it's an all-day event
        if time == "00:00-23:59" or time.lower() == "all day":
            start = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            end = start + datetime.timedelta(days=1)
            event = {
                'summary': description,
                'location': location,
                'start': {
                    'date': start.isoformat(),
                },
                'end': {
                    'date': end.isoformat(),
                },
            }
        else:
            # For regular time-bound events
            start_time, end_time = time.split('-')
            start_datetime = datetime.datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            
            event = {
                'summary': description,
                'location': location,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': user_timezone,
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': user_timezone,
                },
            }

        event = service.events().insert(calendarId='primary', body=event).execute()
        
        return {
            "is_success": True,
            "message": f"Created event '{description}' on {date} {'all day' if time == '00:00-23:59' or time.lower() == 'all day' else f'from {time}'}"
        }

    except HttpError as error:
        return {
            "is_success": False,
            "message": f"An error occurred: {error}"
        }

def edit_google_calendar_event(event_id: str, date: str = None, time: str = None, description: str = None, location: str = None, duration: float = None):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        
        # Get the existing event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        logging.debug(f"Original event: {event}")
        
        # Get the user's timezone
        calendar = service.calendars().get(calendarId='primary').execute()
        user_timezone = calendar['timeZone']
        
        # Update the event details if provided
        if date and time:
            start_time, end_time = time.split('-')
            start_datetime = datetime.datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            
            event['start'] = {
                'dateTime': start_datetime.isoformat(),
                'timeZone': user_timezone,
            }
            event['end'] = {
                'dateTime': end_datetime.isoformat(),
                'timeZone': user_timezone,
            }
        
        if description:
            event['summary'] = description
        
        if location:
            event['location'] = location

        logging.debug(f"Updated event (before API call): {event}")
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        logging.debug(f"Updated event (after API call): {updated_event}")
        
        return {
            "is_success": True,
            "message": f"Updated event '{updated_event['summary']}' to {time}"
        }

    except HttpError as error:
        return {
            "is_success": False,
            "message": f"An error occurred: {error}"
        }

def delete_google_calendar_event(event_id: str):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        
        return {
            "is_success": True,
            "message": f"Deleted event with ID: {event_id}"
        }

    except HttpError as error:
        return {
            "is_success": False,
            "message": f"An error occurred: {error}"
        }


'''
def create_calendar_event(date: str, time: str, duration: int):
  
  return {
        "is_success": True,
        "message": f"Created a {duration} hour long event at {time} on {date}"
    }

functions_map = {
    "get_calendar_events": get_calendar_events,
    "create_calendar_event": create_calendar_event
}

'''


if __name__ == "__main__":
    events = get_google_calendar_events()
    print(events)  # Print the events when running this script directly