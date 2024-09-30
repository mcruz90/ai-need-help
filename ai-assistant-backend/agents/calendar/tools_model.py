from agents.calendar.calendar_tools import get_calendar_events, create_calendar_event, edit_calendar_event, delete_calendar_event

functions_map = {
    "get_calendar_events": get_calendar_events,
    "create_calendar_event": create_calendar_event,
    "edit_calendar_event": edit_calendar_event,
    "delete_calendar_event": delete_calendar_event
}

# Tool definitions
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_daily_sales_report",
            "description": "Connects to a database to retrieve overall sales volumes and sales information for a given day.",
            "parameters": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "string",
                        "description": "Retrieves sales data for this day, formatted as YYYY-MM-DD.",
                    }
                },
                "required": ["day"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_product_catalog",
            "description": "Connects to a product catalog with information about all the products being sold, including categories, prices, and stock levels.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Retrieves product information data for all products in this category.",
                    }
                },
                "required": ["category"],
            },
        },
    },
]




tools = [
    {
        "type": "function",
        "function": {
            "name": 'get_calendar_events',
            "description": 'Returns a range of events from the user calendar, using the end date of the date range as determined from the user query.',
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": 'string',
                        "description": 'Date of the event in YYYY-MM-DD format. If not provided, use the last day in the date range from the user query.',
                        
                    }
                },
                "required": ["date"]   
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'create_calendar_event',
            "description": 'Creates a new calendar event of the specified duration at the specified time and date. A new event cannot be created on the same time as an existing event.',
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": 'string',
                        "description": 'Date of the event in YYYY-MM-DD format.',
                    },
                    "time": {
                        "type": 'string',
                        "description": 'Time of the event in HH:MM format, or a start and end time range. The default value is 9am-5pm.',
                    },
                    "description": {
                        "type": 'string',
                        "description": 'Brief description of the event.',
                    },
                    "location": {
                        "type": 'string',
                        "description": 'Venue or location of the event. The default value is: "TBD"',
                    },
                    "duration": {
                        "type": 'string',
                        "description": 'Duration of the event in hours. The default value is: 1 hour',
                    },
                },
                "required": ["date", "time", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'edit_calendar_event',
            "description": 'Edits an existing calendar event',
            "parameters": { 
                "type": "object",
                "properties": {
                    "date": {
                        "type": 'string',
                        "description": 'The date of the event in YYYY-MM-DD format.',
                    },
                    "original_description": {
                        "type": 'string',
                        "description": 'The original description of the event in the calendar.',
                    },
                    "new_description": {
                        "type": 'string',
                        "description": 'The new description to be applied to the event.',
                    },
                    "time": {
                        "type": 'string',
                        "description": 'The new time of the event in HH:MM format or HH:MM-HH:MM format. If not provided, the default value is: 9:00am-5:00pm',
                    },
                    "location": {
                        "type": 'string',
                        "description": 'The new venue or location of the event. The default value is: "TBD"',
                    },
                    "duration": {
                        "type": 'string',
                        "description": 'The new duration of the event in hours. The default value in is: 1 hour',
                    }
                },
                "required": ["date", "original_description", "new_description"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": 'delete_calendar_event',
            "description": 'Deletes an existing calendar event. The event is identified by its date, time, and description.',
            "parameters": {
                "type": "object",   
                "properties": {
                    "date": {
                        "type": 'string',
                        "description": 'Date of the event in YYYY-MM-DD format.',
                    },
                    "time": {
                        "type": 'string',
                        "description": 'Time of the event in HH:MM format.',
                    },
                    "description": {
                        "type": 'string',
                        "description": 'Brief description of the event.',
                    }
                },
                "required": ["date", "time", "description"]
            }
        }
    }
]