from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from ..db.mongo import get_memories_collection
from ..db.chroma import get_chroma_collection
from ..services.embedding_service import index_memory_vector
from ..services.groq_service import generate_summary_and_tags


router = APIRouter(tags=["memories"])


class CreateNoteRequest(BaseModel):
    title: str
    content: str


class CreateMemoryResponse(BaseModel):
    id: str
    message: str
    summary: str
    tags: list[str]


class MemoryListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    type: str
    title: str
    summary: str
    tags: list[str]
    createdAt: datetime


class MemoryDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    type: str
    title: str
    extractedText: str
    summary: str
    tags: list[str]
    createdAt: datetime
    updatedAt: datetime


def _parse_object_id(memory_id: str) -> ObjectId:
    try:
        return ObjectId(memory_id)
    except InvalidId as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid memory id",
        ) from exc


def _serialize_memory(document: dict) -> dict:
    serialized = dict(document)
    serialized["_id"] = str(serialized["_id"])
    return serialized


@router.post("/memory/note", response_model=CreateMemoryResponse, status_code=status.HTTP_201_CREATED)
def create_note(payload: CreateNoteRequest) -> CreateMemoryResponse:
    collection = get_memories_collection()
    now = datetime.now(timezone.utc)

    generated_summary = ""
    generated_tags: list[str] = []

    try:
        generated = generate_summary_and_tags(payload.content, payload.title)
        generated_summary = str(generated.get("summary", "")).strip()
        generated_tags = [tag for tag in generated.get("tags", []) if isinstance(tag, str)]
    except Exception:
        generated_summary = ""
        generated_tags = []

    document = {
        "type": "note",
        "title": payload.title,
        "extractedText": payload.content,
        "summary": generated_summary,
        "tags": generated_tags,
        "createdAt": now,
        "updatedAt": now,
    }

    result = collection.insert_one(document)
    memory_id = str(result.inserted_id)

    try:
        index_memory_vector(
            memory_id=memory_id,
            memory_type="note",
            title=payload.title,
            tags=generated_tags,
            summary=generated_summary,
            extracted_text=payload.content,
            created_at=now,
        )
    except Exception:
        pass

    return CreateMemoryResponse(
        id=memory_id,
        message="Memory created successfully",
        summary=generated_summary,
        tags=generated_tags,
    )


@router.get("/memories", response_model=list[MemoryListItem])
def list_memories() -> list[MemoryListItem]:
    collection = get_memories_collection()

    cursor = collection.find({}, {"extractedText": 0, "updatedAt": 0}).sort("createdAt", -1)
    memories = [_serialize_memory(document) for document in cursor]

    print(f"[Memories List] Returning {len(memories)} memories")
    for mem in memories:
        print(f"  - {mem.get('title')}: summary length = {len(mem.get('summary', ''))}")

    return [MemoryListItem.model_validate(memory) for memory in memories]


@router.get("/memory/{id}", response_model=MemoryDetailResponse)
def get_memory_by_id(id: str) -> MemoryDetailResponse:
    object_id = _parse_object_id(id)
    collection = get_memories_collection()

    document = collection.find_one({"_id": object_id})
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )

    serialized = _serialize_memory(document)
    print(f"[Memory Detail] Retrieved: {serialized.get('title')}")
    print(f"  - Type: {serialized.get('type')}")
    print(f"  - Summary length: {len(serialized.get('summary', ''))}")
    print(f"  - Tags: {serialized.get('tags')}")

    return MemoryDetailResponse.model_validate(serialized)


@router.delete("/memory/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(id: str) -> None:
    object_id = _parse_object_id(id)
    collection = get_memories_collection()

    # Delete from MongoDB
    result = collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found",
        )

    # Delete from ChromaDB (non-fatal if it fails)
    try:
        chroma_collection = get_chroma_collection()
        chroma_collection.delete(ids=[id])
    except Exception:
        pass

    return None
