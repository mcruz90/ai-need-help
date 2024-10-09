from config import cohere_client
from web_search_tools import agent_executor as web_search_agent
from calendar_agent import calendar_agent
from tutor_agent import tutor_agent

model = 'command-r-plus-08-2024'

# Define a dictionary of available agents with descriptions
AGENTS = {
    'calendar': {
        'agent': calendar_agent,
        'description': 'an agent that can handle queries related to calendars. You MUST use this agent when the user query is related to calendars.'
    },
    'tutor': {
        'agent': lambda input, history: tutor_agent(input, history),
        'description': 'an agent that can handle queries related to tutoring. You MUST use this agent when the user query is related to tutoring.'
    },
    'general': {
        'agent': lambda input, history: {
            "role": "Chatbot",
            "message": web_search_agent.invoke({"input": input, "preamble": history})["output"],
            "grounded_answer": web_search_agent.invoke({"input": input, "preamble": history}).get("grounded_answer", "No grounded answer provided")
            },
        'description': 'an agent that can handle queries related to general information. Do not use this agent unless the user query is related to general information.'
    }
}

agent_descriptions = "\n".join([f"{key}_agent is {value['description']}" for key, value in AGENTS.items()])

preamble = f"""
You are an expert router agent that determines which agent can best respond to a given query.
The available agents are {list(AGENTS.keys())}.

Agent Descriptions: {agent_descriptions}

After receiving the response, it is very important that you only respond with the name of the agent that can best respond to the user query, as these are the only valid responses that the agents can understand.
For example, if the user query is related to calendars, you should respond with 'calendar'. If the user is asking help for a topic in one
of their classes or explicitly asking for a tutoring session, you
should response with 'tutor'.

If the user query is related to tutoring, you should respond with 'tutor'. Be sure to pay attention to previous context and key information in the chat history. The user may be answering a previous question in the chat history that the tutor agent is asking, so you should continue to route these user queries to the tutor agent.

You should only switch to the general agent if it is obvious from the
chat history and context that the user has moved on from their tutoring session or explicitly concluded the tutoring session. If it is unclear, first ask the user if they are done with their tutoring session before
routing their query to another agent.

"""

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
    Respond ONLY with one of the following: {', '.join(AGENTS.keys())}
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
    if agent_type in AGENTS:
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
    formatted_history = [{
        'role': msg['role'],
        'message': msg['content'] if 'content' in msg else msg['message']
    } for msg in chat_history]
    result = AGENTS[agent_type]['agent'](user_input, formatted_history)
    
    if agent_type == 'calendar':
        # Extract the message from the NonStreamedChatResponse object
        message = result.text if hasattr(result, 'text') else str(result)
        return {
            "role": "Chatbot",
            "message": message,
            "grounded_answer": "Calendar response"
        }
    elif agent_type == 'tutor':
        return {
            "role": "Chatbot",
            "message": result['message'],
            "grounded_answer": result.get('grounded_answer', "No grounded response.")
        }
    else:
        return {
            "role": "Chatbot",
            "message": result.get('message', '') or result.get("grounded_answer", ''),
            "grounded_answer": result.get("grounded_answer", "No grounded answer provided.")
        }

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


if __name__ == "__main__":
    print(router_agent("studying for my linear algebra exam. Can you go through a worked example explaining linear combinations and spanning spaces?", []))