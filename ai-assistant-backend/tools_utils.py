from calendar_tools import get_calendar_events, create_calendar_event, edit_calendar_event, delete_calendar_event

tools = [
   {
       "name": "get_calendar_events",
       "description": "Gets the user's events for the current month, or for a specific date if provided. Includes date, time, location, and description.",
       "parameter_definitions": {
            "date": {
                "description": "Date of the event in YYYY-MM-DD format. If not provided, returns events for the current month.",
                "type": "str",
                "required": False
            },
        }
   }, 
    {
      "name": "create_calendar_event",
      "description": "Creates a new calendar event of the specified duration at the specified time and date. A new event cannot be created on the same time as an existing event.",
      "parameter_definitions": {
            "date": {
                "description": "Date of the event in YYYY-MM-DD format",
                "type": "str",
                "required": True
            },
            "time": {
                "description": "Time of the event in HH:MM format, or a start and end time range, or 9am-5pm if not specified",
                "type": "str",
                "required": True
            },
            "description": {
                "description": "Brief description of the event",
                "type": "str",
                "required": True
            },
            "location": {
                "description": "Venue or location of the event, or 'None' if not specified",
                "type": "str",
                "required": False
            },
            "duration": {
                "description": "Duration of the event in hours, or 1 if not specified",
                "type": "int",
                "required": False
            }
      }
    },
    {
      "name": "edit_calendar_event",
      "description": "Edits an existing calendar event",
      "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "The date of the event in YYYY-MM-DD format"},
                "original_description": {"type": "string", "description": "The original description of the event in the calendar"},
                "new_description": {"type": "string", "description": "The new description to be applied to the event"},
                "time": {"type": "string", "description": "The new time of the event in HH:MM format or HH:MM-HH:MM format (optional)"},
                "location": {"type": "string", "description": "The new venue or location of the event (optional)"},
                "duration": {"type": "integer", "description": "The new duration of the event in hours (optional)"}
            },
            "required": ["date", "original_description", "new_description"]
        }
    },
    {
      "name": "delete_calendar_event",
      "description": "Deletes an existing calendar event. The event is identified by its date, time, and description.",
      "parameter_definitions": {
            "date": {
                "description": "Date of the event in YYYY-MM-DD format",
                "type": "str",
                "required": True
            },
            "time": {
                "description": "Time of the event in HH:MM format",
                "type": "str",
                "required": True
            },
            "description": {
                "description": "Brief description of the event",
                "type": "str",
                "required": True
            }
      }
    }
]

functions_map = {
    "get_calendar_events": get_calendar_events,
    "create_calendar_event": create_calendar_event,
    "edit_calendar_event": edit_calendar_event,
    "delete_calendar_event": delete_calendar_event
}
