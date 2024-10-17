from config import tavily_client
from llm_models.rerank import rerank
from utils import logger
from typing import List, Dict

# Create a web search function

async def web_search(queries: List[str]) -> List[Dict]:
    all_results = []
    documents = []

    # Perform searches for all queries
    for query in queries:
        response = tavily_client.search(query, search_depth="advanced", max_results=6)
        results = [
            {"title": r["title"], "content": r["content"], "url": r["url"]}
            for r in response["results"]
        ]
        all_results.extend(results)

    # Prepare documents for reranking
    rerank_docs = [f"{r['title']} {r['content']}" for r in all_results]

    # Rerank the results
    rerank_response = await rerank.rerank(query=queries[0], documents=rerank_docs)

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

    # Sort documents by relevance score (highest first) and take top 6
    documents.sort(key=lambda x: x["data"]["relevance_score"], reverse=True)
    return documents[:6]


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
