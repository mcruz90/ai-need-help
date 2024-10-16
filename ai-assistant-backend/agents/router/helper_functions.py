import re
import json
from llm_models.chat import chat_model
from utils import logger
from typing import List, Any

### Context extraction functions for router agent ###
def extract_key_info(user_input: str, chat_history: list) -> str:
    """
    Extracts the key information from the user's input to determine which agent to route the query to.
    """
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

    response = chat_model.generate_response(messages)

    return response.message.content[0].text if response else None

def parse_agent_response(response: str) -> str:
    """
    Parses the response from the model to determine the agent type.
    """
    # First, try to match the format "AGENT_NAME: explanation"
    agent_match = re.match(r'^(\w+)(?:\s*:\s*(.*))?$', response.strip(), re.IGNORECASE)
    
    if agent_match:
        return agent_match.group(1).lower()
    
    # If that fails, look for any word followed by a colon
    agent_match = re.search(r'(\w+):', response)
    
    if agent_match:
        return agent_match.group(1).lower()
    
    # If no match is found, log a warning and return 'general'
    logger.warning(f"Could not parse agent type from response: {response}. Returning 'general'.")
    return 'general'

def format_chat_history(chat_history: list) -> list:
    """Formats the chat history for processing, returning only user and assistant messages."""
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

### Response formatting functions ###

def code_block_formatter(raw_output: str) -> str:
    """
    Processes the raw output from the model and enhances it for frontend rendering.
    Ensures that code blocks and LaTex preserve their formatting with proper line breaks.
    """
    
    # This regex finds code blocks enclosed in triple backticks and ensures they contain newlines
    def format_code_blocks(text):
        code_block_pattern = re.compile(r'```(\w+)?\n?(.*?)```', re.DOTALL)
        
        def replacer(match):
            language = match.group(1) or ''
            code = match.group(2).strip()
            # Ensure code has proper line breaks
            formatted_code = '\n'.join(line.strip() for line in code.splitlines())
            return f'```{language}\n{formatted_code}\n```'
        
        return code_block_pattern.sub(replacer, text)
    
    enhanced_output = format_code_blocks(raw_output)
    
    return enhanced_output

def enhance_output_with_citations(output: str, citations: list) -> str:
    """
    Enhances the output string with inline citations that link directly to the URLs.
    
    :param output: The original output string from the model
    :param citations: List of citation objects
    :return: Enhanced output string with inline citations linking to URLs
    """

    
    logger.debug(f"Received citations: {citations}")
    for citation in citations:
        logger.debug(f"Citation: start={citation.start}, end={citation.end}, text={citation.text}")
        for source in citation.sources:
            logger.debug(f"Source: {source}")

    url_dict = {}
    current_number = 1

    # Sort citations by their end position in descending order
    sorted_citations = sorted(citations, key=lambda x: x.end, reverse=True)
    
    for citation in sorted_citations:
        urls = list(set(doc['url'] for doc in citation.documents))
        citation_links = []
        
        for url in urls:
            if url not in url_dict:
                url_dict[url] = current_number
                current_number += 1
            num = url_dict[url]
            citation_links.append(f'<a href="{url}" class="citation-link" target="_blank" rel="noopener noreferrer"><span class="citation">{num}</span></a>')
        
        citation_marker = f" {''.join(sorted(citation_links))}"
        output = output[:citation.end] + citation_marker + output[citation.end:]
    
    # Clean up and format the output
    lines = output.split('\n')
    formatted_lines = []
    
    for line in lines:
        # Remove excess commas and spaces
        line = ' '.join(line.split()).strip(', ')
        
        # Handle list items and headings
        if line.startswith('- ') or line.startswith('#'):
            formatted_lines.append('')  # Add empty line before
        
        formatted_lines.append(line)
        
        # Add newline after headings with citations
        if line.startswith('#') and '<span class="citation">' in line:
            formatted_lines.append('')
    
    # Join the formatted lines
    formatted_output = '\n'.join(formatted_lines).strip()
    
    return formatted_output

def output_with_citations(output: str, citations: List[Any]) -> str:
    """
    Enhances the output string with inline citations that link directly to the URLs.
    
    :param output: The original output string
    :param citations: A list of Citation objects from Cohere API
    :return: Enhanced output string with inline citations linking to URLs
    """
    
    logger.debug(f"Received citations: {citations}")
    
    url_dict = {}
    current_number = 1

    # Sort citations by their end position in descending order
    sorted_citations = sorted(citations, key=lambda x: x.end, reverse=True)

    for citation in sorted_citations:
        logger.debug(f"Processing citation: start={citation.start}, end={citation.end}, text={citation.text}")
        urls = set()
        if citation.sources:
            for source in citation.sources:
                logger.debug(f"Source: {source}")
                if hasattr(source, 'tool_output') and isinstance(source.tool_output, dict) and 'content' in source.tool_output:
                    try:
                        documents = json.loads(source.tool_output['content'])
                        for doc in documents:
                            if isinstance(doc, dict) and 'data' in doc and 'url' in doc['data']:
                                urls.add(doc['data']['url'])
                    except json.JSONDecodeError:
                        logger.error(f"Error decoding JSON: {source.tool_output['content']}")

        citation_links = []
        for url in urls:
            if url not in url_dict:
                url_dict[url] = current_number
                current_number += 1
            num = url_dict[url]
            citation_links.append(f'<a href="{url.strip()}" class="citation-link" target="_blank" rel="noopener noreferrer"><span class="citation">{num}</span></a>')
        
        citation_marker = ''.join(sorted(citation_links))
        output = output[:citation.end].rstrip() + citation_marker + output[citation.end:].lstrip()

    # Clean up and format the output
    lines = output.split('\n')
    formatted_lines = []
    
    for line in lines:
        # Remove excess commas and spaces
        line = re.sub(r'\s+', ' ', line).strip(', ')
        
        # Handle list items and headings
        if line.startswith('- ') or line.startswith('#'):
            formatted_lines.append('')  # Add empty line before
        
        formatted_lines.append(line)
        
        # Add newline after headings with citations
        if line.startswith('#') and '<span class="citation">' in line:
            formatted_lines.append('')

    # Join the formatted lines
    formatted_output = '\n'.join(formatted_lines).strip()
    
    # Remove any potential spaces between adjacent citation links
    formatted_output = re.sub(r'(</a>)\s+(<a)', r'\1\2', formatted_output)
    
    return formatted_output
