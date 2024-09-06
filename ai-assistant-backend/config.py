import os
import cohere
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_cohere import CohereEmbeddings

# Load environment variables
load_dotenv()

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Initialize Cohere client
cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))

os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

# Initialize Tavily client
tavily_client = TavilySearchResults()

# Initialize Cohere embeddings
model='embed-english-v3.0'
cohere_embeddings = CohereEmbeddings(model=model, cohere_api_key=os.getenv("COHERE_API_KEY"))
