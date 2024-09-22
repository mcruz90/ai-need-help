from config import cohere_client, cohere_model as model
from web_search_tools import web_search_agent
from calendar_agent import calendar_agent
from tutor_agent import tutor_agent
from utils import enhance_output_with_citations, code_block_formatter


# Define a dictionary of available agents
AGENTS = {
    'calendar': {
        "tool": calendar_agent,
        "description": "Handles queries related to calendars."
    },
    'tutor': {
        "tool": tutor_agent,
        "description": "Handles queries related to tutoring."
    },
    'general': {
        "tool": web_search_agent,
        "description": "Handles queries related to general information using web search. "
    }
}

def generate_preamble(agents: dict) -> str:
    agent_descriptions = "\n".join([f"- {agent}: {info['description']}" for agent, info in agents.items()])
    return f"""
    You are an expert router agent that determines which agent can best respond to a given query.
    The available agents are:

    {agent_descriptions}

    Determine which agent is most suitable for the user query.
    After receiving the response, it is very important that you only respond with one of the following agent names: {', '.join(agents.keys())}.
    These are the only valid responses that the agents can understand.

    Do not refuse questions that don't seem to fit any specific agent, as the general agent can handle a wide range of queries.

    When routing to the tutor agent, the preamble is very important as it helps the tutor understand the user's context. The user may also be answering questions
    from the tutor, so if the agent hasn't explicitly closed the tutoring session, the user may still be receiving help, so you must continue to route to the tutor agent.

    Coding questions should be routed to the general agent unless the user specifies that they need help with learning to code. In that case, route to the tutor agent.
    """

preamble = generate_preamble(AGENTS)

def router_agent(user_input: str, chat_history: list, previous_agent_type: str = None) -> dict:
    # Ensure all elements in chat_history have a 'message' field
    formatted_history = []
    for msg in chat_history:
        if 'content' in msg:
            formatted_history.append({
                'role': msg['role'],
                'message': msg['content']
            })
        elif 'message' in msg:
            formatted_history.append(msg)

    key_info = next((msg['message'] for msg in formatted_history if msg['role'] == 'System' and msg['message'].startswith('Key information:')), None)
    
    updated_preamble = preamble + f"""
    Previous context: {previous_agent_type if previous_agent_type else 'None'}
    Key information: {key_info if key_info else 'None'}
    
    Important: Evaluate the current query objectively. The user may switch topics.
    Respond ONLY with one of the following: {', '.join(AGENTS.keys())}.
    """

    # Determine which agent to use
    agent_type_response = cohere_client.chat(
        message=f"Classify this query: {user_input}",
        model=model,
        chat_history=formatted_history,
        preamble=updated_preamble
    )
    
    agent_type = agent_type_response.text.strip().lower()
    print(f"Raw agent type response: {agent_type}")
    
    # Check if the agent type is directly in our AGENTS dictionary
    if agent_type in AGENTS.keys():
        selected_agent = agent_type
    else:
        # If not, check for partial matches
        matching_agents = [agent for agent in AGENTS.keys() if agent in agent_type]
        if matching_agents:
            selected_agent = matching_agents[0]
        else:
            selected_agent = None

    if selected_agent:
        print(f"Selected agent: {selected_agent}")
        return handle_query(user_input, chat_history, selected_agent)
    else:
        return handle_unclear_agent_type(user_input, chat_history)

def handle_query(user_input, chat_history, agent_type):
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
    else:
        # Handle other agents as before
        result = AGENTS[agent_type]["tool"].invoke({"input": user_input, "chat_history": formatted_history})
    
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

def handle_unclear_agent_type(user_input, chat_history):
    clarification_prompt = f"I'm not sure which agent should handle this query: '{user_input}'. Could you please provide more context or clarify your question?"
    
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


