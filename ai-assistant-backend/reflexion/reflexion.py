import json
from typing import List, Dict, Any
from config.config import cohere_client as client, Config
from llm_models.embed import get_embeddings
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from utils.utils import logger

async def generate_text(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    response = await client.chat(messages=messages, model=Config.COHERE_MODEL)
    return response.message.content[0].text

class ModelEvaluator:
    async def evaluate(self, user_input: str, model_response: str, tool_plan: List[str], context_info: str) -> Dict[str, Any]:
        evaluation_prompt = f"""
        <prompt>
            <task>Evaluate the following response</task>
            <input>
                <user_query>{user_input}</user_query>
                <model_response>{model_response}</model_response>
                <tool_plan>{tool_plan}</tool_plan>
                <context_info>{context_info}</context_info>
            </input>
            
            <evaluation_criteria>
                <criterion>Relevance to the user's query</criterion>
                <criterion>Accuracy of the information</criterion>
                <criterion>Completeness of the response</criterion>
                <criterion>Appropriateness of the tool plan</criterion>
                <criterion>Consideration of the context information</criterion>
            </evaluation_criteria>
            
            <output_requirements>
                <requirement>
                    <type>Qualitative assessment</type>
                    <description>A detailed evaluation considering all criteria</description>
                </requirement>
                <requirement>
                    <type>Numerical score</type>
                    <description>A score between 0 and 1 (0 being completely unsatisfactory, 1 being perfect)</description>
                </requirement>
                <requirement>
                    <type>Areas for improvement</type>
                    <description>Specific suggestions for enhancing the response, if any</description>
                </requirement>
                <requirement>
                    <type>New tool plan</type>
                    <description>Suggestions for a new tool plan if the current one is inadequate</description>
                </requirement>
            </output_requirements>
            
            <response_format>
                <format>JSON</format>
                <structure>
                    <key>
                        <name>score</name>
                        <type>float</type>
                    </key>
                    <key>
                        <name>critique</name>
                        <type>string</type>
                    </key>
                    <key>
                        <name>areas_for_improvement</name>
                        <type>list of strings</type>
                    </key>
                    <key>
                        <name>new_tool_plan</name>
                        <type>list of strings</type>
                        <note>Empty if current plan is adequate</note>
                    </key>
                </structure>
            </response_format>
        </prompt>
        """
        evaluation_response = await generate_text(evaluation_prompt)
        
        try:
            evaluation_json = json.loads(evaluation_response)
            return evaluation_json
        except json.JSONDecodeError:
            logger.error("Failed to parse evaluation response as JSON")
            return {
                "score": 0.5,
                "critique": "Error in generating evaluation",
                "areas_for_improvement": ["Unable to generate proper evaluation"],
                "new_tool_plan": []
            }

class MathematicalEvaluator:
    def __init__(self):
        self.cached_embeddings = {}

    def get_embedding(self, text: str) -> List[float]:
        if text not in self.cached_embeddings:
            self.cached_embeddings[text] = get_embeddings([text])[0]
        return self.cached_embeddings[text]

    def embedding_similarity(self, text1: str, text2: str) -> float:
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        return cosine_similarity([emb1], [emb2])[0][0]

    def context_similarity(self, context_info: str, model_response: str) -> float:
        return self.embedding_similarity(context_info, model_response)

    def length_appropriateness(self, query: str, response: str) -> float:
        query_embedding = self.get_embedding(query)
        response_embedding = self.get_embedding(response)
        
        similarity = cosine_similarity([query_embedding], [response_embedding])[0][0]
        
        length_ratio = len(response.split()) / len(query.split())
    
        if length_ratio < 0.5:
            length_score = length_ratio * 2  # Linear increase from 0 to 1 as ratio goes from 0 to 0.5
        elif length_ratio > 2:
            length_score = max(0, 2 - (length_ratio - 2) / 3)  # Linear decrease from 1 to 0 as ratio goes from 2 to 5
        else:
            length_score = 0.99  # Set to slightly less than 1 even for appropriate lengths
        
        # Combine semantic similarity and length appropriateness
        combined_score = (similarity * 0.7) + (length_score * 0.3)
    
        # Ensure the score is always less than 1
        return min(combined_score, 0.99)

    def evaluate_tool_plan(self, user_input: str, tool_plan: List[str]) -> float:
        combined_tool_plan = " ".join(tool_plan)
        
        # Generate embeddings using your function
        embeddings = get_embeddings([user_input, combined_tool_plan])
        
        # Calculate cosine similarity between embeddings
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        
        return similarity

    def evaluate(self, user_input: str, model_response: str, tool_plan: List[str], context_info: str) -> float:
        scores = []

        # Embedding-based similarity between query and response
        query_response_similarity = self.embedding_similarity(user_input, model_response)
        scores.append(query_response_similarity)

        # Context similarity (replacing BLEU score)
        context_sim = self.context_similarity(context_info, model_response)
        scores.append(context_sim)

        # Length appropriateness score
        length_score = self.length_appropriateness(user_input, model_response)
        scores.append(length_score)

        # Tool plan evaluation score
        tool_plan_score = self.evaluate_tool_plan(user_input, tool_plan)
        scores.append(tool_plan_score)

        # You can adjust the weights of different scores if needed
        weights = [0.3, 0.2, 0.2, 0.3]  # Example weights
        weighted_scores = [score * weight for score, weight in zip(scores, weights)]

        final_score = np.sum(weighted_scores)

        return final_score

    def get_detailed_scores(self, user_input, model_response, tool_plan, context_info):
        return {
            "query_response_similarity": self.embedding_similarity(user_input, model_response),
            "context_relevance": self.context_similarity(context_info, model_response),
            "length_appropriateness": self.length_appropriateness(user_input, model_response),
            "tool_plan_relevance": self.evaluate_tool_plan(user_input, tool_plan)
        }

class HybridEvaluator:
    def __init__(self, model_evaluator: ModelEvaluator, mathematical_evaluator: MathematicalEvaluator, alpha: float = 0.7, satisfaction_threshold: float = 0.75):
        self.model_evaluator = model_evaluator
        self.mathematical_evaluator = mathematical_evaluator
        self.alpha = alpha
        self.satisfaction_threshold = satisfaction_threshold

    def evaluate(self, user_input: str, model_response: str, tool_plan: List[str], context_info: str) -> Dict[str, Any]:
        try:
            model_result = self.model_evaluator.evaluate(user_input, model_response, tool_plan, context_info)
            math_score = self.mathematical_evaluator.evaluate(user_input, model_response, tool_plan, context_info)
            math_detailed_scores = self.mathematical_evaluator.get_detailed_scores(user_input, model_response, tool_plan, context_info)
            
            combined_score = self.alpha * model_result['score'] + (1 - self.alpha) * math_score
            
            rounded_score = round(combined_score, 2)  # Round to two decimal places
            
            return {
                'score': combined_score,
                'is_satisfactory': rounded_score >= self.satisfaction_threshold,
                'model_evaluation': model_result,  # This now includes critique, areas_for_improvement, and new_tool_plan
                'mathematical_evaluation': {
                    'score': math_score,
                    'detailed_scores': math_detailed_scores,
                    'summary': f"""
                    Mathematical Evaluation:
                    - Query-Response Similarity: {math_detailed_scores['query_response_similarity']:.2f}
                    - Context Relevance: {math_detailed_scores['context_relevance']:.2f}
                    - Length Appropriateness: {math_detailed_scores['length_appropriateness']:.2f}
                    - Tool Plan Relevance: {math_detailed_scores['tool_plan_relevance']:.2f}
                    """
                }
            }
        except Exception as e:
            logger.error(f"Error in HybridEvaluator: {e}")
            return {
                'score': 0.5,
                'is_satisfactory': False,
                'model_evaluation': {
                    'score': 0.5,
                    'critique': "Error in model evaluation",
                    'areas_for_improvement': ["Unable to generate proper evaluation"],
                    'new_tool_plan': []
                },
                'mathematical_evaluation': {
                    'score': 0.5,
                    'detailed_scores': {},
                    'summary': "Error in mathematical evaluation"
                }
            }

class Memory:
    def __init__(self):
        self.long_term_memory: List[Dict[str, Any]] = []
        self.memory_embeddings: np.ndarray = np.array([])

    def append_reflection(self, reflection: Dict[str, Any]) -> None:
        def default(obj):
            if isinstance(obj, np.generic):
                return obj.item()
            raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

        embedding = get_embeddings([json.dumps(reflection, default=default)])[0]
        if self.memory_embeddings.size == 0:
            self.memory_embeddings = np.array([embedding])
        else:
            self.memory_embeddings = np.vstack([self.memory_embeddings, embedding])
        self.long_term_memory.append(reflection)

    def get_relevant_memories(self, query: str, n: int = 5) -> List[Dict[str, Any]]:
        if not self.long_term_memory:
            return []
        query_embedding = get_embeddings([query])[0]
        cosine_similarities = cosine_similarity([query_embedding], self.memory_embeddings)[0]
        top_indices = np.argsort(cosine_similarities)[-n:][::-1]
        return [self.long_term_memory[i] for i in top_indices]

def get_batch_embeddings(texts: List[str]) -> List[List[float]]:
    return get_embeddings(texts)


class Reflexion:
    def __init__(self, evaluator: HybridEvaluator, memory: Memory):
        self.evaluator = evaluator
        self.memory = memory

    async def reflect(self, user_input: str, model_response: str, tool_plan: List[str], context_info: str) -> Dict[str, Any]:
        try:
            logger.info(f"Starting reflection for user input: {user_input}")
            evaluation_result = await self.evaluator.evaluate(user_input, model_response, tool_plan, context_info)
            logger.info(f"Evaluation result: {evaluation_result}")
            
            relevant_memories = self.memory.get_relevant_memories(user_input)
            logger.info(f"Retrieved {len(relevant_memories)} relevant memories")

            def str_to_bool(value: str) -> bool:
                return str(value).lower() in ('true', 't', 'yes', 'y', '1')

            is_satisfactory = str_to_bool(str(evaluation_result.get('is_satisfactory', False)))
            
            reflection_result = {
                "satisfactory_response": is_satisfactory,
                "old_response": model_response,
                "critique": evaluation_result['model_evaluation']['critique'],
                "old_tool_plan": tool_plan,
                "new_tool_plan": [] if is_satisfactory else evaluation_result['model_evaluation'].get('new_tool_plan', []),
                "embedding_based_suggestions": evaluation_result['mathematical_evaluation']['summary'],
                "areas_for_improvement": [] if is_satisfactory else evaluation_result['model_evaluation'].get('areas_for_improvement', []),
                "combined_score": float(evaluation_result['score']),
                "mathematical_details": self._convert_numpy_types(evaluation_result['mathematical_evaluation']['detailed_scores'])
            }

            self.memory.append_reflection(reflection_result)
            return reflection_result

        except Exception as e:
            logger.exception(f"An error occurred during reflection: {e}")
            return {
                "satisfactory_response": False,
                "old_response": model_response,
                "critique": f"Error in generating reflection: {str(e)}",
                "old_tool_plan": tool_plan,
                "new_tool_plan": [],
                "embedding_based_suggestions": "Error in generating embedding-based suggestions",
                "areas_for_improvement": ["Unable to complete reflection process"],
                "combined_score": 0,
                "mathematical_details": {},
                "error_details": str(e)
            }

    def _convert_numpy_types(self, obj):
        if isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        return obj

async def web_search_reflexion(user_input: str, model_response: str, tool_plan: List[str], context_info: str) -> Dict[str, Any]:
    """
    This function is used to reflect on the web search response process.
    It evaluates the appropriateness and quality of the generated response for the given user query.
    
    Returns a dictionary with the following keys:
    - satisfactory_response: True if the response is appropriate and sufficient, False otherwise.
    - critique: Critique of the generated response.
    - confidence_score: Confidence score for the response quality.
    - areas_for_improvement: Suggestions for improving the response if it's unsatisfactory.
    - evaluation_details: Detailed evaluation of the response generation process.
    """
    model_evaluator = ModelEvaluator()
    mathematical_evaluator = MathematicalEvaluator()
    hybrid_evaluator = HybridEvaluator(model_evaluator, mathematical_evaluator)
    memory = Memory()
    reflexion_system = Reflexion(hybrid_evaluator, memory)
    
    prompt = f"""
    <prompt>
        Evaluate the generated response for the following user query:
        <user_query>
            {user_input}
        </user_query>
        <original_generated_response>
            {model_response}
        </original_generated_response>
        <tool_plan>
            {tool_plan}
        </tool_plan>
        <additional_context>
            {context_info}
        </additional_context>

        Your task is to determine if the generated response is appropriate and sufficient for the user's query. Consider the following:
        1. Does the response directly address the user's query?
        2. Is the information provided accurate and up-to-date?
        3. Is the response comprehensive enough for the complexity of the query?
        4. Are there any areas where the response could be improved or expanded?
        
        Provide your evaluation in the following format:
        1. Critique: Offer a brief analysis of the response quality and relevance.
        2. Confidence Score: Rate the overall quality of the response on a scale of 0 to 1.   
        3. Areas for Improvement: Suggest specific ways the response could be enhanced, if necessary.
        Based on your evaluation, determine if the response is satisfactory.
    </prompt>
    """
    
    evaluation_result = await reflexion_system.reflect(user_input, prompt, tool_plan, context_info)
    
    # Extract information from the evaluation result
    is_satisfactory = evaluation_result.get('satisfactory_response', False)
    confidence_score = evaluation_result.get('combined_score', 0.0)
    critique = evaluation_result.get('critique', '')
    areas_for_improvement = evaluation_result.get('areas_for_improvement', [])

    # Log the evaluation result for debugging
    logger.info(f"Web search evaluation result: {evaluation_result}")
    
    return {
        "satisfactory_response": is_satisfactory,
        "critique": critique,
        "confidence_score": confidence_score,
        "areas_for_improvement": areas_for_improvement,
        "evaluation_details": evaluation_result
    }

def router_reflexion(user_input: str, selected_agent: str, agent_explanation: str, available_agents: Dict[str, str], context_info: str) -> Dict[str, Any]:
    """
    This function is used to reflect on the agent selection process.
    It evaluates the appropriateness of the selected agent for the given user query.
    
    Returns a dictionary with the following keys:
    - satisfactory_response: True if the selected agent is appropriate, False otherwise.
    - critique: Critique of the agent selection decision.
    - confidence_score: Confidence score for the agent selection decision.
    - alternative_agent: Alternative agent to consider if the current selection is inappropriate.
    - original_selection: The agent that was originally selected.
    - evaluation_details: Detailed evaluation of the agent selection process.
    """
    model_evaluator = ModelEvaluator()
    mathematical_evaluator = MathematicalEvaluator()
    hybrid_evaluator = HybridEvaluator(model_evaluator, mathematical_evaluator)
    memory = Memory()
    reflexion_system = Reflexion(hybrid_evaluator, memory)
    
    prompt = f"""
    Evaluate the agent selection for the following user query:
    User Query: "{user_input}"
    Selected Agent: {selected_agent}
    Agent Explanation: {agent_explanation}
    
    Available Agents:
    {available_agents}
    
    Additional Context: {context_info}

    Your task is to determine if the selected agent is appropriate for handling this query. Consider the following:
    1. Does the selected agent's capabilities align with the user's query?
    2. Is the explanation for choosing this agent logical and comprehensive?
    3. Only suggest an alternative if the current selection is clearly inappropriate.

    Provide your evaluation in the following format:
    1. Critique: Offer a brief analysis of the agent selection decision.
    2. Confidence Score: Rate the appropriateness of the agent selection on a scale of 0 to 1.
    3. Alternative Agent (if necessary): Only suggest an alternative if the current selection is clearly inappropriate.

    Based on your evaluation, determine if the agent selection is satisfactory.
    """
    
    evaluation_result = reflexion_system.reflect(user_input, prompt, [], context_info)
    
    # Extract information from the evaluation result
    is_satisfactory = evaluation_result.get('satisfactory_response', False)
    confidence_score = evaluation_result.get('combined_score', 0.0)
    critique = evaluation_result.get('critique', '')
    alternative_agent = evaluation_result.get('alternative_agent')

    return {
        "satisfactory_response": is_satisfactory,
        "critique": critique,
        "confidence_score": confidence_score,
        "alternative_agent": alternative_agent,
        "original_selection": selected_agent,
        "evaluation_details": evaluation_result
    }


__all__ = ['ModelEvaluator', 'MathematicalEvaluator', 'HybridEvaluator', 'Memory', 'Reflexion', 'reflexion', 'router_reflexion', 'web_search_reflexion']