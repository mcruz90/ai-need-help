from agents.calendar.tools_model import tools, functions_map
from datetime import date
from llm_models.chat import chat_model
import json
from typing import List, Dict, Any
from utils.utils import logger
from agents.triage.triage_utils import StreamHandler

async def calendar_agent(query: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Call the calendar_agent to help with the user's calendar.
    """
    try:
        logger.info(f"Calling calendar_agent to address the user's query")

        #Step 1: System Prompt to guide the agent
        system_prompt = f"""
            ## Task & Context
            You are an expert calendar assistant with over 10 years experience who helps users with their personal scheduling. 

            When creating events, you must make sure that a new event does not overlap with any existing event.
            Inform the user of the conflict.

            When getting events, be very careful to think logically through the user's query, as they could be
            providing a very abstract concept of the date, such as "every weekend next month", "the last half of the month",
            "over the next three weeks" or "all Wednesdays". In cases such as these, you must avoid making numerous calls
            to the get_calendar_events function. You should first calculate and reason through the range of time they're
            asking about to find out what date to use when getting events. 

            If it is unclear what date the user is asking about, you must say so, and get clarification. 

            Today is  ${str(date.today())}

            ## Style Guide
            You are very precise and detail-oriented with your responses. For example, you cannot just say "You have an
            event scheduled for tomorrow", you must state the description, date and time.

            ## Important
            Always carefully review the results of your tool calls before responding to the user.
            If a tool call returns events, make sure to include those in your response.
            If no events are found, explicitly state that no events were found for the specified date or time range.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            *chat_history,
            {"role": "user", "content": query}
        ]

        # Step 2: Generate the tool plan and tool calls and append the results to the messages list
        response = await chat_model.generate_response_with_tools(messages, tools)

        for tc in response.message.tool_calls:
            logger.info(f"Tool name: {tc.function.name} | Parameters: {tc.function.arguments}")

        messages.append(
            {
                "role": "assistant",
                "tool_calls": response.message.tool_calls,
                "tool_plan": response.message.tool_plan,
            }
        )

        # Step 3: Iterate over the tool calls generated by the model and append the results of the tool calls to the messages list
        tool_content = []
        if response.message.tool_calls:
            for tc in response.message.tool_calls:
                try:
                    tool_result = await functions_map[tc.function.name](**json.loads(tc.function.arguments))
                    if isinstance(tool_result, dict) and "error" in tool_result:
                        logger.error(f"Error from {tc.function.name}: {tool_result['error']}")
                        return {"error": f"An error occurred: {tool_result['error']}"}
                    
                    tool_content.append(json.dumps(tool_result))
                    messages.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": tool_content}
                    )

                except Exception as e:
                    logger.error(f"Error calling {tc.function.name}: {str(e)}")
                    return {"error": f"An error occurred while processing your request: {str(e)}"}
                
        logger.info("Tool results that will be used by the calendar agent to generate the final response")
        for result in tool_content:
            logger.info(result)

        # Step 4: Generate the final response
        response_stream = await chat_model.generate_streaming_response(
            messages=messages,
            tools=tools
        )
        
        full_response = ""
        # Step 5: Stream the response back to the triage agent
        async def response_generator():
            nonlocal full_response
            logger.info("Starting response generation")
            async for chunk in StreamHandler.stream_with_timeout(response_stream, timeout=10.0):
                if chunk and chunk.type == "content-delta":
                    content = chunk.delta.message.content.text
                    if content:
                        full_response += content
                        logger.debug(f"Content chunk received: {content}")
                        yield {"type": "content", "data": content}
                elif chunk and chunk.type in ["message-start", "content-start", "content-end", "message-end"]:
                    logger.debug(f"Received chunk type: {chunk.type}")
                else:
                    logger.warning(f"Unexpected chunk type received: {chunk.type}")
            
            logger.info("Response generation completed")
            logger.info(f"Full response: {full_response}")
            
            try:
                yield {"type": "full_response", "data": full_response}
                yield {"type": "cited_response", "data": full_response}
                yield {"type": "url_to_index", "data": {}}
            except Exception as e:
                yield {"type": "error", "data": str(e)}

        return response_generator()

    except Exception as e:
        logger.error(f"Error in calendar_agent: {e}")
        raise e