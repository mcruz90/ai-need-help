from agents.calendar.google_calendar_api import GoogleCalendarAPI
import logging
import datetime

calendar_api = GoogleCalendarAPI()


def parse_time(time_str: str) -> datetime.time:
    """
    Parse time from string time_str. First tries to parse 24-hour format, then 12-hour format.
    Returns a datetime.time object.
    
    :param time_str: The time string to parse
    :return: A datetime.time object
    """

    try:
        return datetime.datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return datetime.datetime.strptime(time_str, "%I%p").time()

def get_calendar_events(date: str = None) -> dict:
    """
    Fetches google calendar events from cached google calendar events.
    Returns a dictionary of events for the given date or current month.

    :param date: The date to fetch events for (optional)
    :return: Dictionary containing the existing events

    """
    events = calendar_api.get_google_calendar_events(date)
    return {
        "existing_events": events
    }

def create_calendar_event(date: str, time: str, description: str, location: str = None, duration: int = 1) -> dict:
    """
    Creates a new calendar event.

    :param date: The date of the event in YYYY-MM-DD format
    :param time: The time of the event in HH:MM format, or a start and end time range, or 9am-5pm if not specified
    :param description: The description of the event
    :param location: The location of the event (optional)
    :param duration: The duration of the event in hours (optional)
    :return: The result of the event creation
    """

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

    return calendar_api.create_google_calendar_event(date, time, description, location, duration)

def edit_calendar_event(date: str, original_description: str, new_description: str, time: str = None, location: str = None, duration: int = None) -> dict:
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
        result = calendar_api.edit_google_calendar_event(
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

def delete_calendar_event(date: str, time: str, description: str) -> dict:
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
    return calendar_api.delete_google_calendar_event(event_id)