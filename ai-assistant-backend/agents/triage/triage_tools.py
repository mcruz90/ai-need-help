
from agents.calendar.calendar_agent import calendar_agent
from agents.tutor.tutor_agent import tutor_agent
from agents.code.code_agent import code_agent
from agents.cohere_search.web_search_agent import cohere_web_search_agent as search_agent

functions_map = {
    "calendar_agent": calendar_agent,
    "tutor_agent": tutor_agent,
    "search_agent": search_agent,
    "code_agent": code_agent,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "calendar_agent",
            "description": "Handles queries related to managing the user's appointments and retrieving personal event details on their calendar. Do not use this agent for querying general events such as a concert, sports event, holiday, or for any other purpose than managing the user's personal schedule.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's calendar-related query to the agent.",
                    },
                    "chat_history": {
                        "type": "list",
                        "description": "The chat history",
                    }
                },
                "required": ["query", "chat_history"],
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
                    }
                },
                "required": ["user_message", "chat_history"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_agent",
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
            "description": "Handles queries related to code generation and code critique, including debugging, and creating coding documentation. Use this agent for any query that requires assistance with programming or technical documentation. Do not use this agent for information-seeking questions about coding, programming or software development, which should be handled by the web_search_agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_message": {
                        "type": "string",
                        "description": "The user's code-relatedquery to the agent.",
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

