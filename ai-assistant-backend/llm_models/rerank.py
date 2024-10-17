from config.config import Config, cohere_client



class CohereReRank:
    def __init__(self):
        self.client = cohere_client
        self.model_name = Config.RERANK_MODEL

    async def rerank(self, query: str, documents: list) -> list:
        response = await self.client.rerank(
            query=query,
            documents=documents,
            model=self.model_name,
            top_n=6
        )
        return response

rerank = CohereReRank()