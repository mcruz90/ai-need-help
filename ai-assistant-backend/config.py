import os
import cohere
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_cohere import CohereEmbeddings
from chromadb.utils.embedding_functions import EmbeddingFunction

# Load environment variables
load_dotenv()

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Initialize Cohere client
cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))

# Initialize Tavily client
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
tavily_client = TavilySearchResults()

# Initialize Langchain Cohere embeddings
model='embed-english-v3.0'
cohere_embeddings = CohereEmbeddings(model=model, cohere_api_key=os.getenv("COHERE_API_KEY"))

# Custom Cohere embedding function for ChromaDB
class CustomCohereEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key, model_name="embed-english-v2.0"):
        self.client = cohere.Client(api_key)
        self.model_name = model_name

    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        embeddings = self.client.embed(texts=input, model=self.model_name).embeddings
        return [list(map(float, embedding)) for embedding in embeddings]

# Create the custom Cohere embedding function
cohere_ef = CustomCohereEmbeddingFunction(api_key=os.getenv("COHERE_API_KEY"))