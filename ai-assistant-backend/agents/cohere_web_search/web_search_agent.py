from llm_models.chat import chat_model
from agents.cohere_web_search.web_search_tools import web_search_tool, web_search
from agents.router.helper_functions import format_chat_history
import logging
import json
from typing import List, Dict, Any
from rich.logging import RichHandler

logger = logging.basicConfig(
       level="INFO",
       format="%(message)s",
       datefmt="[%X]",
       handlers=[RichHandler(rich_tracebacks=True)]
   )

logger = logging.getLogger(__name__)

def cohere_web_search_agent(user_input: str, chat_history: list) -> dict:
    """
    Search the web for information relevant to the user's query.
    """

    # Perform the initial web search and generate response

    # Reflect on the inital result and return suggestions for improvement or the original response    
    #final_response = apply_reflexion(perform_web_search_and_generate_response, user_input, initial_result)
    
    # return the final response
    return perform_web_search_and_generate_response(user_input, chat_history)

def perform_web_search_and_generate_response(query: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
    # Ensure all roles are lowercase and use 'content' instead of 'message'
    formatted_history = format_chat_history(chat_history)
    
    system_prompt = f"""
    Analyze the following query:
    "{query}"

    Extract some keywords from the user input as well as the provided chat history and use them to inform what would be best to search for on the internet.
    """
    # Combine preamble and formatted history into a single messages list as required by Cohere Chat v2 endpoint
    messages = [
        {"role": "system", "content": system_prompt},
        *formatted_history,
        {"role": "user", "content": query}
    ]
    # Step 1: The model will generate a response with a tool plan and tool calls
    response = chat_model.generate_response_with_tools(messages, web_search_tool)

    tool_content = []

    if response.message and response.message.tool_calls:
        for tc in response.message.tool_calls:
            logger.info(f"Tool Plan: {response.message.tool_plan}")
            logger.info(f"Tool name: {tc.function.name} | Parameters: {tc.function.arguments}")

        # Step 2: append the model's tool calls and plan to the chat history
        messages.append(
            {
                "role": "assistant",
                "tool_calls": response.message.tool_calls,
                "tool_plan": response.message.tool_plan,
            }
        )

        # Step 3: Get tool results
        for idx, tc in enumerate(response.message.tool_calls):
            try:
                args = json.loads(tc.function.arguments)
                tool_result = web_search(**args)  # Use web_search directly without caching
                logger.info(f"Tool result: {tool_result}")
                tool_content.append(json.dumps(tool_result))

                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": tool_content}
                )
            except json.JSONDecodeError:
                logger.error(f"Failed to parse tool call arguments: {tc.function.arguments}")
            except Exception as e:
                logger.error(f"Error during web search: {str(e)}")
        
        # Step 4: Generate response and citations
        web_search_response = chat_model.generate_response_with_tools(messages, web_search_tool)
    else:
        # If no tool calls were generated, use the initial response
        web_search_response = response

    return {
        "messages": messages,
        "response": web_search_response.message.content[0].text if web_search_response and hasattr(web_search_response, 'message') and web_search_response.message.content else "",
        "tool_plan": getattr(web_search_response.message, 'tool_plan', None) if web_search_response and hasattr(web_search_response, 'message') else None,
        "tool_calls": getattr(web_search_response.message, 'tool_calls', None) if web_search_response and hasattr(web_search_response, 'message') else None,
        "tool_results": tool_content,
        "citations": getattr(web_search_response.message, 'citations', []) if web_search_response and hasattr(web_search_response, 'message') else []
    }