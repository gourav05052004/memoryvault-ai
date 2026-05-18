import logging
import re

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from ..db.chroma import get_chroma_collection
from ..db.mongo import get_memories_collection
from ..dependencies.auth import get_current_user
from ..services.embedding_service import align_embedding_to_collection, embed_text
from ..services.filter_service import filter_user_memories
from ..services.gemini_service import generate_answer
from ..services.query_parser_service import parse_user_query


router = APIRouter(tags=["ask"])
logger = logging.getLogger(__name__)

MAX_CANDIDATES = 100
VECTOR_CANDIDATE_MULTIPLIER = 8
MIN_RELEVANCE_SCORE = 1.5
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is",
    "it", "its", "of", "on", "or", "that", "the", "to", "was", "were", "will", "with", "this",
    "these", "those", "your", "you", "our", "their", "they", "we", "can", "should", "any", "what",
    "who", "when", "where", "why", "how", "about", "tell", "me", "my", "i",
}


class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=3, ge=1, le=10)


class AskMatch(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    title: str
    type: str
    extractedText: str | None = None
    fileUrl: str | None = None
    fileName: str | None = None
    fileSize: int | None = None
    tags: list[str]
    createdAt: str | None = None


class AskResponse(BaseModel):
    answer: str
    matched_memories: list[AskMatch]


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9_]{2,}", text.lower())
    return {word for word in words if word not in STOP_WORDS}


def _relevance_score(question_tokens: set[str], memory: dict) -> float:
    if not question_tokens:
        return 0.0

    title_tokens = _tokenize(str(memory.get("title", "")))
    summary_tokens = _tokenize(str(memory.get("summary", "")))
    tags_tokens = {str(tag).lower() for tag in memory.get("tags", []) if isinstance(tag, str)}
    content_tokens = _tokenize(str(memory.get("extractedText", "")))

    title_overlap = len(question_tokens.intersection(title_tokens))
    tags_overlap = len(question_tokens.intersection(tags_tokens))
    summary_overlap = len(question_tokens.intersection(summary_tokens))
    content_overlap = len(question_tokens.intersection(content_tokens))

    score = (
        (title_overlap * 4.0)
        + (tags_overlap * 3.0)
        + (summary_overlap * 2.0)
        + (content_overlap * 1.0)
    )

    memory_type = str(memory.get("type", "")).lower()
    if memory_type in question_tokens:
        score += 2.0

    return score


def _rank_memories(question: str, memories: list[dict], top_k: int) -> list[dict]:
    question_tokens = _tokenize(question)
    if not memories:
        return []

    scored = [(_relevance_score(question_tokens, memory), index, memory) for index, memory in enumerate(memories)]
    scored.sort(key=lambda item: (-item[0], item[1]))

    ranked = [item[2] for item in scored if item[0] >= MIN_RELEVANCE_SCORE]
    return ranked[:top_k]


def _fallback_memories_from_mongo(user_id: ObjectId, limit: int = MAX_CANDIDATES) -> list[dict]:
    collection = get_memories_collection()
    return list(collection.find({"userId": user_id}).sort("createdAt", -1).limit(limit))


def _resolve_ranked_fallback(question: str, candidate_docs: list[dict], top_k: int) -> list[dict]:
    ranked = _rank_memories(question, candidate_docs, top_k)
    if ranked:
        return ranked
    return candidate_docs[:top_k]


def _serialize_match(memory: dict) -> AskMatch:
    created_at = memory.get("createdAt")
    created_at_str = None
    if created_at:
        try:
            created_at_str = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
        except Exception:
            created_at_str = str(created_at)

    return AskMatch(
        _id=str(memory["_id"]),
        title=str(memory.get("title", "")),
        extractedText=memory.get("extractedText"),
        type=str(memory.get("type", "")),
        fileUrl=memory.get("fileUrl"),
        fileName=memory.get("fileName"),
        fileSize=memory.get("fileSize"),
        tags=[tag for tag in memory.get("tags", []) if isinstance(tag, str)],
        createdAt=created_at_str,
    )


@router.post("/ask", response_model=AskResponse)
def ask_memory(
    payload: AskRequest,
    current_user: dict = Depends(get_current_user),
) -> AskResponse:
    """
    RAG pipeline for context-aware memory retrieval.
    """
    question = payload.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    user_id = current_user["_id"]
    logger.info("[ASK] Started question processing | user_id=%s | top_k=%s", str(user_id), payload.top_k)
    logger.debug("[ASK] Question=%s", question)

    try:
        parsed_query = parse_user_query(question)
    except Exception as e:
        logger.exception("[ASK] Query parsing failed, proceeding with fallback parser path")
        parsed_query = None
    else:
        logger.info(
            "[ASK] Parsed query | date_filter=%s | memory_type=%s | keywords=%s",
            getattr(parsed_query, "date_filter", None),
            getattr(parsed_query, "memory_type", None),
            getattr(parsed_query, "keywords", []),
        )

    pre_filtered_memories: list[dict] = []
    if parsed_query:
        try:
            pre_filtered_memories = filter_user_memories(
                user_id=user_id,
                parsed_query=parsed_query,
                limit=MAX_CANDIDATES,
            )
            logger.info("[ASK] Pre-filtered memories count=%s", len(pre_filtered_memories))
        except Exception as e:
            logger.exception("[ASK] Mongo pre-filtering failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MongoDB filtering failed: {e}",
            ) from e

    try:
        chroma_collection = get_chroma_collection()
        logger.info("[ASK] Chroma collection ready | count=%s", chroma_collection.count())
        question_embedding = embed_text(
            question,
            task_type="RETRIEVAL_QUERY",
            collection=chroma_collection,
        )
        question_embedding = align_embedding_to_collection(
            question_embedding,
            collection=chroma_collection,
        )

        if pre_filtered_memories:
            pre_filtered_ids = [str(doc["_id"]) for doc in pre_filtered_memories]
            query_result = chroma_collection.query(
                query_embeddings=[question_embedding],
                n_results=max(payload.top_k * VECTOR_CANDIDATE_MULTIPLIER, payload.top_k),
                where={"document_id": {"$in": pre_filtered_ids}} if pre_filtered_ids else None,
            )
        else:
            query_result = chroma_collection.query(
                query_embeddings=[question_embedding],
                n_results=max(payload.top_k * VECTOR_CANDIDATE_MULTIPLIER, payload.top_k),
            )
        logger.info("[ASK] Vector search completed")
    except Exception as e:
        logger.exception("[ASK] Vector search failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {e}",
        ) from e

    matched_ids = query_result.get("ids", [[]])[0]
    logger.info("[ASK] Vector matched IDs count=%s", len(matched_ids))
    if not matched_ids:
        logger.warning("[ASK] No vector matches found; switching to Mongo fallback")
        fallback_docs = pre_filtered_memories or _fallback_memories_from_mongo(user_id=user_id)
        logger.info("[ASK] Fallback candidate docs count=%s", len(fallback_docs))
        if not fallback_docs:
            return AskResponse(
                answer="No relevant memories found. Try asking about specific topics, dates, or types of files.",
                matched_memories=[],
            )

        ranked_documents = _resolve_ranked_fallback(question, fallback_docs, payload.top_k)
        if not ranked_documents:
            return AskResponse(
                answer="No relevant memories found. Try asking about specific topics, dates, or types of files.",
                matched_memories=[],
            )

        try:
            answer = generate_answer(question, ranked_documents)
        except Exception as e:
            logger.exception("[ASK] Gemini answer generation failed on fallback documents")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            ) from e

        matches = [_serialize_match(document) for document in ranked_documents]
        return AskResponse(answer=answer, matched_memories=matches)

    try:
        object_ids = [ObjectId(memory_id) for memory_id in matched_ids if ObjectId.is_valid(memory_id)]
        collection = get_memories_collection()
        documents = list(collection.find({"_id": {"$in": object_ids}, "userId": user_id}))
        logger.info("[ASK] Mongo hydrated documents count=%s", len(documents))
    except Exception as e:
        logger.exception("[ASK] Mongo retrieval by matched vector IDs failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MongoDB retrieval failed: {e}",
        ) from e

    document_map = {str(document["_id"]): document for document in documents}
    ordered_documents = [document_map[memory_id] for memory_id in matched_ids if memory_id in document_map]
    ranked_documents = _resolve_ranked_fallback(question, ordered_documents, payload.top_k)

    if not ranked_documents:
        logger.warning("[ASK] Ranked documents empty after vector+mongo hydration")
        return AskResponse(
            answer="No relevant memories found. Try asking about specific topics, dates, or types of files.",
            matched_memories=[],
        )

    try:
        answer = generate_answer(question, ranked_documents)
    except Exception as e:
        logger.exception("[ASK] Gemini answer generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

    matches = [_serialize_match(document) for document in ranked_documents]
    return AskResponse(answer=answer, matched_memories=matches)

