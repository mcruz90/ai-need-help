from agents.BaseAgent.base_agent import BaseAgent
from typing import List, Dict, Any, AsyncGenerator
from llm_models.chat import chat_model
from utils.utils import logger

class SearchAgent(BaseAgent):
    def __init__(self, tools: List[Dict[str, Any]], functions_map: Dict[str, Any], name: str = "Search Agent"):
        self.messages = []
        super().__init__(tools, functions_map, name)

    def initialize_messages(self, chat_history: List[Dict[str, str]], query: str) -> List[Dict[str, Any]]:

        system_prompt = f"""
        ## Task & Context
        You are an expert search agent designed to search for information relevant to the user's query.
        You will be given a user query and must use the available tools to search and retrieve information relevant to the user's query.
        
        ## Instructions
        1. Analyze the user's query and determine the main topic and any subtopics.
        2. Identify the user's intent (e.g., seeking information, comparing options, finding recent events).
        3. Note any specific requirements or constraints.
        4. Judge the complexity level (simple, moderate, or complex) of the query and adjust your strategy accordingly.
        5. Generate search keywords and formulate search queries based on the complexity level.
        6. Specify search parameters and suggest sources to prioritize.
        7. Ensure your strategy is tailored to the complexity level of the query while finding the most relevant, accurate, and up-to-date information to address the user's query effectively.

        ## Search Parameters Strategy
        After determining the complexity level of the query, you will use the following strategy to determine the search parameters:
            - Simple: Use broad search parameters to quickly gather information.
            - Moderate: Use specific search parameters to refine search results.
            - Complex: Use advanced search parameters to gather comprehensive information, including specific dates, terms, and entities. You may need to make multiple tool calls to gather all the necessary information.
        """

        self.messages = [
            {"role": "system", "content": system_prompt},
            *chat_history,
            {"role": "user", "content": query}
        ]

    async def analyze_tool_calls(self, query: str) -> str:
        """
        Extracts key information from the user's input and chat history to help inform the final response.
        """
        logger.info(f"Starting analyze_tool_calls for query: {query[:50]}...")

        prompt = f"""
        ## Task & Context
        Analyze the user's input and resulting tool calls in the provided chat history to
        extract key information to help inform the final response.

        User Query: "{query}"
        Chat history: "{self.messages}"

        ## Instructions
        Focus on analyzing the following:
        - Does the information retrieved answer all aspects of the user's query?
        - Was there any missing information that should have been retrieved in the tool calls?
        - Was there any information in the tool calls that is not relevant to the query?
        - Was there any information in the tool calls that is unclear or confusing?
        - Was there any information in the tool calls that is outdated?
        - Are the 5 W's (Who, What, When, Where, Why) applicable to the query covered in the tool calls?

        Do NOT attempt to answer the query. Instead, provide a brief, structured summary of the key points that will help inform the final response.

        ## Output
        Provide your analysis in the following format, but be concise and to the point:
        - Summary: A brief, structured summary of the key points.
        - Missing Information: A list of missing information that should have been retrieved in the tool calls.
        - Outdated Information: A list of outdated information that should have been retrieved in the tool calls.
        - Unclear Information: A list of unclear information that should have been retrieved in the tool calls.
        - Irrelevant Information: A list of irrelevant information that should have been retrieved in the tool calls.
        - Possible Improvements: A list of possible improvements to the tool calls.
        - Confidence Score: Rate the confidence in the analysis on a scale of 0 to 1.
        """

        context_messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            response = await chat_model.generate_response(context_messages)
            
        except Exception as e:
            logger.error(f"Error extracting key info: {e}")
            return "Error extracting key info"

        return response.message.content[0].text

    async def generate_final_response(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:

        tool_call_analysis = await self.analyze_tool_calls(query)

        updated_instructions =  f"""
                ## Task & Context
                You have just received the results of your tool calls, and will now be asked to provide a final response to the user.
                Your final response must be based on the tool results provided and the analysis of the tool calls.

                ## User Query
                {query}

                ## Tool Call Analysis
                {tool_call_analysis}

                ## Instructions
                The tool results contain the answer to the user's question. Your task is to use this information to generate a final response to the user query.
                If the tool calls were not able to provide any relevant information, you should state that you are not able to answer the query and ask for more information or if you are able to help with something else.
                Make sure that your final response addresses all aspects of the user's query. Given the tool call analysis, you should adjust your response
                to address any aspect of the user's query that was missed as a result of the tools not being able to find the information.

                ## Style Guidelines
                - Be concise and to the point if the complexity of the user's request is low.
                - Be detailed and comprehensive if the complexity of the user's request is high.
                - Be kind and helpful, and maintain a professional tone.
                """
        
        self.messages.append({"role": "assistant", "content": updated_instructions})

        response_stream = await chat_model.generate_streaming_response(
            messages=self.messages,
            tools=self.tools
        )

        return response_stream