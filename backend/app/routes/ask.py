import re

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from ..db.chroma import get_chroma_collection
from ..db.mongo import get_memories_collection
from ..services.embedding_service import align_embedding_to_collection, embed_text
from ..services.groq_service import generate_answer


router = APIRouter(tags=["ask"])

MAX_FALLBACK_DOCS = 50
VECTOR_CANDIDATE_MULTIPLIER = 6
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is",
    "it", "its", "of", "on", "or", "that", "the", "to", "was", "were", "will", "with", "this",
    "these", "those", "your", "you", "our", "their", "they", "we", "can", "should", "any", "what",
    "who", "when", "where", "why", "how", "about", "tell", "me",
}

class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=3, ge=1, le=10)


class AskMatch(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    title: str
    type: str
    summary: str
    fileUrl: str | None = None
    tags: list[str]


class AskResponse(BaseModel):
    answer: str
    matches: list[AskMatch]


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9_]{2,}", text.lower())
    return {word for word in words if word not in STOP_WORDS}


def _relevance_score(question_tokens: set[str], memory: dict) -> float:
    if not question_tokens:
        return 0.0

    title_tokens = _tokenize(str(memory.get("title", "")))
    summary_tokens = _tokenize(str(memory.get("summary", "")))
    tags_tokens = {str(tag).lower() for tag in memory.get("tags", []) if isinstance(tag, str)}
    content_tokens = _tokenize(str(memory.get("extractedText", ""))[:1200])

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

    ranked = [item[2] for item in scored]
    return ranked[:top_k]


def _fallback_candidates(question: str, top_k: int) -> list[dict]:
    collection = get_memories_collection()
    docs = list(
        collection.find({}).sort("createdAt", -1).limit(max(top_k * VECTOR_CANDIDATE_MULTIPLIER, MAX_FALLBACK_DOCS))
    )
    return _rank_memories(question, docs, top_k)


def _serialize_match(memory: dict) -> AskMatch:
    return AskMatch(
        _id=str(memory["_id"]),
        title=str(memory.get("title", "")),
        type=str(memory.get("type", "")),
        summary=str(memory.get("summary", "")),
        fileUrl=memory.get("fileUrl"),
        tags=[tag for tag in memory.get("tags", []) if isinstance(tag, str)],
    )


@router.post("/ask", response_model=AskResponse)
def ask_memory(payload: AskRequest) -> AskResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    matched_ids: list[str] = []

    try:
        question_embedding = embed_text(question)
        chroma_collection = get_chroma_collection()
        question_embedding = align_embedding_to_collection(
            question_embedding,
            collection=chroma_collection,
        )
        query_result = chroma_collection.query(
            query_embeddings=[question_embedding],
            n_results=max(payload.top_k * VECTOR_CANDIDATE_MULTIPLIER, payload.top_k),
        )
        matched_ids = query_result.get("ids", [[]])[0]
    except Exception:
        matched_ids = []

    ranked_documents: list[dict] = []

    if matched_ids:
        object_ids = [ObjectId(memory_id) for memory_id in matched_ids if ObjectId.is_valid(memory_id)]
        if object_ids:
            collection = get_memories_collection()
            documents = list(collection.find({"_id": {"$in": object_ids}}))
            document_map = {str(document["_id"]): document for document in documents}
            ordered_documents = [document_map[memory_id] for memory_id in matched_ids if memory_id in document_map]
            ranked_documents = _rank_memories(question, ordered_documents, payload.top_k)

    if not ranked_documents:
        ranked_documents = _fallback_candidates(question, payload.top_k)

    if not ranked_documents:
        return AskResponse(answer="No relevant memories found.", matches=[])

    answer = generate_answer(question, ranked_documents)
    matches = [_serialize_match(document) for document in ranked_documents]

    return AskResponse(answer=answer, matches=matches)
