from llm_models.chat import chat_model
from agents.router.agents_list import AGENTS
from agents.router.helper_functions import extract_context_info, extract_key_info, parse_agent_response, enhance_output_with_citations, format_chat_history

import logging

logger = logging.getLogger(__name__)

def generate_preamble(agents: dict) -> str:
    agent_descriptions = "\n".join([f"- {agent}: {info['description']}" for agent, info in agents.items()])
    return f"""
    You are an expert router agent that determines which specialized agent can best respond to a given user query.
    Your role is crucial in ensuring that user queries are directed to the most appropriate agent for accurate and helpful responses.

    Available agents:
    {agent_descriptions}

    Instructions:
    1. Carefully analyze the user's query and any provided context.
    2. Determine the most suitable agent based on the query's content and the agents' specializations.
    3. Provide your response in the following format:
       AGENT_NAME: Brief explanation of why you chose this agent.

    Important guidelines:
    - Only use the agent names listed above. Do not use alternative names for the agent.
    - If a query doesn't clearly fit a specific agent, route it to the 'general' agent.
    - For the tutor agent:
      * Consider the user's learning context and previous interactions.
      * If a tutoring session is ongoing (no explicit closure), continue routing to the tutor agent.
    - For coding questions:
      * Route to the 'code' agent unless the user specifically asks for help in learning to code.
      * If it's about learning to code, route to the 'tutor' agent.
    - Provide a concise but informative explanation for your choice to help with confidence assessment.

    Remember, your role is to route, not to answer the query directly. Focus on selecting the most appropriate agent based on the query's nature and context.
    """


def router_agent(user_input: str, chat_history: list, previous_agent_type: str = None) -> dict:
    """
    Router agent called in the chat route that determines which specialized agent can best respond to a given user query.
    Send the router agent the user input, chat history, and the previous agent type as a dict to handle_query for processing.

    :param user_input: The user's input.
    :param chat_history: The chat history.
    :param previous_agent_type: The previous agent type. Default is None if no previous agent type is provided (i.e. first message).
    """
    logger.info(f"Router agent called with input: {user_input}")
    logger.info(f"Previous agent type: {previous_agent_type}")

    
    # Ensure all roles are lowercase and use 'content' instead of 'message'
    formatted_history = format_chat_history(chat_history)

    logger.info(f"formatted_history: {formatted_history}")

    context_info = extract_context_info(formatted_history, user_input)
    key_info = extract_key_info(user_input)

    # Include key_info in the context if it's provided
    if key_info:
        context_info = f"{context_info} | Key information: {key_info}" if context_info else f"Key information: {key_info}"
    
    logger.info(f"Context info: {context_info}")

    updated_preamble = generate_preamble(AGENTS) + f"""
    Previous agent: {previous_agent_type if previous_agent_type else 'None'}
    Context: {context_info if context_info else 'No additional context'}

    Analyze the following query and determine the most suitable agent:
    "{user_input}"

    Extract some keywords from the user input and use them to inform your decision.

    Respond with the agent name followed by a colon and your reasoning.
    For example: "calendar: This query is about scheduling an appointment."
    """

    # Combine preamble and formatted history into a single messages list as required by Cohere Chat v2 endpoint
    messages = [
        {"role": "system", "content": updated_preamble},
        *formatted_history,
        {"role": "user", "content": user_input}
    ]

    agent_type_response = chat_model.generate_response(messages)

    agent_type, confidence = parse_agent_response(agent_type_response.message.content[0].text)

    logger.info(f"Raw agent type response: {agent_type_response.message.content[0].text}")
    logger.info(f"Parsed agent type: {agent_type}, Confidence: {confidence}")
    
    if agent_type in AGENTS.keys():
        selected_agent = agent_type
    else:
        matching_agents = [agent for agent in AGENTS.keys() if agent in agent_type]
        selected_agent = matching_agents[0] if matching_agents else 'general'
        confidence = max(confidence - 0.1, 0.3) if selected_agent == 'general' else confidence

    confidence_threshold = 0.7  

    if selected_agent and confidence >= confidence_threshold:
        logger.debug(f"Selected agent: {selected_agent}, Confidence: {confidence}")
        
        return handle_query(user_input, chat_history, selected_agent, context_info, confidence)
    else:
        logger.debug(f"Unclear agent type, confidence: {confidence}")
        
        return handle_unclear_agent_type(user_input, chat_history, confidence)


# TODO: Possible duplicated function
def handle_query(user_input: str, formatted_history: list, agent_type: str, context_info: str = None, confidence: float = None):
    """
    Called by router agent to handle the query.

    :param user_input: The user's input.
    :param formatted_history: The formatted chat history.
    :param agent_type: The type of agent to handle the query.
    :param context_info: The context information.
    :param confidence: The confidence of the agent type.
    """

    try:
        logger.info(f"Handling query with {agent_type} agent")
        formatted_history = []

        return handle_agent_response(agent_type, user_input, formatted_history, context_info, confidence)
    
    except Exception as e:
        logger.error(f"Error in handle_query: {str(e)}", exc_info=True)
        return {"role": "assistant", "content": f"An error occurred while processing your query: {str(e)}", "agent_type": "error"}


def handle_agent_response(agent_type: str, user_input: str, formatted_history: list, context_info: str, confidence: float) -> dict:
    """
    Receives the agent type, user input, formatted history, context info, and confidence.
    Calls the appropriate agent tool with the user input and formatted history.
    Returns the agent's response as a dictionary back to the router agent to be returned to the client.

    :param agent_type: The type of agent to handle the query.
    :param user_input: The user's input.
    :param formatted_history: The formatted chat history.
    :param context_info: The context information.
    :param confidence: The confidence of the agent type.
    """
    if agent_type == 'calendar':
        result = AGENTS[agent_type]["tool"](user_input, formatted_history)
        enhanced_output = enhance_output_with_citations(result["response"], result.get("citations", []))
        return {"role": "assistant", "content": enhanced_output, "agent_type": agent_type}
    else:
        result = AGENTS[agent_type]["tool"].invoke({
            "input": user_input, 
            "chat_history": formatted_history,
            "router_context": context_info,
            "router_confidence": confidence
        })

    if isinstance(result, dict):
        output = result.get("output") or result.get("response") or str(result)
        enhanced_output = enhance_output_with_citations(output, result.get("citations", []))
        return {"role": "assistant", "content": enhanced_output, "agent_type": agent_type}
    else:
        return {"role": "assistant", "content": str(result), "agent_type": agent_type}


#TODO: Need more robust testing of this function
def handle_unclear_agent_type(user_input: str, chat_history: list, confidence: float) -> dict:
    clarification_prompt = f"I'm not entirely sure which agent should handle this query (confidence: {confidence:.2f}): '{user_input}'. Could you please provide more context or clarify your question?"
    
    formatted_history = format_chat_history(chat_history)
    
    messages = [
        {"role": "assistant", "content": clarification_prompt},
        *formatted_history,
    ]

    clarification_response = chat_model.generate_response(messages)
    
    return {"role": "assistant", "content": clarification_response.message.content[0].text}
