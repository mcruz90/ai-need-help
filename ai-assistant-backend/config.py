import os
import cohere
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from tavily import TavilyClient

# Load environment variables
load_dotenv()

class Config:
    DEBUG = os.getenv("DEBUG", "False") == "True"
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Cohere models
    COHERE_MODEL = 'command-r-plus-08-2024'
    EMBED_MODEL = 'embed-english-v2.0'
    RERANK_MODEL = 'rerank-multilingual-v3.0'


    # Initialize Cohere client
    @classmethod
    def init_cohere_client(cls):
        return cohere.ClientV2(cls.COHERE_API_KEY)

    @classmethod
    def init_tavily_search(cls):
        return TavilySearchResults(max_results=8)
    
    @classmethod
    def init_cohere_tavily_search(cls):
        return TavilyClient(api_key=cls.TAVILY_API_KEY)
        

# Create instances of the Cohere client
cohere_client = Config.init_cohere_client()
# Create Tavily search instance
tavily_search = Config.init_tavily_search()

tavily_client = Config.init_cohere_tavily_search()