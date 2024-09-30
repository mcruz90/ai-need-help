from config import Config, cohere_client
import logging

logger = logging.getLogger(__name__)

class ChatModel:
    def __init__(self):
        self.client = cohere_client
        self.model_name = Config.COHERE_MODEL

    def generate_response(self, messages: list) -> dict:
        response = self.client.chat(
            messages=messages,
            model=self.model_name
        )
        return response
    
    def generate_short_response(self, messages: list) -> dict:
        response = self.client.chat(
            messages=messages,
            model=self.model_name,
            max_tokens=50,
            temperature=0.3
        )
        return response
    
    def generate_response_with_tools(self, messages: list, tools: list) -> dict:

        response = self.client.chat(
            messages=messages,
            model=self.model_name,
            tools=tools
        )

        return response

# Create an instance of the ChatModel
chat_model = ChatModel()