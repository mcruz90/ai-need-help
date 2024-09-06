import os
from config import tavily_client, cohere_client, cohere_embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain.tools.retriever import create_retriever_tool
from langchain_cohere.chat_models import ChatCohere
from models import TavilySearchInput

from langchain.agents import AgentExecutor
from langchain_cohere.react_multi_hop.agent import create_cohere_react_agent
from langchain_core.prompts import ChatPromptTemplate

# LLM model
model='command-r-plus-08-2024'

# Internet_search tool using Tavily
internet_search = tavily_client
internet_search.name = "internet_search"
internet_search.description = "Returns a list of relevant document snippets for a textual query retrieved from the internet."
internet_search.args_schema = TavilySearchInput



######## VECTOR_SEARCH TOOL ########

# Set embeddings
embd = cohere_embeddings

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
    embedding=embd,
)

vectorstore_retriever = vectorstore.as_retriever()

vectorstore_search = create_retriever_tool(
    retriever=vectorstore_retriever,
    name="vectorstore_search",
    description="Retrieve relevant info from a vectorstore that contains documents related to agents, prompt engineering, and adversarial attacks.",
)

############### AGENT HERE ###############

chat = ChatCohere(model=model, temperature=0.3)

# Prompt
prompt = ChatPromptTemplate.from_template("{input}")

# Preamble
preamble = """
You are an expert who answers the user's question with the most relevant datasource.
You are equipped with an internet search tool and a special vectorstore of information about agents prompt engineering and adversarial attacks.
If the query covers the topics of agents, prompt engineering or adversarial attacks, use the vectorstore search.
"""

# Prompt
prompt = ChatPromptTemplate.from_template("{input}")

# Create the ReAct agent
agent = create_cohere_react_agent(
    llm=chat,
    tools=[internet_search, vectorstore_search],
    prompt=prompt,
)

agent_executor = AgentExecutor(
    agent=agent, tools=[internet_search, vectorstore_search], verbose=True
)

agent_executor.invoke(
    {
        "input": "Who will the Bears draft first in the NFL draft?",
        "preamble": preamble,
    }
)