import datetime
import os.path
import logging
import pytz
from functools import lru_cache
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# logging.basicConfig(level=logging.DEBUG)

def get_cached_google_calendar_events(target_date: str = None, cache_duration: int = 15):
    """
    Fetches and caches Google Calendar events.
    
    :param target_date: The date to fetch events for (optional)
    :param cache_duration: How long to cache the results in minutes
    :return: List of calendar events
    """
    cache_key = f"calendar_events_{target_date}"
    
    # Check if we have a cached result that's still valid
    if hasattr(get_cached_google_calendar_events, cache_key):
        cached_data, cache_time = getattr(get_cached_google_calendar_events, cache_key)
        if datetime.datetime.now() - cache_time < datetime.timedelta(minutes=cache_duration):
            logging.info(f"Returning cached calendar events for {target_date}")
            return cached_data

    # If no valid cache, fetch the events
    events = get_google_calendar_events(target_date)
    
    # Store the result and the time it was fetched
    setattr(get_cached_google_calendar_events, cache_key, (events, datetime.datetime.now()))
    
    logging.info(f"Fetched and cached new calendar events for {target_date}")
    return events

def get_calendar_events(date: str = None):
    """
    Fetches google calendar events from cache
    :param date: The date to fetch events for (optional)
    :return: List of calendar events for the given date or current month
    """
    events = get_cached_google_calendar_events(date)
    return {
        "existing_events": events
    }

def create_calendar_event(date: str, time: str, description: str, location: str = None, duration: int = 1):
    """
    Creates a new calendar event
    :param date: The date of the event in YYYY-MM-DD format
    :param time: The time of the event in HH:MM format, or a start and end time range, or 9am-5pm if not specified
    :param description: The description of the event
    :param location: The location of the event (optional)
    :param duration: The duration of the event in hours (optional)
    :return: The result of the event creation
    """
    def parse_time(time_str):
        # Try parsing 24-hour format
        try:
            return datetime.datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            # Else, try parsing 12-hour format
            return datetime.datetime.strptime(time_str, "%I%p").time()

    # If time is provided as a range (e.g., "09:00-17:00" or "9am-5pm"), use it directly
    if '-' in time:
        start_time, end_time = map(parse_time, time.split('-'))
        start_datetime = datetime.datetime.combine(datetime.datetime.strptime(date, "%Y-%m-%d").date(), start_time)
        end_datetime = datetime.datetime.combine(datetime.datetime.strptime(date, "%Y-%m-%d").date(), end_time)
        duration = (end_datetime - start_datetime).total_seconds() / 3600
        time = f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
    else:
        # If only start time is provided, calculate end time based on duration
        start_time = parse_time(time)
        start_datetime = datetime.datetime.combine(datetime.datetime.strptime(date, "%Y-%m-%d").date(), start_time)
        end_datetime = start_datetime + datetime.timedelta(hours=duration)
        time = f"{start_time.strftime('%H:%M')}-{end_datetime.time().strftime('%H:%M')}"

    return create_google_calendar_event(date, time, description, location, duration)

def edit_calendar_event(date: str, original_description: str, new_description: str, time: str = None, location: str = None, duration: int = None):
    """
    Edits an existing calendar event
    :param date: The date of the event in YYYY-MM-DD format
    :param original_description: The original description of the event in the calendar
    :param new_description: The new description to be applied to the event
    :param time: The new time of the event in HH:MM format or HH:MM-HH:MM format (optional)
    :param location: The new venue or location of the event, or 'None' if not specified (optional)
    :param duration: The new duration of the event in hours (optional)
    :return: The result of the event editing
    """
    logging.info(f"Attempting to edit event: date={date}, original_description={original_description}, new_description={new_description}")
    
    # Get events for the given date
    events = get_calendar_events(date)["existing_events"]
    
    if not events:
        logging.error(f"No events found for date: {date}")
        return {"is_success": False, "message": f"No events found for date: {date}"}

    # Find the event that matches the original description
    event_id = None
    original_event = None
    for event in events:
        if event['description'].lower() == original_description.lower():
            event_id = event['event_id']
            original_event = event
            break

    if event_id is None:
        logging.error(f"Event not found for date: {date}, original description: {original_description}")
        return {"is_success": False, "message": f"Event not found for date: {date}, original description: {original_description}"}
    
    logging.info(f"Found matching event: {original_event['description']}")

    # Call edit_google_calendar_event with the found event_id
    try:
        result = edit_google_calendar_event(
            event_id, 
            date=date, 
            time=time if time else original_event['time'], 
            description=new_description, 
            location=location, 
            duration=duration
        )
        
        if not result["is_success"]:
            logging.error(f"Failed to edit event: {result['message']}")
            return {"is_success": False, "message": f"Failed to edit event: {result['message']}"}
        
        logging.info(f"Successfully edited event: {new_description}")
        return {"is_success": True, "message": f"Successfully edited event: {new_description}"}

    except Exception as e:
        logging.error(f"Unexpected error in edit_calendar_event: {str(e)}")
        return {"is_success": False, "message": f"An unexpected error occurred: {str(e)}"}

def delete_calendar_event(date: str, time: str, description: str):
    """
    Deletes an existing calendar event
    :param date: The date of the event in YYYY-MM-DD format
    :param time: The time of the event in HH:MM format
    :param description: The description of the event
    :return: The result of the event deletion
    """ 
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

def get_google_calendar_events(target_date: str = None):
    """Fetches events from all of the user's Google Calendars for the specified date or current month."""
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
        
        if target_date:
            # If a specific date is provided, set the time range to that day
            start_of_day = datetime.datetime.strptime(target_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
            time_min = start_of_day.isoformat() + 'Z'
            time_max = end_of_day.isoformat() + 'Z'
        else:
            # Calculate the start and end of the current month
            today = datetime.datetime.now(pytz.UTC)
            start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = start_of_month + datetime.timedelta(days=32)
            end_of_month = next_month.replace(day=1) - datetime.timedelta(seconds=1)
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
        if description:
            event['summary'] = description
        
        if location:
            event['location'] = location

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
        elif duration:
            # If only duration is provided, update the end time
            start_datetime = datetime.datetime.fromisoformat(event['start']['dateTime'])
            end_datetime = start_datetime + datetime.timedelta(hours=duration)
            event['end']['dateTime'] = end_datetime.isoformat()

        logging.debug(f"Updated event (before API call): {event}")
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        logging.debug(f"Updated event (after API call): {updated_event}")
        
        return {
            "is_success": True,
            "message": f"Updated event '{updated_event['summary']}'"
        }

    except HttpError as error:
        logging.error(f"An error occurred: {error}")
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