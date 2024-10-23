from typing import List, Dict, Any
from llm_models.chat import chat_model
from utils.utils import logger
from agents.triage.triage_utils import StreamHandler


async def code_agent(user_message: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
    try:
        """
        Generate a response to the user's message related to code generation or critique.
        """

        logger.info(f"Calling code_agent to generate a response to the user's message")

        # Step 1: System Prompt to guide the agent
        system_prompt = """
        ## Task & Context
        You are an expert code generation agent designed to generate a response to the user's message.
        You may be asked to generate code for a variety of languages and use cases, as well as
        critique code written by the user and provide suggestions for improvement.

        ## Style Guide
        Unless specified otherwise, you should directly answer using LaTeX and markdown syntax to produce and format your code, making sure to include comments and explanations where necessary.

        ## Code Generation
        When generating code, you should follow the following structure:
        ```
        <language>
        <code>
        ```

        ## Example Code Generation Response

        user: What's an example function to add two numbers in golang?
        assistant: ```go
        package main

        import "fmt"

        // add sums two numbers and returns the result
        func add(a, b int) int {
            return a + b
        }
        
        ```
        ## Code Critique
        When critiquing code, you should follow the following structure:
        
        <critique>

        ```
        <language>
        <improvedcode>
        ```

        ## Example Code Critique Response

        user: What's wrong with this code?
        ```go
        package main

        import "fmt"
        
        ```
        assistant: The code is missing the main function.
        ```go
        package main

        import "fmt"

        func main() {
            fmt.Println("Hello, World!")
        }
        ```
        """

        # Append the system prompt, chat history, and user's queries to the messages list to pass to the LLM
        messages = [
            {"role": "system", "content": system_prompt},
            *chat_history,
            {"role": "user", "content": user_message},
        ]

        # Step 2: Generate the response
        response_stream = await chat_model.generate_streaming_response(messages, tools=None)

        full_response = ""
        # Step 3: Stream the response back to the triage agent
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
        logger.error(f"Error in code_agent: {e}")
        raise e
