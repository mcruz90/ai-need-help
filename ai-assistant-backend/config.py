import os
import cohere
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_cohere import CohereEmbeddings
from chromadb.utils.embedding_functions import EmbeddingFunction
from cohere import ClassifyExample

# Load environment variables
load_dotenv()

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# LLM model
cohere_model='command-r-plus-08-2024'

# Initialize Cohere client
cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))

# Initialize Langchain Cohere embeddings
embed_model='embed-english-v2.0'
cohere_embeddings = CohereEmbeddings(model=embed_model, cohere_api_key=os.getenv("COHERE_API_KEY"))

# Custom Cohere embedding function for ChromaDB
class CustomCohereEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key, model_name=embed_model):
        self.client = cohere.Client(api_key)
        self.model_name = model_name

    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        embeddings = self.client.embed(texts=input, model=self.model_name).embeddings
        return [list(map(float, embedding)) for embedding in embeddings]

# Create the custom Cohere embedding function
cohere_ef = CustomCohereEmbeddingFunction(api_key=os.getenv("COHERE_API_KEY"))

# Initialize Tavily client
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

tavily_search = TavilySearchResults(
    max_results=8,
)


examples = [
    # Time-sensitive examples
    ClassifyExample(text="What are the latest developments in AI?", label="time_sensitive"),
    ClassifyExample(text="Breaking news on the economic summit", label="time_sensitive"),
    ClassifyExample(text="Current trends in renewable energy", label="time_sensitive"),
    ClassifyExample(text="This week's top selling books", label="time_sensitive"),
    ClassifyExample(text="Recent breakthroughs in quantum computing", label="time_sensitive"),
    ClassifyExample(text="How has the stock market performed over the past month?", label="time_sensitive"),
    ClassifyExample(text="What are the upcoming movie releases this summer?", label="time_sensitive"),
    ClassifyExample(text="Latest updates on the ongoing climate conference", label="time_sensitive"),
    ClassifyExample(text="Who are the frontrunners in the upcoming election?", label="time_sensitive"),
    ClassifyExample(text="What were the major scientific discoveries of the past year?", label="time_sensitive"),
    ClassifyExample(text="How has the COVID-19 situation changed in the last few weeks?", label="time_sensitive"),
    ClassifyExample(text="What are the current diplomatic tensions between countries X and Y?", label="time_sensitive"),
    ClassifyExample(text="Recent advancements in electric vehicle technology", label="time_sensitive"),
    ClassifyExample(text="This season's fashion trends", label="time_sensitive"),
    ClassifyExample(text="How have housing prices changed in the last quarter?", label="time_sensitive"),

    # Timeless examples
    ClassifyExample(text="What is the capital of France?", label="timeless"),
    ClassifyExample(text="How does photosynthesis work?", label="timeless"),
    ClassifyExample(text="What are the basic principles of economics?", label="timeless"),
    ClassifyExample(text="Explain the theory of relativity", label="timeless"),
    ClassifyExample(text="Who wrote 'To Kill a Mockingbird'?", label="timeless"),
    ClassifyExample(text="What is the chemical composition of water?", label="timeless"),
    ClassifyExample(text="Describe the process of mitosis", label="timeless"),
    ClassifyExample(text="What are the main themes in Shakespeare's 'Hamlet'?", label="timeless"),
    ClassifyExample(text="How does a combustion engine work?", label="timeless"),
    ClassifyExample(text="What is the significance of the Pythagorean theorem?", label="timeless"),
    ClassifyExample(text="Explain the concept of supply and demand", label="timeless"),
    ClassifyExample(text="What are the main features of Renaissance art?", label="timeless"),
    ClassifyExample(text="How do vaccines work to prevent diseases?", label="timeless"),
    ClassifyExample(text="What is the structure of an atom?", label="timeless"),
    ClassifyExample(text="Describe the water cycle on Earth", label="timeless"),

    # More nuanced or ambiguous examples
    ClassifyExample(text="How has our understanding of dinosaurs changed?", label="time_sensitive"),
    ClassifyExample(text="What are the long-term effects of climate change?", label="timeless"),
    ClassifyExample(text="How do modern interpretations of Shakespeare differ from historical ones?", label="time_sensitive"),
    ClassifyExample(text="What are the enduring impacts of the Industrial Revolution?", label="timeless"),
    ClassifyExample(text="How has the role of women in society evolved over the past century?", label="time_sensitive"),
    ClassifyExample(text="What are the fundamental laws of thermodynamics?", label="timeless"),
    ClassifyExample(text="How do current space exploration efforts compare to those of the 1960s?", label="time_sensitive"),
    ClassifyExample(text="What are the classic symptoms of depression?", label="timeless"),
    ClassifyExample(text="How has the internet changed the way we communicate?", label="time_sensitive"),
    ClassifyExample(text="What are the key differences between major world religions?", label="timeless")
    ]

def classify_query_time_sensitivity(query: str) -> float:
    response = cohere_client.classify(
        model="embed-multilingual-v2.0",
        inputs=[query],
        examples=examples
    )
    
    # Extract the classification result for the query
    classification = response.classifications[0]
    
    # Check if 'time_sensitive' is in the labels
    if 'time_sensitive' in classification.labels:
        return classification.labels['time_sensitive'].confidence
    else:
        # If 'time_sensitive' is not a label, assume it's the opposite of 'timeless'
        return 1 - classification.labels['timeless'].confidence