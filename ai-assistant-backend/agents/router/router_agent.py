from llm_models.chat import chat_model
from agents.router.agents_list import AGENTS
from agents.router.helper_functions import extract_key_info, parse_agent_response, enhance_output_with_citations, format_chat_history, output_with_citations

import asyncio
from httpx import AsyncClient, TimeoutException
from typing import TypedDict, Literal

import logging

logger = logging.getLogger(__name__)

class HandlerResponse(TypedDict):
    role: Literal["assistant"]
    content: str
    agent_type: str

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


async def router_agent(user_input: str, chat_history: list, previous_agent_type: str = None) -> HandlerResponse:
    """
    Router agent called in the chat route that determines which specialized agent can best respond to a given user query.
    Send the router agent the user input, chat history, and the previous agent type as a dict to handle_query for processing.

    :param user_input: The user's input.
    :param chat_history: The chat history.
    :param previous_agent_type: The previous agent type. Default is None if no previous agent type is provided (i.e. first message).
    
    returns the result from handle_query
    handle query returns a dictionary with the following keys:
    - "role": "assistant"
    - "content": the response from the agent
    - "agent_type": the type of agent that responded
    """
    try:
        logger.info(f"Router agent called with input: {user_input}")
        logger.info(f"Previous agent type: {previous_agent_type}")

        # Ensure all roles are lowercase and use 'content' instead of 'message'
        formatted_history = format_chat_history(chat_history)

        context_info = extract_key_info(user_input)

        logger.info(f"Context info: {context_info}")

        updated_preamble = generate_preamble(AGENTS) + f"""
        
        Previous agent: {previous_agent_type if previous_agent_type else 'None'}
        Context: {context_info if context_info else 'No additional context'}

        Given details about the previous agent and context, analyze the following query and determine the most suitable agent:
        "{user_input}"

        Your response should consider the following information:
        1. State the agent name followed by a colon and your reasoning. For example: "First agent choice: calendar: The user is asking for help with their schedule, so I should choose the calendar agent."
        2. Reflect on the reasoning you used to determine the most suitable agent and consider the following:
            a. Was your reasoning appropriate for the query?
            b. Did you consider the context and previous agent used?
            c. Did you consider how well the other available agents could respond to the query?
            d. Did you choose the most appropriate agent based on the query and context?

        3. If you are confident in your initial choice, then you can choose the same agent and respond in the same format: For example: "Final agent choice is unchanged: calendar: The query is uniquely related to the user's personal calendar and not to an external or publically available event. The other agents do not have access to the user's calendar and would not be able to perform the requested calendar-based tasks."
        4. If, however, your reflection suggests that you should choose a different agent, then you can choose a different agent
        and respond in the same format as the example above.
        
        Your final response should be formatted as: "[FINAL AGENT]: Detailed explanation incorporating reflection on the query and reasoning for choosing the agent."
        
        For example, if you changed your mind during your reflection:
        "general: My first assumption was to choose the calendar agent, because the user is asking for help with their schedule. However, upon reflection, this query is actually about seeking general information about a TV event that requires searching external sources, which the general agent is equipped to do, and is therefore not related to the user's calendar, so my final choice is 'general'."
        
        Another example, if you did not change your mind during your reflection:
        "calendar: My first assumption was to choose the calendar agent, because the user is asking for help with their schedule. Upon further reflection, my agent choice is unchanged, and I would still choose the calendar agent, as the query is uniquely related to events that is most likely to be on a user's personal calendar and not to an external or publically available event, such as a summer event or TV event. Furthermore, the other agents do not have access to the user's calendar and would not be able to perform the requested calendar-based tasks."
        """

        # Combine preamble and formatted history into a single messages list as required by Cohere Chat v2 endpoint
        messages = [
            {"role": "system", "content": updated_preamble},
            *formatted_history,
            {"role": "user", "content": user_input}
        ]

        agent_type_response = chat_model.generate_short_response(messages)

        logger.info(f"Agent type raw response: {agent_type_response.message.content[0].text}")

        agent_type, confidence = parse_agent_response(agent_type_response.message.content[0].text)

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
            
            handler_response = await handle_query(user_input, chat_history, selected_agent, context_info, confidence)

        else:
            logger.debug(f"Unclear agent type, confidence: {confidence}")
            handler_response = await handle_unclear_agent_type(user_input, chat_history, confidence)
        
        return{
            "role": "assistant",
            "content": handler_response["content"],
            "agent_type": handler_response["agent_type"]
        }
        
    except TimeoutException:
        logger.error("Timeout occurred while calling the Cohere API")
        return {"role": "assistant", "content": "I'm sorry, but I'm having trouble processing your request right now. Could you please try again in a moment?", "agent_type": "router"}
    except Exception as e:
        logger.error(f"An error occurred in router_agent: {str(e)}")
        return {"role": "assistant", "content": "I apologize, but an error occurred while processing your request. Please try again later.", "agent_type": "router"}


# TODO: Possible duplicated function
async def handle_query(user_input: str, formatted_history: list, agent_type: str, context_info: str = None, confidence: float = None):
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

        return await handle_agent_response(agent_type, user_input, formatted_history, context_info, confidence)
    
    except Exception as e:
        logger.error(f"Error in handle_query: {str(e)}", exc_info=True)
        return {"role": "assistant", "content": f"An error occurred while processing your query: {str(e)}", "agent_type": "error"}


async def handle_agent_response(agent_type: str, user_input: str, formatted_history: list, context_info: str, confidence: float) -> dict:
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
        enhanced_output = enhance_output_with_citations(result["response"], result["citations"])
        return {"role": "assistant", "content": enhanced_output, "agent_type": agent_type}
    elif agent_type == 'general':
        result = AGENTS[agent_type]["tool"](user_input, formatted_history)
        logger.info(f"result keys: {result.keys()}")
        logger.info(f"citations: {result.get('citations')}")  # Log the citations for debugging
        
        # Check if citations exist and are not None or empty
        if result.get("citations") and isinstance(result["citations"], list):
            cited_output = output_with_citations(result["response"], result["citations"])
        else:
            # If no citations or citations is None, just use the response as is
            cited_output = result["response"]

        logger.info(f"cited_output: {cited_output}")  # Log the final output for debugging

        return {"role": "assistant", "content": cited_output, "agent_type": agent_type}
    else:
        # Check if the tool is a coroutine function (async)
        if asyncio.iscoroutinefunction(AGENTS[agent_type]["tool"].invoke):
            result = await AGENTS[agent_type]["tool"].invoke({
                "input": user_input, 
                "chat_history": formatted_history,
                "router_context": context_info,
                "router_confidence": confidence
            })
        else:
            # If it's not async, call it synchronously
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
async def handle_unclear_agent_type(user_input: str, chat_history: list, confidence: float) -> dict:
    clarification_prompt = f"I'm not entirely sure which agent should handle this query (confidence: {confidence:.2f}): '{user_input}'. Could you please provide more context or clarify your question?"
    
    formatted_history = format_chat_history(chat_history)
    
    messages = [
        {"role": "assistant", "content": clarification_prompt},
        *formatted_history,
    ]

    clarification_response = chat_model.generate_response(messages)
    
    return {"role": "assistant", "content": clarification_response.message.content[0].text}
