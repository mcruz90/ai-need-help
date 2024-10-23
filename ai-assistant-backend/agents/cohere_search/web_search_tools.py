from config import tavily_client
from llm_models.rerank import rerank
from typing import List, Dict, Optional
from db import document_collection
import requests
from bs4 import BeautifulSoup
from llm_models.embed import cohere_embeddings
from llm_models.rerank import rerank
from nltk.tokenize import sent_tokenize
import nltk
from utils import logger

nltk.download('punkt')


# Create a web search function
async def web_search(query: str) -> List[Dict]:
    all_results = []
    documents = []

    response = tavily_client.search(query, search_depth="advanced", max_results=10)
    results = [
        {"title": r["title"], "content": r["content"], "url": r["url"]}
        for r in response["results"]
    ]
    all_results.extend(results)

    # Prepare documents for reranking
    rerank_docs = [f"{r['title']} {r['content']}" for r in all_results]

    # Rerank the results
    rerank_response = await rerank.rerank(query=query, documents=rerank_docs)

    # Create the final list of documents
    for idx, reranked_doc in enumerate(rerank_response.results):
        if reranked_doc.relevance_score >= 0.7:
            original_index = reranked_doc.index
            result = all_results[original_index]
            document = {
                "id": str(idx),
                "data": {
                    "title": result["title"],
                    "content": result["content"],
                    "url": result["url"],
                    "relevance_score": reranked_doc.relevance_score
                }
            }
            documents.append(document)

    documents.sort(key=lambda x: x["data"]["relevance_score"], reverse=True)
    return documents

# Create vector search tool
async def vector_search(query: str) -> List[Dict]:

    urls = [
        "https://lilianweng.github.io/posts/2023-06-23-agent/",
        "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
        "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
    ]

    # Function to fetch and parse content from a URL
    def fetch_content(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()

    # Function to split text into chunks
    def split_into_chunks(text, chunk_size=512, overlap=0):
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
                if overlap > 0:
                    words = current_chunk.split()
                    current_chunk = " ".join(words[-overlap:]) + " "
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    # Fetch and chunk content for each URL
    all_chunks = []
    for url in urls:
        content = fetch_content(url)
        chunks = split_into_chunks(content)
        all_chunks.extend([(chunk, url) for chunk in chunks])

    # Create embeddings for the chunks
    embeddings = cohere_embeddings.embed_documents([chunk for chunk, _ in all_chunks])

    # Add chunks to the ChromaDB collection
    document_collection.add(
        documents=[chunk for chunk, _ in all_chunks],
        metadatas=[{"url": url} for _, url in all_chunks],
        ids=[f"chunk_{i}" for i in range(len(all_chunks))],
        embeddings=embeddings
    )

    # Query the vector store
    results = document_collection.query(
        query_texts=[query],
        n_results=10,
        include=["documents", "metadatas", "distances"]
    )

    # Prepare documents for reranking
    rerank_docs = results['documents'][0]

    # Rerank the results
    rerank_response = await rerank.rerank(query=query, documents=rerank_docs)

    # Format the results
    formatted_results = []
    for reranked_doc in rerank_response.results:
        if reranked_doc.relevance_score >= 0.7:
            formatted_results.append({
                "id": results['ids'][0][reranked_doc.index],
                "data": {
                    "content": reranked_doc.document,
                    "url": results['metadatas'][0][reranked_doc.index]['url'],
                    "relevance_score": reranked_doc.relevance_score
                }
            })

    formatted_results.sort(key=lambda x: x["data"]["relevance_score"], reverse=True)
    return formatted_results


async def file_search(query: str, filenames: Optional[List[str]] = None) -> List[Dict]:
    """
    Search through uploaded files in ChromaDB using semantic search.
    If filenames are provided, search only within those files.
    """
    try:
        # Query parameters
        where_filter = None
        if filenames:
            where_filter = {"filename": {"$in": filenames}}
            logger.info(f"Searching in files: {filenames}")

        logger.info(f"Executing semantic search with query: '{query}'")

        # Query the vector store using only semantic search
        results = document_collection.query(
            query_texts=[query],
            n_results=20,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        if not results['documents'][0]:
            logger.warning("No results found in semantic search")
            return []

        logger.info(f"Semantic search returned {len(results['documents'][0])} chunks")

        # Format results directly without reranking
        formatted_results = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            similarity_score = 1 - (distance / 2)
            
            # Get metadata values with defaults if keys don't exist
            formatted_results.append({
                "id": results['ids'][0][i],
                "data": {
                    "content": doc,
                    "filename": metadata.get("filename", "unknown"),
                    "chunk_index": i,  # Use the current index instead of metadata
                    "total_chunks": len(results['documents'][0]),
                    "type": metadata.get("type", "document"),
                    "relevance_score": similarity_score
                }
            })

        # Sort by similarity score instead of chunk index
        formatted_results.sort(key=lambda x: x["data"]["relevance_score"], reverse=True)
        
        logger.info(f"Returning {len(formatted_results)} chunks sorted by relevance")
        
        # Log the metadata structure for debugging
        if formatted_results:
            logger.info(f"Sample metadata structure: {results['metadatas'][0][0]}")
        
        return formatted_results

    except Exception as e:
        logger.error(f"Error in file search: {str(e)}", exc_info=True)
        return []


functions_map = {
    "web_search": web_search,
    "vector_search": vector_search,
    "file_search": file_search,
}


# Define the web search tool
web_search_tool = [

    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Returns a list of relevant document snippets for a textual query retrieved from the internet",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search the internet with.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vector_search",
            "description": "Useful for when you need to find specific information from a curated database about agents, prompt engineering, and adversarial attacks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search the vector database with.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_search",
            "description": "Use for when you need to find specific information about specific files uploaded by the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search the database with, along with any information about the specific file name the user uploaded.",
                    },
                    "filenames": {
                        "type": "array",
                        "description": "The specific file names the user uploaded.",
                        "items": {"type": "string"}
                    }
                },
                "required": ["query"],
            },
        },
    }
]
