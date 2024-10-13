from agents.calendar.calendar_agent import calendar_agent
from agents.tutor.tutor_agent import tutor_agent
from agents.web_search.web_search_tools import web_search_agent
from agents.cohere_web_search.web_search_agent import cohere_web_search_agent

#TODO: Create designated agent for the code agent, rather than reuse web agent. Perhaps consider model that specializes in code.
AGENTS = {
    'calendar': {
        "tool": calendar_agent,
        "description": "Handles queries related to scheduling, managing appointments, and calendar reminders of the user's personal calendar. Do not use this agent for querying general events, or for any other purpose than scheduling and managing the user's appointments."
    },
    'tutor': {
        "tool": tutor_agent,
        "description": "Handles educational queries ONLY when the user explicitly requests tutoring assistance. Use this agent when the user asks for help with a specific topic, requests a lesson, or uses phrases very similar to 'can you teach me', 'can we review','explain step-by-step', or 'I need help understanding'. Do not use for general knowledge questions."
    },
    'general': {
        "tool": cohere_web_search_agent,
        "description": "Handles all queries seeking information, explanations, or answers, including complex topics and factual questions. Use this agent for any query that doesn't explicitly request tutoring or fall under other specialized agents."
    },
    'code': {
        "tool": web_search_agent,
        "description": "Handles coding and syntax formatting questions, providing examples, debugging. The code agent directly answers the user's question and does not need to any web searches. If the user is not asking as if they are a student, use this agent to answer their coding-related question."
    }
}
