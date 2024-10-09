import re
import json
from llm_models.chat import chat_model

### Context extraction functions for router agent ###
def extract_key_info(user_input: str) -> str:
    """
    Extracts the key information from the user's input to determine which agent to route the query to.
    """
    prompt = f"""
    Given the following user input, extract and summarize the key information
    that would be relevant for determining the most appropriate AI agent to handle the query.
    Focus on the main topic, intent, and any specific requirements or constraints mentioned.

    Your job is not to answer the user's question, but to gather the relevant details needed
    to help the router agent determine which agent to route the user query to.

    This should be a short and concise response.

    User input: "{user_input}"

    Key information:
    """

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_input}
    ]

    response = chat_model.generate_short_response(
        messages,
    )

    return response.message.content[0].text if response else None

# TODO: Revisit whether both extract_context_info and extract_key_info are necessary
def extract_context_info(formatted_history: list, user_input: str) -> str:
    """
    Extracts the context information from the chat history and user input.
    """

    system_messages = [msg['message'] for msg in formatted_history if msg['role'] == 'system']
    summary = next((msg for msg in system_messages if msg.startswith("Conversation summary:")), None)
    
    key_info = extract_key_info(user_input)
    
    context = []
    if summary:
        context.append(f"Conversation summary: {summary.split(':', 1)[1].strip()}")
    if key_info:
        context.append(f"Key information: {key_info}")
    
    return " | ".join(context) if context else None

# TODO: Redo confidence logic and methodology--it's currently overconfident in its response
def parse_agent_response(response: str) -> tuple:
    """
    Parses the response from the model to determine the agent type and confidence level.
    """
    agent_match = re.match(r'^(\w+)(?:\s*:\s*(.*))?$', response.strip(), re.IGNORECASE)
    if not agent_match:
        return 'general', 0.5  # Default to general with low confidence if no match

    agent_type = agent_match.group(1).lower()
    reasoning = agent_match.group(2) if agent_match.group(2) else ""

    if not reasoning:
        confidence = 0.6
    else:
        confidence = min(0.6 + (len(reasoning) / 100), 0.9)
        if re.search(r'\b(certain|sure|confident|definitely)\b', reasoning, re.IGNORECASE):
            confidence = min(confidence + 0.1, 0.95)
        if re.search(r'\b(unsure|maybe|possibly|not certain)\b', reasoning, re.IGNORECASE):
            confidence = max(confidence - 0.1, 0.4)

    return agent_type, confidence

def format_chat_history(chat_history: list) -> list:
    """Formats the chat history for processing."""
    return [
        {"role": msg['role'].lower(), "content": msg['message'] if 'message' in msg else msg['content']}
        for msg in chat_history[-5:]  # Only consider the last 5 messages for context
    ]

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


def output_with_citations(output: str, citations: dict) -> str:
    """
    Enhances the output string with inline citations that link directly to the URLs.
    
    :param output_data: A dictionary containing 'response' and 'citations'
    :return: Enhanced output string with inline citations linking to URLs
    """
    
    url_dict = {}
    current_number = 1

    # Sort citations by their end position in descending order
    sorted_citations = sorted(citations, key=lambda x: x.end, reverse=True)

    for citation in sorted_citations:
        urls = set()
        if citation.sources:
            for source in citation.sources:
                if hasattr(source, 'tool_output') and 'documents' in source.tool_output:
                    documents = source.tool_output['documents']
                    try:
                        documents_list = json.loads(documents)
                        for doc in documents_list:
                            if 'data' in doc and 'url' in doc['data']:
                                urls.add(doc['data']['url'])
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON: {documents}")

        citation_links = []
        for url in urls:
            if url not in url_dict:
                url_dict[url] = current_number
                current_number += 1
            num = url_dict[url]
            citation_links.append(f'<a href="{url}" class="citation-link" target="_blank" rel="noopener noreferrer"><span class="citation">{num}</span></a>')
        
        citation_marker = ''.join(sorted(citation_links))
        output = output[:citation.end] + citation_marker + output[citation.end:]

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
    
    return formatted_output