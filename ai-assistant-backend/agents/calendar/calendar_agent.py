from agents.calendar.tools_model import tools, functions_map
from datetime import date
from llm_models.chat import chat_model
import json
import logging

logger = logging.getLogger(__name__)

preamble=f"""
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

        """

def calendar_agent(user_message: str, formatted_history: list) -> dict:
    """
    The calendar agent is provided with a user message and a formatted history.
    Using the calendar tools and access to the user's personal calendar, the agent
    creates a tool plan and a list of tool calls with the appropriate parameters
    to answer the user's query.

    :param user_message: The user's message to the assistant.
    :param formatted_history: The formatted history of the conversation.
    :return: A dictionary with the response from the assistant, that is sent back to the router_agent
    """
    messages = [
        {"role": "system", "content": preamble},
        *formatted_history,
        {"role": "user", "content": user_message}
    ]

    # Step 1: The model will generate a response with a tool plan and tool calls
    response = chat_model.generate_response_with_tools(messages, tools)

    logger.info(f"Tool plan: {response.message.tool_plan}")
    logger.info(f"Tool calls: {response.message.tool_calls}")

    # Step 2: append the model's tool calls and plan to the chat history
    messages.append(
        {
            "role": "assistant",
            "tool_calls": response.message.tool_calls,
            "tool_plan": response.message.tool_plan,
        }
    )

    # Step 3: Iteraate through tool calls and store the tool ids and the tool results in tool_content.
    # Then append the tool content to the messages.
    tool_content = []
    if response.message.tool_calls:
        for tc in response.message.tool_calls:
            tool_result = functions_map[tc.function.name](
                **json.loads(tc.function.arguments)
                )
            tool_content.append(json.dumps(tool_result))
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": tool_content}
            )

    # Step 4: The model will generate a response with the tool calls and tool results.
    response = chat_model.generate_response_with_tools(messages, tools)
    
    # Return only the text content
    return {"response": response.message.content[0].text}
