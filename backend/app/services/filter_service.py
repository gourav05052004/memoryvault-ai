from bson import ObjectId
from pymongo.collection import Collection

from ..db.mongo import get_memories_collection
from .query_parser_service import ParsedQuery


def build_filter_query(user_id: ObjectId, parsed_query: ParsedQuery) -> dict:
    """
    Build MongoDB filter query based on parsed user query.
    
    Applies:
    - User ID filtering (JWT-based isolation)
    - Date range filtering if present
    - Memory type filtering if present
    """
    filter_query: dict = {"userId": user_id}

    # Apply date range filtering
    if parsed_query.date_range:
        date_range = parsed_query.date_range
        start_date = date_range.get("start")
        end_date = date_range.get("end")

        if start_date and end_date:
            filter_query["createdAt"] = {
                "$gte": start_date,
                "$lte": end_date,
            }

    # Apply memory type filtering
    if parsed_query.memory_type:
        filter_query["type"] = parsed_query.memory_type

    return filter_query


def apply_keyword_filters(memories: list[dict], keywords: list[str]) -> list[dict]:
    """
    Apply keyword-based filtering to memories.
    
    Scores memories based on keyword matches in:
    - Title (highest weight)
    - Tags (high weight)
    - Summary (medium weight)
    - Extracted text (low weight)
    """
    if not keywords:
        return memories

    def keyword_score(memory: dict) -> float:
        """Calculate relevance score for a memory based on keywords."""
        score = 0.0

        title = str(memory.get("title", "")).lower()
        summary = str(memory.get("summary", "")).lower()
        tags = [str(tag).lower() for tag in memory.get("tags", [])]
        extracted_text = str(memory.get("extractedText", "")).lower()[:2000]

        for keyword in keywords:
            keyword_lower = keyword.lower().strip()

            # Title match (weight: 4.0)
            if keyword_lower in title:
                score += 4.0

            # Tags match (weight: 3.0)
            for tag in tags:
                if keyword_lower in tag or tag in keyword_lower:
                    score += 3.0
                    break

            # Summary match (weight: 2.0)
            if keyword_lower in summary:
                score += 2.0

            # Extracted text match (weight: 1.0)
            if keyword_lower in extracted_text:
                score += 1.0

        return score

    # Score and filter
    scored_memories = [
        (keyword_score(memory), idx, memory)
        for idx, memory in enumerate(memories)
    ]

    # Sort by score (descending), then by original order
    scored_memories.sort(key=lambda x: (-x[0], x[1]))

    # Return only memories with non-zero score
    return [memory for score, _, memory in scored_memories if score > 0]


def filter_user_memories(
    user_id: ObjectId,
    parsed_query: ParsedQuery,
    limit: int = 50,
) -> list[dict]:
    """
    Retrieve and filter user memories based on parsed query.
    
    Steps:
    1. Apply structured filtering (user_id, date_range, type)
    2. Apply keyword-based filtering
    3. Sort by creation date (most recent first)
    4. Return limited results
    """
    # Build MongoDB filter
    filter_query = build_filter_query(user_id, parsed_query)

    # Query MongoDB
    collection = get_memories_collection()
    memories = list(
        collection.find(filter_query)
        .sort("createdAt", -1)
        .limit(limit)
    )

    # Apply keyword filtering
    if parsed_query.keywords:
        memories = apply_keyword_filters(memories, parsed_query.keywords)

    return memories
