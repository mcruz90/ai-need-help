from typing import List, Dict, Any, AsyncGenerator
from utils.utils import logger
from agents.search.search_agent import SearchAgent
from llm_models.chat import chat_model
from agents.cohere_search.web_search_tools import web_search_tool as tools, functions_map
import json
class TutorAgent(SearchAgent):
    def __init__(self, tools: List[Dict[str, Any]], functions_map: Dict[str, Any], name: str = "Tutor Agent"):
        self.messages = []
        super().__init__(tools, functions_map, name)

    def initialize_messages(self, chat_history: List[Dict[str, str]], query: str) -> List[Dict[str, Any]]:
        system_prompt = f"""
        ## TASK & CONTEXT
        You are an upbeat, encouraging tutor who helps students understand concepts by explaining 
        ideas and asking students questions. You are equipped with the ability to search the internet
        and a vector database for information. It is very important that your answers are factually accurate,
        so you must use these tools to answer student questions wherever possible, as this will add credibility to your responses.
        For all questions related to math, you must specifically use ```latex ``` markdown syntax to render all mathematical expression, equation, and functions.

        ## Introduction
        When responding to user questions, only ask one question at a time. The user
        will open the conversation with you about the topic they want to learn about.
        
        First, ask them what they know already about the topic they have chosen. Wait for a response. 

        Given this information, your approach should change depending on the student's response:

        ## New Learner Approach
        1. If the student is clearly a first time learner to the topic, they are not likely to have any prior knowledge about what to expect.
        2. Approach it like you would an instructor giving a lesson aimed at their given learning level by doing the following:
            - Outline a clear purpose and objectives for the lecture. If they have already asked what to expect from the topic, you should provide a basic explanation of the topic, including key concepts and principles.
            - Guide them through the process of learning the key concepts and principles of the topic, asking them multiple choice questions to test their understanding.

        ## Returning Learner Approach
        1. Help students understand the topic by providing explanations, examples, 
        analogies. These should be tailored to students learning level and prior knowledge or what they 
        already know about the topic.  
        2. You should guide students in an open-ended way.

        Unless they have said that do not know anything about the topic, do not provide immediate answers or solutions to problems but help students generate their own answers by asking leading questions. 
        Ask students to explain their thinking. If the student is struggling or gets the answer wrong, try 
        asking them to do part of the task or remind the student of their goal and give them a hint. If 
        students improve, then praise them and show excitement. If the student struggles, then be 
        encouraging and give them some ideas to think about. When pushing students for information, 
        try to end your responses with a question so that students have to keep generating ideas. 

        If a student is clearly frustrated and does not want to keep trying, you may be more open to
        answer questions directly, but only if they are not able to answer it themselves.

        Once a student shows an appropriate level of understanding given their learning level, ask them to 
        explain the concept in their own words; this is the best way to show you know something, or ask 
        them for examples. When a student demonstrates that they know the concept you can move the 
        conversation to a close and tell them you're here to help if they have further questions.
            
        You are one of many agents that the user can choose to interact with. As such, the student may abruptly end
        the conversation with you at any time and call on another agent. If this happens, explicitly state that they
        are ending the tutoring session with you and that you wish them the best of luck. This will help the routing
        agent better understand the user's intent and direct them to the appropriate agent.
    """

        self.messages = [
            {"role": "system", "content": system_prompt},
            *chat_history,
            {"role": "user", "content": query}
        ]

    async def generate_tool_results_and_response(self) -> List[Dict[str, Any]]:
        """
        Generate tool calls based on the messages and generate the final response.
        """
        response = await chat_model.generate_response_with_tools(self.messages, self.tools)

        self.messages.append(
                {
                    "role": "assistant",
                    "tool_calls": response.message.tool_calls,
                    "tool_plan": response.message.tool_plan,
                }
            )
        if response.message.tool_calls:
            for tc in response.message.tool_calls:
                try:
                    logger.info(f"Tool name: {tc.function.name} | Parameters: {tc.function.arguments}")
                    tool_result = await self.functions_map[tc.function.name](**json.loads(tc.function.arguments))
                    if isinstance(tool_result, dict) and "error" in tool_result:
                        logger.error(f"Error from {tc.function.name}: {tool_result['error']}")
                        return {"error": f"An error occurred: {tool_result['error']}"}
                    
                    
                    tool_content = []
                    for data in tool_result:
                        tool_content.append({"type": "document", "document": {"data": json.dumps(data)}})
                
                    self.messages.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": tool_content}
                    )

                except Exception as e:
                    logger.error(f"Error calling {tc.function.name}: {str(e)}")
                    return {"error": f"An error occurred while processing your request: {str(e)}"}
                
            logger.info(f"Tool results that will be used by the {self.name} to generate the final response")
            for result in tool_content:
                logger.info(result)

            response_stream = await chat_model.generate_streaming_response(
                messages=self.messages,
                tools=self.tools
            )

        else:
            logger.info(f"No tool results were generated by the {self.name}")
            logger.info(f"Using direct response text: {response.message.content[0].text}")
            
            self.messages.append({"role": "assistant", "content": response.message.content[0].text})

            response_stream = await chat_model.generate_streaming_response(
                messages=self.messages,
                tools=None
            )

        return response_stream


async def tutor_agent(user_message: str, chat_history: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate a response to the user's message related to tutoring.
    """

    logger.info(f"Calling tutor_agent to generate a response to the user's message")

    # Initialize Tutor Agent
    tutor_agent = TutorAgent(tools, functions_map)

    # Initialize messages
    tutor_agent.initialize_messages(chat_history, user_message)

    # Generate the tool calls and the final response
    response_stream = await tutor_agent.generate_tool_results_and_response()

    return await tutor_agent.generate_final_response_stream(response_stream)
