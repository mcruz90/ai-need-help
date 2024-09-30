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

logger = logging.getLogger(__name__)

class GoogleCalendarAPI:
    def __init__(self):
        self.creds = self.get_credentials()
        self.service = build("calendar", "v3", credentials=self.creds)

    def get_credentials(self):
        """Handles the Google API credentials."""
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
        return creds

    @lru_cache(maxsize=100)
    def get_cached_google_calendar_events(self, target_date: str = None, cache_duration: int = 15) -> list:
        """
        Fetches and caches Google Calendar events.
        
        :param target_date: The date to fetch events for (optional)
        :param cache_duration: How long to cache the results in minutes
        :return: List of calendar events

        """
        cache_key = f"calendar_events_{target_date}"
        
        # Check if the events are already cached
        if hasattr(self, cache_key):
            return getattr(self, cache_key)[0]  # Return cached events

        # Fetch events from the Google Calendar API
        events = self.get_google_calendar_events(target_date)

        # Cache the events with the current timestamp
        setattr(self, cache_key, (events, datetime.datetime.now()))  # Set the attribute on the instance

        return events

    def get_google_calendar_events(self, target_date: str = None) -> list:
        """Fetches events from all of the user's Google Calendars for the specified date or current month.
        
        :param target_date: The date to fetch events for (optional)
        :return: List of calendar events
        """
        try:
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
            calendar = self.service.calendars().get(calendarId='primary').execute()
            user_timezone = calendar['timeZone']

            # Get list of all calendars
            calendar_list = self.service.calendarList().list().execute()

            events_list = []  # Initialize a list to hold event dictionaries
            for calendar in calendar_list['items']:
                calendar_id = calendar['id']
                events_result = (
                    self.service.events()
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
                        duration = 24 

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

            return events_list

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return []

    def create_google_calendar_event(self, date: str, time: str, description: str, location: str = None, duration: float = 1) -> dict:
        """
        Creates a new event on the user's Google Calendar.
        
        :param date: The date of the event in YYYY-MM-DD format
        :param time: The time of the event in HH:MM format
        :param description: The description of the event
        :param location: The location of the event (optional)
        :param duration: The duration of the event in hours as a float (default is 1.0)

        :return: A dictionary with the status and message of the operation
        """
        
        try:
            # Get the user's timezone
            calendar = self.service.calendars().get(calendarId='primary').execute()
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

            event = self.service.events().insert(calendarId='primary', body=event).execute()
            
            return {
                "is_success": True,
                "message": f"Created event '{description}' on {date} {'all day' if time == '00:00-23:59' or time.lower() == 'all day' else f'from {time}'}"
            }

        except HttpError as error:
            return {
                "is_success": False,
                "message": f"An error occurred: {error}"
            }

    def edit_google_calendar_event(self, event_id: str, date: str = None, time: str = None, description: str = None, location: str = None, duration: float = None) -> dict:
        """
        Edits an existing event on the user's Google Calendar.
        
        :param event_id: The ID of the event to edit
        :param date: The date of the event in YYYY-MM-DD format (optional)
        :param time: The time of the event in HH:MM-HH:MM format (optional)
        :param description: The description of the event (optional)
        :param location: The location of the event (optional)
        :param duration: The duration of the event in hours as a float (optional)

        :return: A dictionary with the status and message of the operation
        """
        try:
            # Get the existing event
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            logger.debug(f"Original event: {event}")
            
            # Get the user's timezone
            calendar = self.service.calendars().get(calendarId='primary').execute()
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

            logger.debug(f"Updated event (before API call): {event}")
            updated_event = self.service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
            logger.debug(f"Updated event (after API call): {updated_event}")
            
            return {
                "is_success": True,
                "message": f"Updated event '{updated_event['summary']}'"
            }

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return {
                "is_success": False,
                "message": f"An error occurred: {error}"
            }

    def delete_google_calendar_event(self, event_id: str) -> dict:
        """
        Deletes an event from the user's Google Calendar.
        
        :param event_id: The ID of the event to delete
        :return: A dictionary with the status and message of the operation
        """
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            
            return {
                "is_success": True,
                "message": f"Deleted event with ID: {event_id}"
            }

        except HttpError as error:
            return {
                "is_success": False,
                "message": f"An error occurred: {error}"
            }


if __name__ == "__main__":
    calendar_api = GoogleCalendarAPI()
    events = calendar_api.get_google_calendar_events()
    print(events) 