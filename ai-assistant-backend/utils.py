import json
from fastapi import HTTPException
from config import cohere_client
import re

def process_events(messages: list):
    for msg in messages:
        if msg.role == "Events":
            return json.loads(msg.content)
    return {}

def handle_exception(error):
    print(f"Error: {error}")
    raise HTTPException(status_code=500, detail=str(error))

def summarize_conversation(history):
    conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    summary = cohere_client.summarize(text=conversation, length='short', format='paragraph', model='command')
    return summary.summary

def extract_key_info(message):
    """
    Extracts key information from the message using simple keyword matching.
    """
    key_words = ["date", "time", "location", "person", "event"]
    extracted = []
    for word in key_words:
        if word in message.lower():
            extracted.append(word)
    return ", ".join(extracted) if extracted else None

# utils.py
def code_block_formatter(raw_output: str) -> str:
    """
    Processes the raw output from the model and enhances it for frontend rendering.
    Ensures that code blocks preserve their formatting with proper line breaks.
    """
    
    # Example: Ensuring that code blocks have proper backticks and line breaks
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
    Enhances the output string with superscript citations that link directly to the URLs.
    
    :param output: The original output string from the model
    :param citations: List of citation objects
    :return: Enhanced output string with superscript citations linking to URLs
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
            citation_links.append(f'<a href="{url}" class="citation-link" target="_blank" rel="noopener noreferrer">[{num}]</a>')
        
        citation_marker = f"<sup>{' '.join(sorted(citation_links))}</sup>"
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
        if line.startswith('#') and line.endswith('</sup>'):
            formatted_lines.append('')
    
    # Join the formatted lines
    formatted_output = '\n'.join(formatted_lines).strip()
    
    # Remove <br> tags after </sup>
    formatted_output = formatted_output.replace('</sup><br>', '</sup>')
    
    return formatted_output