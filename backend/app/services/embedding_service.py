from datetime import datetime
import hashlib
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import GROQ_API_KEY, GROQ_EMBEDDING_MODEL
from ..db.chroma import get_chroma_collection


EMBEDDING_URL = "https://api.groq.com/openai/v1/embeddings"
MAX_EMBED_TEXT_CHARS = 12000
MAX_CONTENT_SNIPPET_CHARS = 2000
TARGET_EMBEDDING_DIM = 768
REQUEST_TIMEOUT_SECONDS = 60


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
    content_snippet = extracted_text.strip()[:MAX_CONTENT_SNIPPET_CHARS]
    tags_text = ", ".join(tags) if tags else ""

    return (
        f"Title: {title}\n"
        f"Type: {memory_type}\n"
        f"Tags: {tags_text}\n"
        f"Summary: {summary}\n"
        f"Content: {content_snippet}"
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


def _deterministic_embedding(text: str, target_dim: int = TARGET_EMBEDDING_DIM) -> list[float]:
    values: list[float] = []
    counter = 0

    while len(values) < target_dim:
        digest = hashlib.sha256(f"{text}::{counter}".encode("utf-8")).digest()
        counter += 1

        for index in range(0, len(digest), 4):
            chunk = digest[index : index + 4]
            if len(chunk) < 4:
                continue
            integer = int.from_bytes(chunk, byteorder="big", signed=False)
            normalized = (integer / 4294967295.0) * 2.0 - 1.0
            values.append(float(normalized))
            if len(values) >= target_dim:
                break

    return values[:target_dim]


def _embed_with_groq(text: str) -> list[float]:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    payload = {
        "model": GROQ_EMBEDDING_MODEL,
        "input": text,
    }

    req = Request(
        EMBEDDING_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Groq embedding HTTP {exc.code}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Groq embedding API: {exc.reason}") from exc

    parsed = json.loads(raw)
    data = parsed.get("data") if isinstance(parsed, dict) else None
    if not isinstance(data, list) or not data:
        raise RuntimeError("Groq embedding response has no data")

    first_item = data[0] if isinstance(data[0], dict) else None
    embedding = first_item.get("embedding") if isinstance(first_item, dict) else None
    if not isinstance(embedding, list) or not embedding:
        raise RuntimeError("Groq embedding response missing vector")

    return [float(value) for value in embedding]


def embed_text(text: str) -> list[float]:
    truncated_text = _truncate_text(text)
    if not truncated_text:
        raise RuntimeError("Cannot embed empty text")

    try:
        embedding = _embed_with_groq(truncated_text)
        return align_embedding_to_collection(embedding)
    except Exception:
        fallback_embedding = _deterministic_embedding(truncated_text)
        return align_embedding_to_collection(fallback_embedding)


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
    embedding = embed_text(combined_text)
    embedding = align_embedding_to_collection(embedding, collection=collection)

    collection.upsert(
        ids=[memory_id],
        documents=[combined_text],
        embeddings=[embedding],
        metadatas=[
            {
                "type": memory_type,
                "title": title,
                "createdAt": _normalize_created_at(created_at),
            }
        ],
    )
