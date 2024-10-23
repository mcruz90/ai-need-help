from prometheus_client import Counter, Histogram, Gauge
import functools
from typing import AsyncIterator, Any

# LLM-specific metrics
LLM_REQUESTS = Counter('llm_requests_total', 'Total number of LLM requests', ['function_name'])
LLM_REQUEST_DURATION = Histogram('llm_request_duration_seconds', 'Duration of LLM requests', ['function_name'])
LLM_INPUT_TOKENS = Gauge('llm_input_tokens', 'Number of input tokens', ['function_name'])
LLM_OUTPUT_TOKENS = Gauge('llm_output_tokens', 'Number of output tokens', ['function_name'])

def track_llm_metrics(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        function_name = func.__name__
        
        # Increment the request counter
        LLM_REQUESTS.labels(function_name=function_name).inc()
        
        # Use the Histogram to track duration
        with LLM_REQUEST_DURATION.labels(function_name=function_name).time():
            result = await func(*args, **kwargs)
        
        # Check if the result is an async generator
        if isinstance(result, AsyncIterator):
            async for item in result:
                # Assuming each item has usage data
                if hasattr(item, 'usage') and hasattr(item.usage, 'tokens'):
                    LLM_INPUT_TOKENS.labels(function_name=function_name).set(item.usage.tokens.input_tokens)
                    LLM_OUTPUT_TOKENS.labels(function_name=function_name).set(item.usage.tokens.output_tokens)
            return result
        else:
            # Update token usage for non-generator results
            if hasattr(result, 'usage') and hasattr(result.usage, 'tokens'):
                LLM_INPUT_TOKENS.labels(function_name=function_name).set(result.usage.tokens.input_tokens)
                LLM_OUTPUT_TOKENS.labels(function_name=function_name).set(result.usage.tokens.output_tokens)
        
        return result
    
    return wrapper
