from config.config import Config, cohere_client
from utils.utils import logger

TOP_N = 10

class CohereReRank:
    def __init__(self):
        self.client = cohere_client
        self.model_name = Config.RERANK_MODEL

    async def rerank(self, query: str, documents: list) -> list:
        try:
            response = await self.client.rerank(
                query=query,
                documents=documents,
            model=self.model_name,
            top_n=TOP_N
            )
            return response
        except Exception as e:
            logger.error(f"Error reranking documents: {str(e)}")
            raise

rerank = CohereReRank()