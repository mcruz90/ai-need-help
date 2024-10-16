from llm_models.chat import chat_model
from agents.cohere_web_search.web_search_tools import web_search_tool, web_search
from agents.router.helper_functions import format_chat_history
from utils import logger
import json
from typing import List, Dict, Any
from datetime import datetime
from reflexion.reflexion import web_search_reflexion

MAX_REFLEXION_ITERATIONS = 3
MAX_CONFIDENCE_THRESHOLD = 0.9

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
            "max_iterations_reached": True
        }
    
    formatted_history = format_chat_history(chat_history)
    
    current_date = datetime.now().strftime("%Y-%m-%d")

    system_prompt = f"""
    Analyze the following user query:
    "{query}"

    You have been provided with the following context information related to the user's query:
    "{context_info}"

    The context may contain information that references a previous iteration of the web search and response generation that was deemed unsatisfactory.
    If this is the case, you must use this information to inform your new search strategy.

    Your task is to generate an optimal web search strategy to find the most relevant and up-to-date information to answer the user's query.
    The complexity level mentioned in the context info should guide the depth and breadth of your search strategy.
    
    Follow these steps:

    1. Analyze the query and context:
    - Identify the main topic and any subtopics
    - Determine the user's intent (e.g., seeking information, comparing options, finding recent events)
    - Note any specific requirements or constraints
    - Consider the complexity level (simple, moderate, or complex) and adjust your strategy accordingly

    2. Temporal context:
    - Today's date is {current_date}
    - Assess whether the query requires recent information or historical data
    - For queries about current events or time-sensitive topics, prioritize recency in your search strategy

    3. Generate search keywords:
    - Extract 3-5 highly relevant keywords or phrases from the query and context
    - For simple queries, focus on the most essential terms
    - For moderate or complex queries, include more specific or technical terms

    4. Formulate search queries:
    - Combine the keywords into 1-3 concise and effective search queries, depending on the complexity level
    - For simple queries, one well-crafted search might suffice
    - For moderate or complex queries, consider multiple searches to cover different aspects
    - Use advanced search operators if appropriate (e.g., quotation marks for exact phrases, site: for specific websites)

    5. Specify search parameters:
    - Suggest any filters or advanced search options that would be beneficial (e.g., date range, region, language)
    - For complex queries, consider recommending more specialized databases or resources

    Output your response in the following format:

    Search Strategy:
    1. Complexity Level: [Simple/Moderate/Complex]
    2. Main topic: [Brief description]
    3. User intent: [Brief description]
    4. Key considerations: [List any important factors, including temporal context]
    5. Primary keywords: [List 3-5 keywords]
    6. Search queries:
    - [Query 1]
    - [Query 2] (if necessary for moderate/complex queries)
    - [Query 3] (if necessary for complex queries)
    7. Search parameters: [List any recommended filters or options]
    8. Suggested sources: [List any specific websites or types of sources to prioritize]

    Ensure your strategy is tailored to the complexity level of the query while finding the most relevant, accurate, and up-to-date information to address the user's query effectively.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        *formatted_history,
        {"role": "user", "content": query}
    ]
    
    logger.debug(f"Starting iteration {iteration} of web search and response generation")

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
        reflexion_result = await web_search_reflexion(query, web_search_response.message.content[0].text, tool_plan, context_info)

        logger.info(f"Reflexion result: {reflexion_result}")

        satisfactory_response = reflexion_result.get("satisfactory_response", False)
        confidence_score = float(reflexion_result.get("confidence_score", 0))

        logger.info(f"Loop condition: satisfactory_response={satisfactory_response}, confidence_score={confidence_score}")
        logger.info(f"Loop break decision: {(satisfactory_response and confidence_score > 0.7) or confidence_score > 0.9}")

        if confidence_score >= MAX_CONFIDENCE_THRESHOLD:
            logger.info(f"Maximum confidence threshold reached. Returning result.")
        elif (satisfactory_response and confidence_score > 0.7) or confidence_score > MAX_CONFIDENCE_THRESHOLD:
            logger.info(f"Satisfactory response found at iteration {iteration + 1}.")
        elif iteration < MAX_REFLEXION_ITERATIONS - 1:
            logger.info(f"Response unsatisfactory. Attempting iteration {iteration + 1}")
            new_context = f"""
            The previous response was deemed unsatisfactory for the user query ("{query}").

            Critique: {reflexion_result['critique']}
            Confidence Score: {reflexion_result['confidence_score']}
            Areas for Improvement: {', '.join(reflexion_result.get('areas_for_improvement', []))}
            New Tool Plan Suggestion: {', '.join(reflexion_result.get('new_tool_plan', []))}

            Your task is to generate an improved web search strategy based on the above feedback from the previous iteration.
            Focus on addressing the critique and areas for improvement mentioned in the feedback. Consider the following:

            1. Carefully review the critique and areas for improvement.
            2. Adjust your search strategy to address the specific points raised in the feedback.
            3. If a new tool plan is suggested, incorporate it into your new search strategy.
            4. Ensure that your new strategy is more targeted and more likely to yield better results.

            Output your response in the same format as before:

            Improved Search Strategy:
            1. Complexity Level: [Simple/Moderate/Complex]
            2. Main topic: [Brief description, with any adjustments based on feedback]
            3. User intent: [Brief description, refined if necessary]
            4. Key considerations: [List any important factors, including how you've addressed the feedback]
            5. Primary keywords: [List 3-5 keywords, adjusted based on feedback]
            6. Search queries:
            - [Query 1]
            - [Query 2] (if necessary for moderate/complex queries)
            - [Query 3] (if necessary for complex queries)
            7. Search parameters: [List any recommended filters or options, refined based on feedback]
            8. Suggested sources: [List any specific websites or types of sources to prioritize, adjusted if necessary]

           """
            
            return await perform_web_search_and_generate_response(query, formatted_history + [{"role": "assistant", "content": web_search_response.message.content[0].text}], new_context, iteration + 1)

    logger.info(f"Final response generated after {iteration + 1} iterations")

    return {
        "messages": messages,
        "response": web_search_response.message.content[0].text if web_search_response and hasattr(web_search_response, 'message') and web_search_response.message.content else "",
        "tool_plan": getattr(web_search_response.message, 'tool_plan', None) if web_search_response and hasattr(web_search_response, 'message') else None,
        "tool_calls": getattr(web_search_response.message, 'tool_calls', None) if web_search_response and hasattr(web_search_response, 'message') else None,
        "tool_results": tool_content,
        "citations": getattr(web_search_response.message, 'citations', []) if web_search_response and hasattr(web_search_response, 'message') else [],
        "iterations": iteration + 1
    }