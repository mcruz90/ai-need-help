from .web_search_tools import web_search_tool as tools, functions_map
from utils.utils import logger
from typing import List, Dict, Any, AsyncGenerator
from agents.search.search_agent import SearchAgent

async def cohere_web_search_agent(queries: str, chat_history: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Search the web for information relevant to the user's queries.
    """

    logger.info(f"Calling search_agent to perform general search")

    # Initialize search agent
    search_agent = SearchAgent(tools, functions_map)

    # Initialize messages
    search_agent.initialize_messages(chat_history, queries)

    # Generate the tool plan and tool calls and append the results of the tool calls to the messages list
    await search_agent.generate_tool_results()

    # Generate the final response
    response_stream = await search_agent.generate_final_response(queries)
    
    # Generate and return the final response stream
    return await search_agent.generate_final_response_stream(response_stream)