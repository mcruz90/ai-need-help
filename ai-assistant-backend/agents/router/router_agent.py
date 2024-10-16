from llm_models.chat import chat_model
from agents.router.agents_list import AGENTS
from agents.router.helper_functions import extract_key_info, parse_agent_response, enhance_output_with_citations, format_chat_history, output_with_citations
from reflexion.reflexion import router_reflexion

import asyncio
from httpx import TimeoutException
from typing import TypedDict, Literal

import logging

logger = logging.getLogger(__name__)

class HandlerResponse(TypedDict):
    role: Literal["assistant"]
    content: str
    agent_type: str

def generate_preamble(agents: dict, previous_agent_type: str = None, context_info: str = None) -> str:
    agent_descriptions = "\n".join([f"- {agent}: {info['description']}" for agent, info in agents.items()])
    return f"""
    You are an expert router agent responsible for determining which specialized agent can best respond to a given user query. Your role is to analyze the query, context, and chat history, then select the most appropriate agent based on their specializations and the query's requirements.

    Available agents:
    {agent_descriptions}

    Previous agent:
    {previous_agent_type if previous_agent_type else 'None'}

    Context:
    {context_info if context_info else 'No additional context'}

    Instructions:
    1. Carefully analyze the user's query, chat history, and any provided context.
    2. Consider the following factors when selecting an agent:
    - Query topic and subject matter
    - Complexity and depth of the required response
    - Specific task or action requested (e.g., explanation, code generation, analysis)
    - User's implied or stated expertise level
    - Potential for multi-step or ongoing interactions
    3. Select the most suitable agent based on the analysis and the agents' specializations.
    4. Respond ONLY with the agent name and a brief explanation in this format:
        AGENT_NAME: Brief explanation of why you chose this agent.
    5. Include a confidence level (Low, Medium, High) in your selection.

    Important guidelines:
    - Use only the agent names listed above. Do not invent new agent names.
    - Route to 'general' for most factual queries, even if they involve scientific or complex topics, unless another agent is clearly more suitable.
    - Only route to 'tutor' if the user explicitly asks for a lesson, detailed step-by-step explanation, or ongoing educational support.
    - For ongoing tutoring sessions, continue routing to the 'tutor' agent unless explicitly ended or the topic significantly changes.
    - Route coding questions to 'code' unless it's about learning to code concepts (use 'tutor' for that).
    - For queries covering multiple topics, select the agent best equipped to handle the primary focus or the most complex aspect of the query.
    - If a query is ambiguous or could be handled by multiple agents, choose the one that can provide the most comprehensive response.
    - Provide a concise explanation for your choice, including your reasoning and confidence level.
    - NEVEr answer the query yourself. Your job is ONLY to select an agent.

    Remember, you are routing, not answering. Focus solely on selecting the most appropriate agent with a high degree of accuracy.

    Your agent choice from the list, including confidence level:
    """

MAX_REFLEXION_ITERATIONS = 2
MAX_CONFIDENCE_THRESHOLD = 0.95

async def router_agent(user_input: str, chat_history: list, previous_agent_type: str = None) -> HandlerResponse:
    try:
        logger.info(f"Router agent called with input: {user_input}")
        logger.info(f"Previous agent type: {previous_agent_type}")

        formatted_history = format_chat_history(chat_history)
        context_info = extract_key_info(user_input, formatted_history)
        logger.info(f"Context info: {context_info}")

        preamble = generate_preamble(AGENTS, previous_agent_type, context_info)
        
        messages = [
            {"role": "system", "content": preamble},
            *formatted_history,
            {"role": "user", "content": user_input}
        ]

        satisfactory_response_found = False
        reflexion_results = []

        for iteration in range(MAX_REFLEXION_ITERATIONS):
            agent_type_response = chat_model.generate_router_agent_response(messages)
            logger.info(f"Agent type raw response: {agent_type_response.message.content[0].text}")

            agent_type = parse_agent_response(agent_type_response.message.content[0].text)
            logger.info(f"Parsed agent type: {agent_type}")

            reflexion_result = router_reflexion(
                user_input, 
                agent_type, 
                agent_type_response.message.content[0].text, 
                {name: info['description'] for name, info in AGENTS.items()},
                context_info
            )

            if not isinstance(reflexion_result, dict):
                logger.error(f"Unexpected reflexion_result type: {type(reflexion_result)}")
                reflexion_result = {"satisfactory_response": False, "confidence_score": 0, "critique": "Error in reflexion process", "alternative_agent": None}

            reflexion_results.append(reflexion_result)

            logger.info(f"Reflexion result: {reflexion_result}")

            satisfactory_response = reflexion_result.get("satisfactory_response", False)
            confidence_score = float(reflexion_result.get("confidence_score", 0))

            logger.info(f"Loop condition: satisfactory_response={satisfactory_response}, confidence_score={confidence_score}")
            logger.info(f"Loop break decision: {(satisfactory_response and confidence_score > 0.7) or confidence_score > 0.9}")

            if confidence_score >= MAX_CONFIDENCE_THRESHOLD:
                logger.info(f"Maximum confidence threshold reached. Breaking loop.")
                satisfactory_response_found = True
                break

            if (satisfactory_response and confidence_score > 0.7) or confidence_score > 0.9:
                satisfactory_response_found = True
                logger.info(f"Satisfactory response found at iteration {iteration + 1}. Breaking loop.")
                break
            else:
                logger.info(f"Reflexion iteration {iteration + 1}: Routing decision unsatisfactory. Attempting to improve.")

                new_context = f"""
                The previous routing decision was deemed unsatisfactory.
                Critique: {reflexion_result['critique']}
                Confidence Score: {reflexion_result['confidence_score']}
                Suggested alternative agent: {reflexion_result['alternative_agent'] or 'None'}

                Please reconsider the routing decision based on this feedback.
                """

                messages.append({"role": "system", "content": new_context})
                messages.append({"role": "user", "content": user_input})

        if not satisfactory_response_found:
            logger.warning("Max iterations reached without satisfactory response. Using highest-scoring result.")
            selected_agent = max(reflexion_results, key=lambda x: x['confidence_score'])['alternative_agent'] or agent_type
        else:
            selected_agent = reflexion_result.get("alternative_agent") or agent_type

        if selected_agent.lower() not in AGENTS:
            logger.warning(f"Selected agent '{selected_agent}' not found in AGENTS. Defaulting to 'general'.")
            selected_agent = 'general'

        logger.debug(f"Final selected agent: {selected_agent}")
        handler_response = await handle_query(user_input, formatted_history, selected_agent, context_info)

        if not all(key in handler_response for key in ["role", "content", "agent_type"]):
            logger.warning(f"Invalid handler_response structure. Falling back to general agent.")
            handler_response = {
                "role": "assistant",
                "content": "I apologize, but I couldn't process your request properly. Here's what I understand: " + agent_type_response.message.content[0].text,
                "agent_type": "general"
            }

        handler_response["reflexion_result"] = reflexion_result
        handler_response["iterations"] = iteration + 1

        return handler_response

    except TimeoutException:
        logger.error("Timeout occurred while calling the Cohere API")
        return {"role": "assistant", "content": "I'm sorry, but I'm having trouble processing your request right now. Could you please try again in a moment?", "agent_type": "router"}
    except Exception as e:
        logger.error(f"An error occurred in router_agent: {str(e)}", exc_info=True)
        return {"role": "assistant", "content": "I apologize, but an error occurred while processing your request. Please try again later.", "agent_type": "error"}
    
async def handle_query(user_input: str, formatted_history: list, agent_type: str, context_info: str = None):
    try:
        logger.info(f"Handling query with {agent_type} agent")
        return await handle_agent_response(agent_type, user_input, formatted_history, context_info)
    except Exception as e:
        logger.error(f"Error in handle_query: {str(e)}", exc_info=True)
        return {"role": "assistant", "content": f"An error occurred while processing your query: {str(e)}", "agent_type": "error"}

async def handle_agent_response(agent_type: str, user_input: str, formatted_history: list, context_info: str) -> dict:
    try:
        if agent_type == 'calendar':
            logger.info(f"Calling calendar agent")
            result = AGENTS[agent_type]["tool"](user_input, formatted_history)
            return {"role": "assistant", "content": result["response"], "agent_type": agent_type}
        elif agent_type == 'general':
            logger.info(f"Calling general agent")
            result = await AGENTS[agent_type]["tool"](user_input, formatted_history, context_info)
            
             # Check if the tool is a coroutine function (async)
            if asyncio.iscoroutinefunction(AGENTS[agent_type]["tool"]):
                result = await AGENTS[agent_type]["tool"](
                    user_input, 
                    formatted_history,
                    context_info,
                )
            else:
                # If it's not async, call it synchronously
                result = AGENTS[agent_type]["tool"](
                    user_input, 
                    formatted_history,
                    context_info,
                )

            # If no citations or citations is None, just use the response as is
            cited_output = result["response"]

            logger.info(f"model response: {result['response']}")
             # Now that we've awaited the result, we can safely access it
            if isinstance(result, dict):
                output = result.get("response", "No response from model")
                citations = result.get("citations", [])
                if isinstance(citations, list) and citations:
                    cited_output = output_with_citations(output, citations)
                else:
                    cited_output = output
                return {"role": "assistant", "content": cited_output, "agent_type": agent_type}
            else:
                return {"role": "assistant", "content": "No response from model", "agent_type": agent_type}

        else:
            # Check if the tool is a coroutine function (async)
            if asyncio.iscoroutinefunction(AGENTS[agent_type]["tool"].invoke):
                result = AGENTS[agent_type]["tool"].invoke({
                    "input": user_input, 
                    "chat_history": formatted_history,
                    "router_context": context_info,
                })
            else:
                # If it's not async, call it synchronously
                result = AGENTS[agent_type]["tool"].invoke({
                    "input": user_input, 
                    "chat_history": formatted_history,
                    "router_context": context_info,
                })
            if isinstance(result, dict):
                output = result.get("output") or result.get("response") or str(result)
                enhanced_output = enhance_output_with_citations(output, result.get("citations", []))
                return {"role": "assistant", "content": enhanced_output, "agent_type": agent_type}
            else:
                return {"role": "assistant", "content": str(output), "agent_type": agent_type}
    except Exception as e:
        logger.error(f"Error in handle_agent_response: {str(e)}", exc_info=True)
        return {"role": "assistant", "content": f"An error occurred while processing your query: {str(e)}", "agent_type": "error"}
