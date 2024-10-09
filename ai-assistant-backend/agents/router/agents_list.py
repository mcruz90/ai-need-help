from agents.calendar.calendar_agent import calendar_agent
from agents.tutor.tutor_agent import tutor_agent
from agents.web_search.web_search_tools import web_search_agent
from agents.cohere_web_search.web_search_agent import cohere_web_search_agent

#TODO: Create designated agent for the code agent, rather than reuse web agent. Perhaps consider model that specializes in code.
AGENTS = {
    'calendar': {
        "tool": calendar_agent,
        "description": "Handles queries related to scheduling, managing appointments, and calendar reminders of the user's personal calendar. Do not use this agent for querying general events, or for any other purpose than scheduling and managing the  user's appointments."
    },
    'tutor': {
        "tool": tutor_agent,
        "description": "Handles educational queries requiring a formal lesson through step-by-step problem-solving, or personalized learning assistance in specific subjects like math, science, literature, or history."
    },
    'general': {
        "tool": cohere_web_search_agent,
        "description": "Handles queries seeking factual information, current events, general knowledge, or topics that may require an in-depth, informative explanation, but does not require a personalized formal lesson to learn about the topic."
    },
    'code': {
        "tool": web_search_agent,
        "description": "Handles coding and syntax formatting questions, providing examples, debugging. The code agent directly answers the user's question and does not need to any web searches. If the user is not asking as if they are a student, use this agent to answer their coding-related question."
    }
}