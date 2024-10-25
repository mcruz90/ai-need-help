from config.config import Config, cohere_sync_client
from langchain_cohere import CohereEmbeddings
from chromadb.utils.embedding_functions import EmbeddingFunction
from typing import List
from utils.utils import logger
from typing import List, Union
import base64

class Embeddings():
    def __init__(self, model_name=Config.EMBED_MODEL, embeddings_type=["float"]):
        self.client = cohere_sync_client
        self.model_name = model_name
        self.embeddings_type = embeddings_type

    def embed_documents(self, texts: List[str]):
        """Embed text documents using the Cohere API."""
        logger.info(f"Embedding {len(texts)} documents")
        response = self.client.embed(
            texts=texts,
            model=self.model_name,
            embedding_types=self.embeddings_type,
            input_type="search_document"
        )
        return response.embeddings.float

    def embed_images(self, image_paths: List[str]):
        """
        Embed images using the Cohere API.
        Each image must be less than 5MB in size.
        """
        # Convert images to data URIs
        image_uris = []
        for image_path in image_paths:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                image_uri = f"data:image/jpeg;base64,{encoded_string}"
                image_uris.append(image_uri)

        response = self.client.embed(
            images=image_uris,
            model=self.model_name,
            embedding_types=self.embeddings_type,
            input_type="image"
        )
        return response.embeddings.float

class CustomCohereEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key, model_name=Config.EMBED_MODEL, embeddings_type=["float"], input_type=None):
        self.client = cohere_sync_client
        self.model_name = model_name
        self.input_type = input_type
        self.embeddings_type = embeddings_type


    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
            

        response = self.client.embed(
            texts=input,
            model=self.model_name,
            embedding_types=self.embeddings_type,
            input_type=self.input_type
        )

        embeddings = response.embeddings.float

        return [list(map(float, embedding)) for embedding in embeddings]

def init_embeddings():

    """Initialize and return the embeddings and custom embedding function."""
    cohere_embeddings = CohereEmbeddings(model=Config.EMBED_MODEL, cohere_api_key=Config.COHERE_API_KEY, user_agent="ai-assistant-backend")
    cohere_ef = CustomCohereEmbeddingFunction(api_key=Config.COHERE_API_KEY, input_type="search_document")
    return cohere_embeddings, cohere_ef

def get_embeddings(texts: List[str]) -> List[List[float]]:
    response = cohere_sync_client.embed(
        model=Config.EMBED_MODEL,
        texts=texts,
        embedding_types=["float"],
        input_type="classification"
    )

    embeddings =  response.embeddings.float

    return [list(map(float, embedding)) for embedding in embeddings]

cohere_embeddings, cohere_ef = init_embeddings()

__all__ = ["cohere_embeddings", "cohere_ef", "get_embeddings"]