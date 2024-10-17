
from agents.calendar.calendar_agent import calendar_agent
from agents.tutor.tutor_agent import tutor_agent
from agents.code.code_agent import code_agent
from agents.cohere_search.web_search_agent import cohere_web_search_agent as web_search_agent

functions_map = {
    "calendar_agent": calendar_agent,
    "tutor_agent": tutor_agent,
    "web_search_agent": web_search_agent,
    "code_agent": code_agent,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "calendar_agent",
            "description": "Handles queries related to scheduling, managing appointments, and calendar reminders of the user's personal calendar. Do not use this agent for querying general events, or for any other purpose than scheduling and managing the user's appointments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "The user's calendar-related query to the agent.",
                    },
                    "formatted_history": {
                        "type": "list",
                        "description": "The formatted chat history",
                    }
                },
                "required": ["user_message", "formatted_history"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tutor_agent",
            "description": "Handles educational queries ONLY when the user explicitly requests tutoring assistance. Use this agent when the user asks for help with a specific topic, requests a lesson, or uses phrases very similar to 'can you teach me', 'can we review','explain step-by-step', or 'I need help understanding'. Do not use for general knowledge questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "The user's educational query to the agent.",
                    },
                    "chat_history": {
                        "type": "list",
                        "description": "The chat history",
                    },
                    "context_info": {
                        "type": "string",
                        "description": "Any additional context information to be provided to the agent.",
                    }
                },
                "required": ["user_message", "chat_history", "context_info"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search_agent",
            "description": "Handles all queries seeking information, explanations, or answers, including complex topics and factual questions. Use this agent for any query that doesn't explicitly request tutoring or fall under other specialized agents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "string",
                        "description": "The user's query to the agent.",
                    },
                    "chat_history": {
                        "type": "list",
                        "description": "The chat history",
                    },
                },
                "required": ["queries", "chat_history"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "code_agent",
            "description": "Handles all queries related to code, including debugging, coding, and documentation. Use this agent for any query that requires assistance with programming, software development, or technical documentation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "The user's query to the agent.",
                    },
                    "chat_history": {
                        "type": "list",
                        "description": "The provided chat history from the user",
                    },
                },
                "required": ["user_message", "chat_history"],
            },
        },
    },
]

