from .triage_utils import Citation, ChatProcessor, ToolCallHandler
from llm_models.chat import chat_model
from .triage_tools import tools, functions_map
from utils.utils import logger, log_structured
import json
import asyncio
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from db import store_conversation
from utils.profiling import profile
from typing import AsyncGenerator

TIMEOUT = 90.0

@profile
async def triage_agent(user_message: str, chat_history: list, background_tasks: BackgroundTasks) -> AsyncGenerator[bytes, None]:
    full_response = ""
    cited_response = None
    citations = []
    url_to_index = None

    async def generate():
        nonlocal full_response, citations, cited_response, url_to_index
        try:
            log_structured("INFO", "Starting triage agent", {"user_message": user_message})

            formatted_history = ChatProcessor.format_chat_history(chat_history)

            system_message = f"""
            ## Task & Context
            You help users route their questions to the appropriate AI agents available as tools and do not try to answer the user's request directly. 

            You will be asked a very wide array of requests on all kinds of topics.
            You will be equipped with a wide range of tools to help you direct the user's request to the appropriate AI agent.

            Carefully consider the tool's description and parameters, as well as the complexity and intent of the user's request.
            Do not try to answer the user's request directly, unless they are having casual chit-chat conversations that do not seek information.
            You must use the tools available to you to route the user's request in all other cases.

            ## Tool Call Parameters
            Where specified, all required arguments to the selected AI agent must be passed as a stringified JSON object.
            You must carefully format the arguments as specified in the tool's description and parameters.
            Do not make up any parameters or arguments.
            
            query or user_message: {user_message}
            chat_history: {formatted_history}
            """

            messages = [
                {"role": "system", "content": system_message},
                *formatted_history,
                {"role": "user", "content": user_message},
            ]
            
            try:
                logger.info("Calling chat_model.generate_response_with_tools")
                
                response = await chat_model.generate_response_with_tools(messages, tools)
                
            except asyncio.TimeoutError:
                log_structured("ERROR", "Triage agent initial response timed out", {"user_message": user_message})
                yield "Sorry, the triage agent's initial request timed out. Please try again.".encode('utf-8')
                return

            logger.info(response)

            logger.info("The model recommends doing the following tool calls:\n")
            logger.info("Tool plan:")
            logger.info("%s", response.message.tool_plan)
            logger.info("Tool calls:")

            if response.message.tool_calls:
                for tc in response.message.tool_calls:
                    logger.info(f"Tool name: {tc.function.name} | Parameters: {tc.function.arguments}")

            # append the chat history
            messages.append({
                "role": "assistant",
                "tool_calls": [ToolCallHandler.serialize_tool_call(tc) for tc in (response.message.tool_calls or [])],
                "tool_plan": response.message.tool_plan
            })
            if response.message.tool_calls:
                # Iterate over the tool calls generated by the model
                for tc in response.message.tool_calls:
                    try:
                        tool_result = await asyncio.wait_for(
                            functions_map[tc.function.name](**json.loads(tc.function.arguments)),
                            timeout=TIMEOUT
                        )
                        if isinstance(tool_result, dict) and "error" in tool_result:
                            log_structured("ERROR", f"Error from {tc.function.name}", {"error": tool_result['error']})
                            yield f"An error occurred: {tool_result['error']}".encode('utf-8')
                            continue
                    
                        async for item in tool_result:
                            if item["type"] == "content":
                                full_response += item["data"]
                                yield item["data"].encode('utf-8')
                            elif item["type"] == "citation":
                                citations.append(Citation(**item["data"]))
                            elif item["type"] == "full_response":
                                full_response = item["data"]
                            elif item["type"] == "cited_response":
                                cited_response = item["data"]
                            elif item["type"] == "url_to_index":
                                url_to_index = item["data"]

                        if cited_response:
                            log_structured("INFO", "Received cited response", {
                                "cited_response": cited_response,
                                "url_to_index": url_to_index
                            })
                            # Send the marker on its own line
                            yield b"__CITATIONS_START__\n"
                            # Then send the cited response
                            yield cited_response.encode('utf-8')
                        else:
                            log_structured("WARNING", "No cited response received from tool", {"tool_name": tc.function.name})

                    except asyncio.TimeoutError:
                        log_structured("ERROR", f"Tool call {tc.function.name} timed out", {"arguments": tc.function.arguments})
                        yield f"Sorry, the {tc.function.name} operation timed out. Continuing with available information.".encode('utf-8')
                    except Exception as e:
                        log_structured("ERROR", f"Error calling {tc.function.name}", {"error": str(e)})
                        yield f"An error occurred while processing your request. Continuing with available information.".encode('utf-8')
            elif response.message.content:
                log_structured("INFO", "No tool calls, but text response received", {"text": response.message.content[0].text})
                full_response = response.message.content[0].text
                yield full_response.encode('utf-8')
            else:
                log_structured("WARNING", "No tool calls or text response generated", {"messages": messages})
                default_response = "I'm sorry, but I couldn't generate a proper response. How else can I assist you?"
                full_response = default_response
                yield default_response.encode('utf-8')

            # After all yielding, construct and yield the final JSON response
            if cited_response:
                final_response = {
                    "raw_response": full_response.strip(),
                    "cited_response": cited_response.strip(),
                    "citations": True
                }
            else:
                final_response = {
                    "raw_response": full_response.strip(),
                    "cited_response": None,
                    "citations": False
                }

            # Yield the final JSON object as the last chunk with a newline delimiter
            yield json.dumps(final_response).encode('utf-8') + b'\n'

        except Exception as e:
            log_structured("ERROR", "Unexpected error in triage_agent", {"error": str(e)})
            yield f"An unexpected error occurred in triage_agent: {str(e)}".encode('utf-8')

    def update_chat_history():
        try:
            store_conversation(user_message, full_response)
        except Exception as e:
            logger.error(f"Error in update_chat_history: {str(e)}")

    background_tasks.add_task(update_chat_history)

    return StreamingResponse(generate(), media_type="text/event-stream")