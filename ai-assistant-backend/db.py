import chromadb
from datetime import datetime
import uuid
import logging
from chromadb.errors import ChromaError
from llm_models.embed import cohere_ef
import os

# Initialize Persistent ChromaDB client
CHROMA_DB_PATH = "./agent_conversation_data"

# Create the directory if it doesn't exist
if not os.path.exists(CHROMA_DB_PATH):
    os.makedirs(CHROMA_DB_PATH)


client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Create or get existing conversation collection
conversation_collection = client.get_or_create_collection(
    name="agent_conversations",
    embedding_function=cohere_ef,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def store_conversation(user_input: str, chatbot_response: str, conversation_id: str = None) -> None:
    """Store a conversation in the ChromaDB collection."""
    try:
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        conversation_collection.add(
            documents=[f"user: {user_input}\nassistant: {chatbot_response}"],
            metadatas=[{"type": "conversation", "timestamp": datetime.now().isoformat()}],
            ids=[conversation_id],
        )
        logger.info(f"Conversation stored successfully with ID: {conversation_id}")
        return conversation_id
    except ChromaError as ce:
        logger.error(f"ChromaDB error while storing conversation: {ce}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while storing conversation: {e}")
        raise

# TODO: Implement a more sophisticated search algorithm
# TODO: Test robustness of this function
# TODO: Flesh out route to allow client to specify n_results
def get_relevant_conversations(query, n_results=3):
    """Retrieve relevant conversations based on a query."""
    try:
        logger.info(f"Querying for relevant conversations with query: '{query}', n_results: {n_results}")
        results = conversation_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        logger.debug(f"Raw query results: {results}")
        
        if not results['documents']:
            logger.info(f"No relevant conversations found for query: {query}")
            return []
        
        conversations = results['documents'][0]
        logger.info(f"Retrieved {len(conversations)} relevant conversations")
        logger.debug(f"Conversations: {conversations}")
        
        return conversations
    except ChromaError as ce:
        logger.error(f"ChromaDB error while retrieving conversations: {ce}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while retrieving conversations: {e}")
        raise

# TODO: Review return type of this function
# TODO: Test this function
def get_conversation_by_id(conversation_id: str):
    """Retrieve a specific conversation by its ID."""
    try:
        result = conversation_collection.get(
            ids=[conversation_id],
            include=["documents", "metadatas"]
        )
        if result['ids']:
            return {
                "id": result['ids'][0],
                "document": result['documents'][0],
                "metadata": result['metadatas'][0]
            }
        else:
            logger.info(f"No conversation found with ID: {conversation_id}")
            return None
    except ChromaError as ce:
        logger.error(f"ChromaDB error while retrieving conversation: {ce}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while retrieving conversation: {e}")
        raise


# TODO: Implement client function to allow user to specify n_results
# TODO: Review return type of this function
def get_recent_conversations(n_results=10) -> list:
    """Retrieve the most recent conversations."""

    
    try:
        results = conversation_collection.get(
            where={"type": "conversation"},
            limit=n_results,
            include=["documents", "metadatas"]
        )
        logger.info(f"Retrieved {len(results['ids'])} recent conversations")
        return [
            {
                "id": id,
                "document": doc,
                "metadata": meta
            }
            for id, doc, meta in zip(results['ids'], results['documents'], results['metadatas'])
        ]
    except ChromaError as ce:
        logger.error(f"ChromaDB error while retrieving recent conversations: {ce}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while retrieving recent conversations: {e}")
        raise

if __name__ == "__main__":
    # Example usage
    user_input = "What's my schedule for tomorrow?"
    assistant_response = "You have a meeting at 10 AM and a lunch appointment at 1 PM tomorrow."
    try:
        #conv_id = store_conversation(user_input, assistant_response)
        #print(f"Stored conversation with ID: {conv_id}")

        # Retrieve relevant conversations
        query = "What appointments do I have?"
        relevant_convs = get_relevant_conversations(query)
        print("Relevant conversations:")
        for conv in relevant_convs:
            print(conv)
            print("---")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()