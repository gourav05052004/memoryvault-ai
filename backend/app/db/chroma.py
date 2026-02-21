import logging
from pathlib import Path
from typing import Optional

import chromadb

logger = logging.getLogger(__name__)


COLLECTION_NAME = "memories_vectors"
BASE_DIR = Path(__file__).resolve().parents[2]
CHROMA_STORE_DIR = BASE_DIR / "chroma_store"
CHROMA_STORE_DIR.mkdir(parents=True, exist_ok=True)

_client: Optional[chromadb.PersistentClient] = None
_collection = None


def get_chroma_collection():
    global _client, _collection

    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_STORE_DIR))
        _collection = _client.get_or_create_collection(name=COLLECTION_NAME)

    return _collection


def reset_chroma_collection():
    """Delete and recreate the collection. Use this to fix dimension mismatches."""
    global _client, _collection
    
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_STORE_DIR))
    
    try:
        _client.delete_collection(name=COLLECTION_NAME)
        logger.debug(f"Deleted old ChromaDB collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.debug(f"Could not delete collection: {e}")
    
    _collection = None
    
    # Recreate with new dimensions
    _collection = _client.get_or_create_collection(name=COLLECTION_NAME)
    logger.info(f"Created fresh ChromaDB collection: {COLLECTION_NAME}")
    
    return _collection
