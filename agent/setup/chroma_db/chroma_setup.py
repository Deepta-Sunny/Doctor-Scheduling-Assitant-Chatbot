import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

def get_chroma_client():
    """Initialize and return ChromaDB cloud client."""
    client = chromadb.CloudClient(
        api_key=os.getenv('CHROMA_API_KEY'),
        tenant=os.getenv('CHROMA_TENANT'),
        database=os.getenv('CHROMA_DATABASE')
    )
    return client

def get_or_create_collection(client, collection_name="faq_documents"):
    """Get or create a collection in ChromaDB."""
    try:
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "FAQ documents for doctor appointment scheduling"}
        )
        return collection
    except Exception as e:
        print(f"Error creating collection: {e}")
        raise
