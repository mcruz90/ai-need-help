from .triage_helper_functions import format_chat_history, extract_key_info, stream_with_timeout, serialize_tool_call
from llm_models.chat import chat_model
from .triage_tools import tools, functions_map
from utils import logger, log_structured
import json
import asyncio
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from db import store_conversation
from typing import List, Dict, Tuple
from json import JSONEncoder

class Citation:
    def __init__(self, start: int, end: int, text: str, sources: List[Dict]):
        self.start = start
        self.end = end
        self.text = text
        self.sources = sources

    def to_dict(self):
        return {
            'start': self.start,
            'end': self.end,
            'text': self.text,
            'sources': [self.serialize_source(s) for s in self.sources]
        }

    @staticmethod
    def serialize_source(source):
        if isinstance(source, dict):
            return source
        return {k: v for k, v in source.__dict__.items() if not k.startswith('_')}

def add_citations_to_response(response: str, citations: List[Citation]) -> Tuple[str, Dict[str, int], List[str]]:
    if not citations:
        return response, {}, []  # Return the original response if there are no citations

    # Sort citations by start position in descending order
    sorted_citations = sorted(citations, key=lambda c: c.start, reverse=True)
    
    # Create a mapping of unique URLs to citation indices
    url_to_index = {}
    current_index = 1


    # First pass: assign indices to unique URLs
    for citation in sorted_citations:
        for source in citation.sources:
            serialized_source = Citation.serialize_source(source)
            content_str = serialized_source.get('tool_output', {}).get('content', '[]')
            try:
                content = json.loads(content_str)
                for item in content:
                    url = item.get('url', '')
                    if url and url not in url_to_index:
                        url_to_index[url] = current_index
                        current_index += 1
            except json.JSONDecodeError:
                print(f"Failed to parse JSON: {content_str}")

    # Second pass: insert citation tags
    for citation in sorted_citations:
        citation_tags = []
        for source in citation.sources:
            serialized_source = Citation.serialize_source(source)
            content_str = serialized_source.get('tool_output', {}).get('content', '[]')
            try:
                content = json.loads(content_str)
                for item in content:
                    url = item.get('url', '')
                    if url and url in url_to_index:
                        index = url_to_index[url]
                        if not any(tag for tag in citation_tags if f'href="{url}"' in tag):
                            citation_tags.append(f'<a href="{url}">{index}</a>')
            except json.JSONDecodeError:
                print(f"Failed to parse JSON: {content_str}")
        
        if citation_tags:
            citation_html = ''.join(citation_tags)
            response = (
                response[:citation.end] +
                citation_html +
                response[citation.end:]
            )
    
    return response, url_to_index

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

async def triage_agent(user_message: str, chat_history: list, background_tasks: BackgroundTasks):
    full_response = ""
    citations: List[Citation] = []

    async def generate():
        nonlocal full_response, citations
        try:
            log_structured("INFO", "Starting triage agent", {"user_message": user_message})

            formatted_history = format_chat_history(chat_history)
            context_info = await extract_key_info(user_message, chat_history)

            system_message = f"""
            ## Task & Context
            You help users route their questions to the appropriate AI agents available as tools. 

            You will be asked a very wide array of requests on all kinds of topics.
            You will be equipped with a wide range of tools to help you, which you use to research your answer.
            You should focus on serving the user's needs as best you can, which will be wide-ranging.

            ## Context Info
            {context_info}

            The context info is provided to help you route the user's query to the appropriate AI agent.

            ## Tool Call Parameters
            Where specified, all required arguments fo the selected AI agent must be passed as a stringified JSON object.
            queries: {user_message}
            chat_history: {formatted_history}
            """

            messages = [
            {"role": "system", "content": system_message},
            *formatted_history,
            {"role": "user", "content": user_message},
            ]
            
            try:
                response = await asyncio.wait_for(
                    chat_model.generate_response_with_tools(messages, tools),
                    timeout=30.0  # 30 seconds timeout
                )
            except asyncio.TimeoutError:
                log_structured("ERROR", "Triage agent initial response timed out", {"user_message": user_message})
                yield "Sorry, the initial request timed out. Please try again.".encode('utf-8')
                return

            logger.info(response)

            logger.info("The model recommends doing the following tool calls:\n")
            logger.info("Tool plan:")
            logger.info("%s", response.message.tool_plan)
            logger.info("Tool calls:")

            for tc in response.message.tool_calls:
                logger.info(f"Tool name: {tc.function.name} | Parameters: {tc.function.arguments}")

            # append the chat history
            messages.append(
                {
                    "role": "assistant",
                    "tool_calls": [serialize_tool_call(tc) for tc in response.message.tool_calls],
                    "tool_plan": response.message.tool_plan,
                }
            )

            # Iterate over the tool calls generated by the model
            for tc in response.message.tool_calls:
                try:
                    tool_result = await asyncio.wait_for(
                        functions_map[tc.function.name](**json.loads(tc.function.arguments)),
                        timeout=30.0  # 30 seconds timeout
                    )
                    if isinstance(tool_result, dict) and "error" in tool_result:
                        log_structured("ERROR", f"Error from {tc.function.name}", {"error": tool_result['error']})
                        yield f"An error occurred: {tool_result['error']}".encode('utf-8')
                        continue
                    
                    log_structured("INFO", f"Tool results from {tc.function.name}", {"results": tool_result})

                    # Process the tool results
                    if tc.function.name == 'code_agent':
                        # For code_agent, we don't need to process the results further
                        processed_results = tool_result.get('result', '')
                    else:
                        processed_results = []
                        if 'result' in tool_result:
                            for item in tool_result['result']:
                                if 'document' in item and 'data' in item['document']:
                                    try:
                                        data = json.loads(item['document']['data'])
                                        processed_results.append(data['data'])
                                    except json.JSONDecodeError:
                                        log_structured("ERROR", "Failed to parse JSON", {"data": item['document']['data']})

                    # Append processed results to messages
                    messages.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": json.dumps(processed_results)}
                    )

                except asyncio.TimeoutError:
                    log_structured("ERROR", f"Tool call {tc.function.name} timed out", {"arguments": tc.function.arguments})
                    yield f"Sorry, the {tc.function.name} operation timed out. Continuing with available information.".encode('utf-8')
                except Exception as e:
                    log_structured("ERROR", f"Error calling {tc.function.name}", {"error": str(e)})
                    yield f"An error occurred while processing your request: {str(e)}. Continuing with available information.".encode('utf-8')

            # Generate final response

            updated_instructions = f"""
            ## Task & Context
            You have just received the results of your tool calls, and will now be asked to provide a final response to the user.
            Your final response must be based on the tool results provided.

            ## Context Info
            The context of the user's question is: {context_info}

            ## Instructions
            The tool results contain the answer to the user's question. Your task is to present this information in a clear and helpful manner.
            Do not state that you can't help with the request, as the necessary information has been provided by the tool.

            If the tool results are from the code_agent:
            1. Present the entire response from the code_agent exactly as it is, without any modifications or additional explanations.
            2. Do not attempt to reformat, summarize, or explain the code_agent's response. It has been pre-formatted and explained appropriately.

            For other types of tool results:
            If the tool results contain a list of documents, your final response should be informed by these documents and should answer
            the user's original question. Do not state anything that cannot be backed up by the documents.

            ## Style Guidelines
            - When presenting code_agent results, do not add any additional commentary or explanation.
            - For other types of results, be concise and to the point if the complexity of the user's request is low.
            - Be detailed and comprehensive if the complexity of the user's request is high.
            - Be kind and helpful, and maintain a professional tone.
            """

            messages.append({"role": "assistant", "content": updated_instructions})

            log_structured("INFO", "Messages before final response generation", {"messages": messages})

            response_stream = await chat_model.generate_streaming_response(
                messages=messages,
                tools=tools
            )

            log_structured("INFO", "Starting final answer generation")
            async for chunk in stream_with_timeout(response_stream, timeout=10.0):  # 10 second timeout between chunks
                if chunk and chunk.type == "content-delta":
                    content = chunk.delta.message.content.text
                    if content:
                        full_response += content
                        # Stream the raw content immediately
                        yield content.encode('utf-8')
                elif chunk and chunk.type == "citation-start":
                    citation = Citation(
                        start=chunk.delta.message.citations.start,
                        end=chunk.delta.message.citations.end,
                        text=chunk.delta.message.citations.text,
                        sources=chunk.delta.message.citations.sources
                    )
                    citations.append(citation)
                log_structured("DEBUG", "Chunk received", {"chunk": str(chunk)})

            log_structured("DEBUG", "Full response and citations", {
                "full_response": full_response,
                "citations": json.dumps([c.to_dict() for c in citations], cls=CustomJSONEncoder)
            })

            # Process citations after generating the full response
            cited_response, url_to_index, sources_list = add_citations_to_response(full_response, citations)
            
            log_structured("DEBUG", "Citations processing", {
                "original_response": full_response,
                "cited_response": cited_response,
                "citations": json.dumps([c.to_dict() for c in citations], cls=CustomJSONEncoder),
                "url_to_index": json.dumps(url_to_index),
                "sources_list": json.dumps(sources_list)
            })

            log_structured("INFO", "Final response completed", {
                "full_response": full_response,
                "cited_response": cited_response,
                "sources_list": json.dumps(sources_list)
            })

            # Yield a special marker to indicate the end of streaming and start of the cited response
            yield b"__CITATIONS_START__"
            # Yield the cited response
            yield cited_response.encode('utf-8')

        except Exception as e:
            log_structured("ERROR", "Unexpected error in triage_agent", {"error": str(e)})
            yield f"An unexpected error occurred: {str(e)}".encode('utf-8')

    def update_chat_history():
        try:
            store_conversation(user_message, full_response)
        except Exception as e:
            logger.error(f"Error in update_chat_history: {str(e)}")

    background_tasks.add_task(update_chat_history)

    return StreamingResponse(generate(), media_type="text/html")
