from urllib import response
from web_search_tools import model
from datetime import date
from langchain_cohere.chat_models import ChatCohere
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor
from langchain_cohere.react_multi_hop.agent import create_cohere_react_agent
from web_search_tools import internet_search
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from typing import Any
from utils import sanitize_html_content
import logging
from config import cohere_model as model

cohere_model = ChatCohere(model=model,)

memory = ChatMessageHistory(session_id="test-session")

today_date = str(date.today())

preamble = """
You are an upbeat, encouraging tutor who helps students understand concepts by explaining ideas and asking students questions.
Start by introducing yourself as their AI tutor who is happy to help with any questions.
You are equipped with an internet search tool to cite anything you say that requires fact-checking.
Do not make up information. If you cannot answer their question without results from the search tool, you must say so.

Make sure to use LaTeX and markdown formatting in your responses, especially for mathematical equations.

Only ask one question at a time after each conversation turn. Never move on until the student answers the question, even if they ask another related question.

They will usually initiate the conversation with a question asking for help on learning a topic or getting more clarification. Respond by asking them what they already know about the chosen topic. Wait for a response. Given this information, help students understand the topic by providing explanations, examples, analogies. These should be
tailored to the student's prior knowledge or what they already know about the topic. Give students explanations, examples, and analogies about the concept to help them understand. You should guide students in an open-ended way. Do not provide immediate answers or solutions to problems but help students generate their own answers by asking leading questions. Ask students to explain their thinking. If the student is struggling or gets the answer wrong, try giving them additional support or give them a hint. If the student improves, then praise them ans show excitement. Try to end your responses with a question so that the student has to keep generating ideas. Once the student shows an appropriate level of understanding, ask them to explain the concept in their own words (this is the best way to show you know something), or ask them for examples. When the student demosnstrates that they know the concept, you can move the conversation to a close and tell them you're here to help if they have further questions.

This may become a very long conversation, with many topics covered, and the user may be likely to forget the information you have provided in previous responses.
You should occasionally summarize what has been discussed and the progress the user has made, and ask if the user would like to review the material again.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", preamble),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
])
agent = create_cohere_react_agent(
    llm=cohere_model,
    tools=[internet_search],
    prompt=prompt,
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=[internet_search],
    verbose=True,
)


agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    lambda session_id: memory,
    input_messages_key="input",
    history_messages_key="chat_history",
    )

def enhance_output_with_citations(output: str, citations: list) -> str:
    """
    Enhances the output by inserting superscript links for citations, ensuring each unique URL
    has a unique superscript number and handling multiple documents per citation.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Sort citations by start index in ascending order for natural reading order
    sorted_citations = sorted(citations, key=lambda x: x.start)
    
    # Initialize URL to superscript mapping
    url_to_superscript = {}
    current_superscript = 1
    
    # Reverse sorted order to insert from the end and prevent index shifting
    sorted_citations = sorted_citations[::-1]
    
    for citation in sorted_citations:
        start = citation.start
        end = citation.end
        text = citation.text
        documents = citation.documents
        
        if not documents:
            logging.warning(f"Citation with text '{text}' has no documents.")
            continue

        # Collect all unique URLs from documents
        urls = [doc['url'] for doc in documents if 'url' in doc]
        unique_urls = list(dict.fromkeys(urls)) 

        if not unique_urls:
            logging.warning(f"Citation with text '{text}' has no valid URLs.")
            continue

        superscripts = []
        for url in unique_urls:
            if url in url_to_superscript:
                sup_num = url_to_superscript[url]
                logging.info(f"Reusing superscript [{sup_num}] for URL: {url}")
            else:
                sup_num = current_superscript
                url_to_superscript[url] = sup_num
                current_superscript +=1
                logging.info(f"Assigning superscript [{sup_num}] to URL: {url}")
            superscripts.append(f'<a href="{url}" target="_blank">[{sup_num}]</a>')
        
        # Combine multiple superscripts for multiple URLs
        superscript = '<sup>' + ' '.join(superscripts) + '</sup>'
        
        # Insert the underlined text with the superscript
        output = (
            output[:start] +
            f'<span style="background-color: #2ca89f;">{text}</span>{superscript}' +
            output[end:]
        )
    
    return output

def safe_get(dictionary, key, default=None):
    return dictionary.get(key, default)

def tutor_agent(user_input: Any, chat_history: Any) -> Any:
    try:
        response = agent_with_chat_history.invoke(
            {"input": user_input, "chat_history": chat_history},
            config={"configurable": {"session_id": "test-session"}})
        
        output = safe_get(response, 'output', default="")
        citations = safe_get(response, 'citations', default=[])

        if output and citations:
            enhanced_output = enhance_output_with_citations(output, citations)
            sanitized_output = sanitize_html_content(enhanced_output)
            grounded_answer = "This response is grounded in the following sources: " + ", ".join([doc['url'] for citation in citations for doc in citation.documents if 'url' in doc])
            return {
                "message": sanitized_output,
                "grounded_answer": grounded_answer
            }
        elif output:
            sanitized_output = sanitize_html_content(output)
            return {
                "message": sanitized_output,
                "grounded_answer": "No specific sources were cited for this response."
            }
        else:
            return {
                "message": "No response generated",
                "grounded_answer": "No response was generated, so no grounding is available."
            }
    
    except KeyError as e:
        return {
            "message": f"Key error: {e}",
            "grounded_answer": "An error occurred, so no grounding is available."
        }
    
    except Exception as e:
        return {
            "message": f"Unexpected error: {e}",
            "grounded_answer": "An error occurred, so no grounding is available."
        }

#if __name__ == "__main__":

#    while True:
#        user_input = input("Enter your question: ")
#        response = tutor_agent(user_input, [])
#        print(response)