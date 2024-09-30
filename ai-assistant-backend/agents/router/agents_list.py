from agents.calendar.calendar_agent import calendar_agent
from agents.tutor.tutor_agent import tutor_agent
from agents.web_search.web_search_tools import web_search_agent

#TODO: Create designated agent for the code agent, rather than reuse web agent. Perhaps consider model that specializes in code.
AGENTS = {
    'calendar': {
        "tool": calendar_agent,
        "description": "Handles queries related to scheduling, managing appointments, and event reminders of the user's google calendar"
    },
    'tutor': {
        "tool": tutor_agent,
        "description": "Handles educational queries requiring in-depth explanations, step-by-step problem-solving, or personalized learning assistance in specific subjects like math, science, literature, or history."
    },
    'general': {
        "tool": web_search_agent,
        "description": "Handles queries seeking factual information, current events, general knowledge, or topics not requiring in-depth educational explanation."
    },
    'code': {
        "tool": web_search_agent,
        "description": "Handles coding and syntax formatting questions, providing examples, debugging. The code agent directly answers the user's question and does not need to any web searches."
    }
}