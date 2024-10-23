import json
from typing import List, Any, Dict, Tuple, Union
import asyncio
from cohere import ToolCallV2, ToolSource
from llm_models.chat import chat_model
from utils.utils import logger

class Citation:
    def __init__(self, start: int, end: int, text: str, sources: List[Dict[str, Any]]):
        self.start = start
        self.end = end
        self.text = text
        self.sources = sources

    def to_dict(self) -> Dict[str, Any]:
        return {
            'start': self.start,
            'end': self.end,
            'text': self.text,
            'sources': self.sources
        }

class CitationHandler:
    @staticmethod
    def add_citations_to_response(response: str, citations: List[Citation]) -> Tuple[str, Dict[str, int]]:
        logger.info(f"Adding citations to response. Citations count: {len(citations)}")

        if not citations:
            logger.warning("No citations provided")
            return response, {}

        sorted_citations = sorted(citations, key=lambda c: c.start, reverse=True)
        url_to_index = {}
        current_index = 1

        # First pass: assign indices to unique URLs
        for citation in sorted_citations:
            for source in citation.sources:
                url = CitationHandler.extract_url(source)
                if url:
                    logger.debug(f"Extracted URL: {url}")
                    if url not in url_to_index:
                        url_to_index[url] = current_index
                        current_index += 1
                else:
                    logger.warning(f"Failed to extract URL from source: {source}")

        logger.info(f"URL to index mapping: {url_to_index}")

        # Second pass: insert citation tags
        for citation in sorted_citations:
            citation_tags = []
            for source in citation.sources:
                url = CitationHandler.extract_url(source)
                if url and url in url_to_index:
                    index = url_to_index[url]
                    if not any(tag for tag in citation_tags if f'href="{url}"' in tag):
                        citation_tags.append(f'<a href="{url}">[{index}]</a>')
            
            if citation_tags:
                citation_html = ''.join(citation_tags)
                response = (
                    response[:citation.end] +
                    citation_html +
                    response[citation.end:]
                )
        
        logger.info(f"Response with citations: {response}")
        return response, url_to_index

    @staticmethod
    def extract_url(source: Union[Dict[str, Any], ToolSource]) -> str:
        try:
            logger.info(f"Source: {source}")
            logger.info(f"Type of source: {type(source)}")
            
            if isinstance(source, ToolSource):
                content = source.tool_output.get('content', '{}')
                data = json.loads(content)
                url = data.get('data', {}).get('url', '')
                if url:
                    return url
            elif isinstance(source, dict):
                if 'tool_output' in source and isinstance(source['tool_output'], dict):
                    content = source['tool_output'].get('content', '{}')
                    data = json.loads(content)
                    url = data.get('data', {}).get('url', '')
                    if url:
                        return url
                
                for key, value in source.items():
                    if isinstance(value, dict):
                        url = value.get('url', '')
                        if url:
                            return url
            
            logger.warning(f"No URL found in source:")
            return ''
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON in source:")
            return ''
        except Exception as e:
            logger.error(f"Error extracting URL from source: {e}")
            return ''

class ChatProcessor:
    @staticmethod
    async def extract_key_info(user_input: str, chat_history: List[Dict[str, str]], timeout: float = 45.0) -> str:
        """
        Extracts key information from the user's input and chat history for routing purposes.
        """
        logger.info(f"Starting extract_key_info for user input: {user_input[:50]}...")

        prompt = f"""
        Analyze the user's input and chat history to extract key information for routing purposes. 
        Your task is to provide a concise summary that will help determine the most appropriate AI agent to handle the query.

        Focus on:
        1. Main topic or subject area (e.g., math, coding, general knowledge, scheduling)
        2. User's intent (e.g., seeking information, requesting a tutorial, scheduling an event)
        3. Specific requirements or constraints mentioned
        4. Any indication of ongoing conversations or previous agent interactions
        5. Level of complexity or depth required in the response

        Do NOT attempt to answer the query. Instead, provide a brief, structured summary of the key points that will aid in routing.

        Chat history: "{chat_history}"

        Key Information Summary:
        1. Topic:
        2. Intent:
        3. Specific Requirements:
        4. Conversation Context:
        5. Complexity Level:

        Additional Relevant Details:
        """

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = await asyncio.wait_for(chat_model.generate_response(messages), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Timeout error: extract_key_info took longer than {timeout} seconds")
            return "Error: Request timed out while extracting key info"
        except Exception as e:
            logger.error(f"Error extracting key info: {e}")
            return "Error extracting key info"

        return response

    @staticmethod
    def format_chat_history(chat_history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Formats the chat history for processing, returning only user and assistant messages.
        """
        formatted_history = []
        for msg in chat_history[-20:]:  # Only consider the last 20 messages for context
            if isinstance(msg, dict) and 'role' in msg:
                role = msg['role'].lower()
                if role in ['user', 'assistant']:
                    content = msg.get('message') or msg.get('content') or ''
                    formatted_history.append({"role": role, "content": content})
            else:
                logger.warning(f"Unexpected message format in chat history: {msg}")
        return formatted_history

class StreamHandler:
    @staticmethod
    async def stream_with_timeout(stream: Any, timeout: float):
        """
        Yields chunks from the stream with a timeout between chunks.
        """
        try:
            timer = asyncio.create_task(asyncio.sleep(timeout))
            async for chunk in stream:
                yield chunk
                timer.cancel()
                timer = asyncio.create_task(asyncio.sleep(timeout))
            timer.cancel()
        except asyncio.TimeoutError:
            logger.error("Stream timed out")
            yield "Stream timed out. Please try again.".encode('utf-8')

class ToolCallHandler:
    @staticmethod
    def serialize_tool_call(tool_call: ToolCallV2) -> Dict[str, Any]:
        """
        Serializes a ToolCallV2 object into a dictionary.
        """
        return {
            "id": tool_call.id,
            "type": tool_call.type,
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments
            }
        }

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)
