from llm_models.chat import chat_model
from agents.cohere_web_search.web_search_tools import web_search_tool, web_search
from agents.router.helper_functions import format_chat_history
import logging
import json
from typing import List, Dict, Any
from rich.logging import RichHandler
from datetime import datetime
import re
from reflexion.reflexion import reflexion

MAX_REFLEXION_ITERATIONS = 3

logger = logging.basicConfig(
       level="INFO",
       format="%(message)s",
       datefmt="[%X]",
       handlers=[RichHandler(rich_tracebacks=True)]
   )

logger = logging.getLogger(__name__)

def sanitize_json_string(json_string):
    # Remove any leading/trailing whitespace
    json_string = json_string.strip()
    
    # Ensure the string starts and ends with curly braces
    if not json_string.startswith('{'):
        json_string = '{' + json_string
    if not json_string.endswith('}'):
        json_string = json_string + '}'
    
    # Replace single quotes with double quotes (except within string values)
    json_string = re.sub(r"(?<!\\)'", '"', json_string)
    
    # Ensure all keys are in double quotes
    json_string = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_string)
    
    return json_string

def parse_reflexion_response(response_text):
    try:
        # First, try parsing as-is
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try sanitizing and parsing again
        sanitized = sanitize_json_string(response_text)
        try:
            return json.loads(sanitized)
        except json.JSONDecodeError:
            # If it still fails, log the error and return a default structure
            logger.error(f"Failed to parse reflexion response: {response_text}")
            return {
                "satisfactory_response": False,
                "old_response": "",
                "critique": "Failed to parse the response",
                "old_tool_plan": [],
                "new_tool_plan": []
            }

async def cohere_web_search_agent(user_input: str, chat_history: List[Dict[str, str]], context_info: str) -> Dict[str, Any]:
    """
    Search the web for information relevant to the user's query.
    """

    # Perform the initial web search and generate response

    logger.info(f"Calling cohere_web_search_agent to perform general search")
    return await perform_web_search_and_generate_response(user_input, chat_history, context_info)

async def perform_web_search_and_generate_response(query: str, chat_history: List[Dict[str, str]], context_info: str, iteration: int = 0) -> Dict[str, Any]:
    if iteration >= MAX_REFLEXION_ITERATIONS:
        logger.warning(f"Reached maximum number of reflexion iterations ({MAX_REFLEXION_ITERATIONS}). Returning current result.")
        return {
            "messages": [],
            "response": "Maximum reflexion iterations reached. The response may not be fully satisfactory.",
            "tool_plan": None,
            "tool_calls": None,
            "tool_results": [],
            "citations": [],
            "reflexion_result": None,
            "max_iterations_reached": True
        }
    
    formatted_history = format_chat_history(chat_history)
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    system_prompt = f"""
    Analyze the following query:
    "{query}"

    You are also given the following context information relating to the user's query:
    "{context_info}"

    Extract some keywords from the user input as well as the provided context information and chat history and use them to inform what would be best to search for on the internet.

    Be very mindful about the keywords you choose, paying particular attention to the temporal context of the user's query, making sure to emphasize recency when appropriate,
    as the purpose of web search is to find temporally relevant information to answer the user's query. Today is {current_date}.
    """

    if iteration > 0:
        system_prompt += f"""

    This is attempt {iteration + 1} to improve the response. Previous attempt(s) were unsatisfactory.
    Consider the following feedback when formulating your search strategy and response:
    {context_info}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        *formatted_history,
        {"role": "user", "content": query}
    ]
    
    logger.debug(f"Starting iteration {iteration} of web search and response generation")
    logger.debug(f"Query: {query}")
    logger.debug(f"Context info: {context_info}")
    logger.debug(f"Chat history length: {len(formatted_history)}")
    logger.debug(f"System prompt: {system_prompt}")

    # Step 1: The model will generate a response with a tool plan and tool calls
    response = chat_model.generate_response_with_tools(messages, web_search_tool)

    tool_content = []

    tool_plan = []

    if response.message and response.message.tool_calls:
        for tc in response.message.tool_calls:
            logger.info(f"Tool Plan: {response.message.tool_plan}")
            tool_plan.append(response.message.tool_plan)
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
                tool_result = web_search(**args)
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

        # Step 5: Reflexion
        reflexion_result = await reflexion(query, web_search_response.message.content[0].text, tool_plan, context_info)

        if not reflexion_result["satisfactory_response"] and iteration < MAX_REFLEXION_ITERATIONS - 1:
            logger.info(f"Response unsatisfactory. Attempting iteration {iteration + 1}")
            new_context = f"{reflexion_result['critique']}\n{reflexion_result.get('areas_for_improvement', '')}"
            return perform_web_search_and_generate_response(query, formatted_history + [{"role": "assistant", "content": web_search_response.message.content[0].text}], new_context, iteration + 1)

    else:
        # If no tool calls were generated, use the initial response
        web_search_response = response

    logger.info(f"Final response generated after {iteration + 1} iterations")

    return {
        "messages": messages,
        "response": web_search_response.message.content[0].text if web_search_response and hasattr(web_search_response, 'message') and web_search_response.message.content else "",
        "tool_plan": getattr(web_search_response.message, 'tool_plan', None) if web_search_response and hasattr(web_search_response, 'message') else None,
        "tool_calls": getattr(web_search_response.message, 'tool_calls', None) if web_search_response and hasattr(web_search_response, 'message') else None,
        "tool_results": tool_content,
        "citations": getattr(web_search_response.message, 'citations', []) if web_search_response and hasattr(web_search_response, 'message') else [],
        "reflexion_result": reflexion_result,
        "iterations": iteration + 1
    }
