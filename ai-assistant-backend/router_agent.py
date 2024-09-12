from config import cohere_client
from web_search_tools import agent_executor as web_search_agent
from calendar_agent import calendar_agent

model = 'command-r-plus-08-2024'

preamble="""
        You are an expert router agent that determines which agent can best response to a given query.
        There are two agents: calendar_agent and web_search_agent.
        calendar_agent is an agent that can handle queries related to calendars. You MUST use this agent when the user query is related to calendars.
        web_search_agent is an agent that can handle queries related to general information, do not use this agent unless the user query is related to general information.
        
        Determine if the user query is related to calendars or general information.
        
        After receiving the response, it is very important that you only respond with 'calendar' or 'general', as these are the only valid responses that the agents can understand.

        Do not refuse questions that are not related to calendars, as the web_search_agent can also answer those questions.
        """

def router_agent(user_input, chat_history, relevant_context) -> dict:
    """
    Route the user message to the appropriate agent and get the response as a dictionary with keys 'role' and 'message'.

    param user_input: the user's input
    param chat_history: the chat history
    param relevant_context: the relevant context
    
    return: the response from the appropriate agent as a dictionary with keys 'role' and 'message'
    """

    updated_preamble = preamble + relevant_context

    # Determine which agent to use
    response = cohere_client.chat(
        message=user_input,
        model=model,
        chat_history=chat_history,
        preamble=updated_preamble
    )
    
    agent_type = response.text.strip().lower()
    print(f"Agent type: {agent_type}")
    
    if agent_type == 'calendar':
        return handle_calendar_query(user_input, chat_history, updated_preamble)
    elif agent_type == 'general':
        return handle_general_query(user_input, chat_history)
    else:
        raise ValueError(f"Invalid agent type: {agent_type}")


def handle_calendar_query(user_input, chat_history, updated_preamble) -> dict:
    """
    Calls the calendar agent to handle the received calendar query

    param user_input: the user's input
    param chat_history: the chat history
    param updated_preamble: the updated preamble
    
    return: the response from the calendar agent as a dictionary with keys 'role' and 'message'
    """
    print(f"Performing calendar actions for input message: {user_input}")

    result = calendar_agent(user_input, chat_history, updated_preamble)
    response = {"role": "Chatbot", "message": result.text}

    return response

def handle_general_query(user_input, chat_history) -> dict:
    """
    Handle the general query

    param user_input: the user's input
    param chat_history: the chat history
    
    return: the response from the web search agent as a dictionary with keys 'role' and 'message'
    """
    print(f"Performing web search actions for input message: {user_input}")

    result = web_search_agent.invoke({"input": user_input, "preamble": chat_history})
    response = {"role": "Chatbot", "message": result["output"]}
    return response


