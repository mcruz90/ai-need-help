from config import cohere_client, cohere_model as model
from web_search_tools import web_search_agent
from calendar_agent import calendar_agent
from tutor_agent import tutor_agent
from utils import enhance_output_with_citations, code_block_formatter, extract_key_info

import re
import logging

logger = logging.getLogger(__name__)

AGENTS = {
    'calendar': {
        "tool": calendar_agent,
        "description": "Handles queries related to scheduling, managing appointments, and event reminders."
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
        "description": "Handles coding questions, providing code examples, debugging. The code agent directly answers the user's question and does not need to any web searches."
    }
}

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
    - Only use the agent names listed above. These are the only valid responses.
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

preamble = generate_preamble(AGENTS)



def extract_context_info(formatted_history, user_input):
    system_messages = [msg['message'] for msg in formatted_history if msg['role'] == 'System']
    summary = next((msg for msg in system_messages if msg.startswith("Conversation summary:")), None)
    
    key_info = extract_key_info(user_input)  # This uses your existing extract_key_info function
    
    context = []
    if summary:
        context.append(f"Conversation summary: {summary.split(':', 1)[1].strip()}")
    if key_info:
        context.append(f"Key information: {key_info}")
    
    return " | ".join(context) if context else None

def parse_agent_response(response: str):
    agent_match = re.match(r'^(\w+)(?:\s*:\s*(.*))?$', response.strip(), re.IGNORECASE)
    if not agent_match:
        return 'general', 0.5  # Default to general with low confidence if no match

    agent_type = agent_match.group(1).lower()
    reasoning = agent_match.group(2) if agent_match.group(2) else ""

    if not reasoning:
        confidence = 0.6
    else:
        confidence = min(0.6 + (len(reasoning) / 100), 0.9)
        if re.search(r'\b(certain|sure|confident|definitely)\b', reasoning, re.IGNORECASE):
            confidence = min(confidence + 0.1, 0.95)
        if re.search(r'\b(unsure|maybe|possibly|not certain)\b', reasoning, re.IGNORECASE):
            confidence = max(confidence - 0.1, 0.4)

    return agent_type, confidence

def router_agent(user_input: str, chat_history: list, previous_agent_type: str = None, key_info: str = None) -> dict:
    logger.info(f"Router agent called with input: {user_input}")
    
    formatted_history = [
        {"role": msg['role'], "message": msg['message'] if 'message' in msg else msg['content']}
        for msg in chat_history[-5:]  # Only consider the last 5 messages for context
    ]

    context_info = extract_context_info(formatted_history, user_input)
    
    # Include key_info in the context if it's provided
    if key_info:
        context_info = f"{context_info} | Key information: {key_info}" if context_info else f"Key information: {key_info}"
    
    updated_preamble = generate_preamble(AGENTS) + f"""
    Previous agent: {previous_agent_type if previous_agent_type else 'None'}
    Context: {context_info if context_info else 'No additional context'}

    Important: Consider the current query independently from previous interactions.
    The previous agent type is provided for context, but it should not heavily influence your decision for the current query.

    Analyze the following query and determine the most suitable agent:
    "{user_input}"

    Respond with the agent name followed by a colon and your reasoning.
    For example: "calendar: This query is about scheduling an appointment."
    """

    agent_type_response = cohere_client.chat(
        message="Route this query to the most appropriate agent",
        model=model,
        chat_history=formatted_history,
        preamble=updated_preamble
    )
    
    agent_type, confidence = parse_agent_response(agent_type_response.text)

    logger.info(f"Raw agent type response: {agent_type_response.text}")
    logger.info(f"Parsed agent type: {agent_type}, Confidence: {confidence}")
    
    if agent_type in AGENTS.keys():
        selected_agent = agent_type
    else:
        matching_agents = [agent for agent in AGENTS.keys() if agent in agent_type]
        selected_agent = matching_agents[0] if matching_agents else 'general'
        confidence = max(confidence - 0.1, 0.3) if selected_agent == 'general' else confidence

    confidence_threshold = 0.7  # You can adjust this threshold

    if selected_agent and confidence >= confidence_threshold:
        logger.debug(f"Selected agent: {selected_agent}, Confidence: {confidence}")
        
        return handle_query(user_input, chat_history, selected_agent, context_info, confidence)
    else:
        logger.debug(f"Unclear agent type, confidence: {confidence}")
        
        return handle_unclear_agent_type(user_input, chat_history, confidence)



def handle_query(user_input, chat_history, agent_type, context_info=None, confidence=None):
    try:
        logger.debug(f"Handling query with {agent_type} agent")
        print(f"Handling query with {agent_type} agent")
        formatted_history = []
        for msg in chat_history:
            if isinstance(msg, dict):
                formatted_msg = {
                    'role': msg.get('role', ''),
                    'message': msg.get('message', msg.get('content', ''))
                }
            else:
                formatted_msg = {
                    'role': getattr(msg, 'role', ''),
                    'message': getattr(msg, 'message', getattr(msg, 'content', ''))
                }
            formatted_history.append(formatted_msg)

        if agent_type == 'calendar':
            # Handle calendar agent separately
            result = AGENTS[agent_type]["tool"](user_input, formatted_history)
            return {"role": "Chatbot", "message": result["response"]}
        elif agent_type == 'general':
            # Handle general agent with additional context
            result = AGENTS[agent_type]["tool"].invoke({
                "input": user_input, 
                "chat_history": formatted_history,
                "router_context": context_info,
                "router_confidence": confidence
            })
        else:
            # Handle other agents as before
            result = AGENTS[agent_type]["tool"].invoke({"input": user_input, "chat_history": formatted_history})
        
            logger.debug(f"Raw result from {agent_type} agent: {result}")

        if isinstance(result, dict):
            if "output" in result:
                output = result["output"]
            elif "response" in result:
                output = result["response"]
            else:
                output = str(result)
            
            if "citations" in result and len(result["citations"]) > 0:
                enhanced_output = enhance_output_with_citations(output, result["citations"])
            else:
                print(f"no citations in output: {output}")
                enhanced_output = code_block_formatter(output)
            return {"role": "Chatbot", "message": enhanced_output}
        else:
            return {"role": "Chatbot", "message": str(result)}
    except Exception as e:
        logger.error(f"Error in handle_query: {str(e)}", exc_info=True)
        return {"role": "Chatbot", "message": f"An error occurred while processing your query: {str(e)}"}

def handle_unclear_agent_type(user_input, chat_history, confidence):
    clarification_prompt = f"I'm not entirely sure which agent should handle this query (confidence: {confidence:.2f}): '{user_input}'. Could you please provide more context or clarify your question?"
    
    formatted_history = [{
        'role': msg['role'],
        'message': msg['content'] if 'content' in msg else msg['message']
    } for msg in chat_history]
    
    clarification_response = cohere_client.chat(
        message=clarification_prompt,
        model=model,
        chat_history=formatted_history
    )
    
    return {"role": "Chatbot", "message": clarification_response.text}


