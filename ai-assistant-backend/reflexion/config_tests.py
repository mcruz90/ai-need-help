import os
from typing import List
from config.config import cohere_client as client

model = "command-r-plus-08-2024"
embed_model = "embed-multilingual-v3.0"

# Initialize the embedding function
def get_embeddings(texts: List[str]) -> List[List[float]]:
    response = client.embed(
        model=embed_model,
        texts=texts,
        embedding_types=["float"],
        input_type="classification"
    )

    embeddings =  response.embeddings.float

    return [list(map(float, embedding)) for embedding in embeddings]