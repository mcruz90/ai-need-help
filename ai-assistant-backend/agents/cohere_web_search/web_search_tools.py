from config import tavily_client
from llm_models.rerank import rerank
import logging

logger = logging.getLogger(__name__)

# Create a web search function

def web_search(queries: list[str]) -> list[dict]:
    all_results = []

    for query in queries:
        response = tavily_client.search(query, search_depth="advanced", max_results=6)
        
        results = [
            {"title": r["title"], "content": r["content"], "url": r["url"]}
            for r in response["results"]
        ]
        all_results.extend(results)

    # Prepare documents for reranking
    documents = [f"{r['title']} {r['content']}" for r in all_results]

    # Rerank the results
    rerank_response = rerank.rerank(query=queries[0], documents=documents)
    

    # Filter and create the final list of documents
    documents = []
    for reranked_doc in rerank_response.results:
        if reranked_doc.relevance_score >= 0.7: 
            original_index = reranked_doc.index
            result = all_results[original_index]
            document = {
                "id": str(original_index),
                "data": result,
                "relevance_score": reranked_doc.relevance_score
            }
            documents.append(document)

    # Sort documents by relevance score (highest first)
    documents.sort(key=lambda x: x["relevance_score"], reverse=True)

    return {"documents": documents[:6]}  # Return top 5 most relevant documents


functions_map = {
    "web_search": web_search,
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
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "a list of queries to search the internet with.",
                    }
                },
                "required": ["queries"],
            },
        },
    }
]