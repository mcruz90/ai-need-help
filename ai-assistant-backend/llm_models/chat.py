import asyncio
from typing import AsyncGenerator
from config.config import Config, cohere_client
from utils import logger

class ChatModel:
    def __init__(self):
        self.client = cohere_client
        self.model_name = Config.COHERE_MODEL

    async def generate_streaming_response(self, messages, tools):
        return self.client.chat_stream(
            model=self.model_name,
            messages=messages,
            tools=tools
        )


    def generate_router_agent_response(self, messages):
       try:
           response = self.client.chat(
               messages=messages,
               temperature=0.2,
               model=self.model_name
           )
           return response
       except Exception as e:
           logger.error(f"Error generating router agent response: {str(e)}")
           raise

    async def generate_response(self, messages):
       try:
           response = await self.client.chat(
               messages=messages,
               model=self.model_name
           )
           return response
       except Exception as e:
           logger.error(f"Error generating response: {str(e)}")
           raise

    def generate_seeded_response(self, messages, seed):
       try:
           response = self.client.chat(
               messages=messages,
               model=self.model_name,
               seed=seed
           )
           return response
       except Exception as e:
           logger.error(f"Error generating response: {str(e)}")
           raise
    
    def generate_json_response(self, messages: list) -> dict:
        response = self.client.chat(
            messages=messages,
            model=self.model_name,
            response_format={ "type": "json_object" }
        )
    
    def generate_short_response(self, messages: list) -> dict:
        response = self.client.chat(
            messages=messages,
            model=self.model_name,
            max_tokens=50,
            temperature=0.3
        )
        return response
    
    async def generate_response_with_tools(self, messages: list, tools: list) -> dict:

        response = await self.client.chat(
            messages=messages,
            model=self.model_name,
            tools=tools
        )

        return response

# Create an instance of the ChatModel
chat_model = ChatModel()