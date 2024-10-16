from utils import logger
import json
import re

def sanitize_json_string(json_string):
    # Remove any leading/trailing whitespace
    json_string = json_string.strip()
    
    # Ensure the string starts and ends with curly braces
    if not json_string.startswith('{'):
        json_string = '{' + json_string
    if not json_string.endswith('}'):
        json_string = json_string + '}'
    
    # Replace single quotes with double quotes (except within string values)
    json_string = re.sub(r"(?<!\\)'", '"', json_string)
    
    # Ensure all keys are in double quotes
    json_string = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_string)
    
    return json_string

def parse_reflexion_response(response_text):
    try:
        # First, try parsing as-is
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try sanitizing and parsing again
        sanitized = sanitize_json_string(response_text)
        try:
            return json.loads(sanitized)
        except json.JSONDecodeError:
            # If it still fails, log the error and return a default structure
            logger.error(f"Failed to parse reflexion response: {response_text}")
            return {
                "satisfactory_response": False,
                "old_response": "",
                "critique": "Failed to parse the response",
                "old_tool_plan": [],
                "new_tool_plan": []
            }
