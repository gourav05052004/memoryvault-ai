import logging
from datetime import datetime
from typing import Literal

from google import genai
from google.genai import types

from ..config import EMBEDDING_MODEL, GEMINI_API_KEY
from ..db.chroma import get_chroma_collection

logger = logging.getLogger(__name__)


MAX_EMBED_TEXT_CHARS = 12000
TARGET_EMBEDDING_DIM = 768
_GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def _truncate_text(text: str) -> str:
    cleaned_text = text.strip()
    if len(cleaned_text) <= MAX_EMBED_TEXT_CHARS:
        return cleaned_text
    return cleaned_text[:MAX_EMBED_TEXT_CHARS]


def _normalize_created_at(created_at: datetime) -> str:
    if isinstance(created_at, datetime):
        return created_at.isoformat()
    return str(created_at)


def build_memory_embedding_text(
    title: str,
    memory_type: str,
    tags: list[str],
    summary: str,
    extracted_text: str,
) -> str:
    # Use FULL extracted text for embeddings, not just snippet
    # This ensures comprehensive semantic search across entire document
    full_content = extracted_text.strip()[:MAX_EMBED_TEXT_CHARS]
    tags_text = ", ".join(tags) if tags else ""

    return (
        f"Title: {title}\n"
        f"Type: {memory_type}\n"
        f"Tags: {tags_text}\n"
        f"Summary: {summary}\n"
        f"Content: {full_content}"
    )


def _resize_embedding(embedding: list[float], target_dim: int = TARGET_EMBEDDING_DIM) -> list[float]:
    if len(embedding) == target_dim:
        return embedding
    if len(embedding) > target_dim:
        return embedding[:target_dim]
    return [*embedding, *([0.0] * (target_dim - len(embedding)))]


def _get_collection_embedding_dim(collection) -> int | None:
    try:
        if collection.count() == 0:
            return None

        sample = collection.peek()
        embeddings = sample.get("embeddings") if isinstance(sample, dict) else None
        if embeddings is None:
            return None

        if hasattr(embeddings, "shape"):
            shape = getattr(embeddings, "shape", None)
            if shape and len(shape) >= 2 and shape[0] > 0 and shape[1] > 0:
                return int(shape[1])

        if isinstance(embeddings, list) and embeddings:
            first = embeddings[0]
            if isinstance(first, list) and first:
                return len(first)
            if hasattr(first, "shape"):
                first_shape = getattr(first, "shape", None)
                if first_shape and len(first_shape) >= 1 and first_shape[0] > 0:
                    return int(first_shape[0])

        return None
    except Exception:
        return None


def align_embedding_to_collection(embedding: list[float], collection=None) -> list[float]:
    target_dim = None
    if collection is None:
        try:
            collection = get_chroma_collection()
        except Exception:
            collection = None

    if collection is not None:
        target_dim = _get_collection_embedding_dim(collection)

    if target_dim is None:
        target_dim = TARGET_EMBEDDING_DIM

    return _resize_embedding(embedding, target_dim=target_dim)


def _resolve_embedding_dim(collection=None) -> int:
    target_dim = _get_collection_embedding_dim(collection) if collection is not None else None
    if target_dim is None:
        target_dim = TARGET_EMBEDDING_DIM
    return target_dim


def _extract_values_from_embedding_result(result) -> list[float]:
    embeddings = getattr(result, "embeddings", None)
    if embeddings and len(embeddings) > 0:
        first = embeddings[0]
        values = getattr(first, "values", None)
        if values:
            return [float(value) for value in values]

    single_embedding = getattr(result, "embedding", None)
    single_values = getattr(single_embedding, "values", None) if single_embedding else None
    if single_values:
        return [float(value) for value in single_values]

    raise RuntimeError("Gemini returned an invalid embedding response")


def embed_text(
    text: str,
    task_type: Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"] = "RETRIEVAL_DOCUMENT",
    collection=None,
) -> list[float]:
    truncated_text = _truncate_text(text)
    if not truncated_text:
        raise RuntimeError("Cannot embed empty text")
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    if _GEMINI_CLIENT is None:
        raise RuntimeError("Gemini client is not initialized")

    try:
        output_dimensionality = _resolve_embedding_dim(collection=collection)
        response = _GEMINI_CLIENT.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=truncated_text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=output_dimensionality,
            ),
        )
        embedding = _extract_values_from_embedding_result(response)
        aligned = align_embedding_to_collection(embedding, collection=collection)
        logger.debug(
            f"Generated {len(aligned)}-dim Gemini embedding using {EMBEDDING_MODEL} "
            f"(task_type={task_type}, output_dimensionality={output_dimensionality})"
        )
        return aligned
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise RuntimeError(f"Failed to generate embedding: {e}")


def index_memory_vector(
    memory_id: str,
    memory_type: str,
    title: str,
    tags: list[str],
    summary: str,
    extracted_text: str,
    created_at: datetime,
) -> None:
    combined_text = build_memory_embedding_text(
        title=title,
        memory_type=memory_type,
        tags=tags,
        summary=summary,
        extracted_text=extracted_text,
    )

    collection = get_chroma_collection()
    embedding = embed_text(
        combined_text,
        task_type="RETRIEVAL_DOCUMENT",
        collection=collection,
    )
    embedding = align_embedding_to_collection(embedding, collection=collection)

    collection.upsert(
        ids=[memory_id],
        documents=[combined_text],
        embeddings=[embedding],
        metadatas=[
            {
                "document_id": memory_id,
                "type": memory_type,
                "title": title,
                "createdAt": _normalize_created_at(created_at),
            }
        ],
    )
