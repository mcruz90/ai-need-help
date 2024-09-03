import os
import cohere
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Cohere client
cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))