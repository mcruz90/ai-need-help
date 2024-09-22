from config import tavily_client, cohere_model as model
from config import cohere_embeddings as embd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain.tools.retriever import create_retriever_tool
from langchain_cohere.chat_models import ChatCohere
from models import TavilySearchInput
from datetime import date
from langchain.agents import AgentExecutor, Tool
from langchain_cohere.react_multi_hop.agent import create_cohere_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory

# Internet_search tool using Tavily
internet_search = tavily_client
internet_search.name = "internet_search"
internet_search.description = "Returns a list of relevant document snippets for a textual query retrieved from the internet."
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

today_date = str(date.today())

# Preamble
preamble = f'''
Today is {today_date}.
You are a general knowledge expert who answers the user's question with the most relevant datasource using today's date as a point of reference.
You are equipped with an internet search tool and a special vectorstore of information about agents prompt engineering and adversarial attacks.
If the query covers the topics of agents, prompt engineering or adversarial attacks, use the vectorstore search.
Otherwise, use the internet search tool.

If the user is asking for code, do not call on any of the tools, you must directly answer the user's question. The available tools are not equipped to answer code-related questions.
'''

# Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", preamble),
    ("human", "{input}"),
])

# Create tools
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

# Create the ReAct agent
agent = create_cohere_react_agent(
    llm=chat,
    tools=tools,
    prompt=prompt,
)

# Create memory
memory = ConversationBufferMemory(memory_key="chat_history", input_key="input", output_key="output", return_messages=True)

# Create the agent executor
web_search_agent = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True
)

#if __name__ == "__main__":
#    while True:
#        user_input = input("Enter your question: ")
#        res = web_search_agent.invoke({"input": user_input})
#        print(res["output"])