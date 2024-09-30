from config import Config, tavily_search
from langchain.agents import AgentExecutor, Tool
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_cohere.react_multi_hop.agent import create_cohere_react_agent
from langchain_cohere.chat_models import ChatCohere
from models import TavilySearchInput
from llm_models.embed import cohere_embeddings

# Internet_search tool using Tavily
internet_search = tavily_search
internet_search.name = "internet_search"
internet_search.description = "Useful for answering questions about current events, general knowledge, and timeless information, adaptively emphasizing recency when appropriate."
internet_search.args_schema = TavilySearchInput

######## VECTOR_SEARCH TOOL ########

# Docs to index
urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
]

# Load
docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]

# Split
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=512, chunk_overlap=0
)
doc_splits = text_splitter.split_documents(docs_list)

# Add to vectorstore
vectorstore = FAISS.from_documents(
    documents=doc_splits,
    embedding=cohere_embeddings,
)

vectorstore_retriever = vectorstore.as_retriever()

vectorstore_search = create_retriever_tool(
    retriever=vectorstore_retriever,
    name="vectorstore_search",
    description="Retrieve relevant info from a vectorstore that contains documents related to agents, prompt engineering, and adversarial attacks.",
)

######### Create tools #########
tools = [
    Tool(
        name="Internet Search",
        func=internet_search,
        description="Useful for when you need to answer questions about current events or general knowledge."
    ),
    Tool(
        name="Vector Database Search",
        func=vectorstore_search,
        description="Useful for when you need to find specific information from a curated database about agents, prompt engineering, and adversarial attacks."
    )
]

############### AGENT HERE ###############

chat = ChatCohere(model=Config.COHERE_MODEL, temperature=0.3)

# Preamble
preamble = """
    You are equipped with an internet search tool and a special vectorstore of information about agents prompt engineering and adversarial attacks.
    If the query covers the topics of agents, prompt engineering or adversarial attacks, use the vectorstore search.
    Otherwise, use the internet search tool.
    If the user is asking for code, do not call on any of the tools, you must directly answer the user's question. The available tools are not equipped to answer code-related questions.

    Instructions for queries that require tool use:
        1. Analyze the provided sources and determine their reliability.
        2. Synthesize information from multiple sources when possible.
        3. If sources contradict each other, mention this discrepancy in your response.
        4. Clearly indicate which parts of your response are factual (based on sources) and which are your own analysis or uncertainty.
        5. If you're unsure about any information, express your uncertainty clearly.
        6. If the query cannot be confidently answered with the given sources, say so.
        7. Time sensitive information is crucial, so prioritize recent information over older sources for queries about current events.
        
        Your response should be informative, balanced, and transparent about its sources and any uncertainties.

    Instructions for coding queries:
        1. You must only use the directly_answer tool for code-related questions unless the user wants background information that requires a response that must be fact-checked.
        2. Make sure to add detailed comments to the code to explain the code.
    
    Additional context from the router: {{router_context}}
    Router's confidence in selecting this agent: {{router_confidence}}
"""

# Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", preamble),
    ("human", "{input}"),
])


# Create the ReAct agent
agent = create_cohere_react_agent(
    llm=chat,
    tools=tools,
    prompt=prompt,
)

# Create memory
memory = ConversationBufferMemory(memory_key="chat_history", input_key="input", output_key="output", return_messages=True)

# Create the agent executor
web_search_agent = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True
)

def web_search_agent_with_context(user_input, chat_history, router_context, router_confidence):
    return web_search_agent.run(
        input=user_input,
        chat_history=chat_history,
        router_context=router_context,
        router_confidence=router_confidence
    )

#if __name__ == "__main__":
#    while True:
#        user_input = input("Enter your question: ")
#        res = web_search_agent.invoke({"input": user_input})
#        print(res["output"])