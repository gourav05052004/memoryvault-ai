#!/usr/bin/env python3
"""
Rebuild Chroma vector index from existing Mongo memories.

Usage:
    python reindex_chroma_from_mongo.py
    python reindex_chroma_from_mongo.py --no-reset
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from app.db.chroma import get_chroma_collection, reset_chroma_collection
from app.db.mongo import get_memories_collection
from app.services.embedding_service import index_memory_vector


def _normalize_tags(raw_tags) -> list[str]:
    if not isinstance(raw_tags, list):
        return []
    return [str(tag).strip() for tag in raw_tags if str(tag).strip()]


def _normalize_created_at(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        text = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return datetime.now(timezone.utc)
    return datetime.now(timezone.utc)


def _reindex_memories(reset_first: bool) -> tuple[int, int]:
    if reset_first:
        reset_chroma_collection()
    else:
        get_chroma_collection()

    collection = get_memories_collection()
    cursor = collection.find({}).sort("createdAt", 1)

    indexed = 0
    skipped = 0

    for document in cursor:
        memory_id = str(document.get("_id", "")).strip()
        if not memory_id:
            skipped += 1
            continue

        memory_type = str(document.get("type", "note") or "note").strip()
        title = str(document.get("title", "Untitled") or "Untitled").strip()
        summary = str(document.get("summary", "") or "").strip()
        extracted_text = str(document.get("extractedText", "") or "").strip()
        tags = _normalize_tags(document.get("tags", []))
        created_at = _normalize_created_at(document.get("createdAt"))

        if not extracted_text and not summary and not title:
            skipped += 1
            continue

        try:
            index_memory_vector(
                memory_id=memory_id,
                memory_type=memory_type,
                title=title,
                tags=tags,
                summary=summary,
                extracted_text=extracted_text,
                created_at=created_at,
            )
            indexed += 1
            if indexed % 10 == 0:
                print(f"[REINDEX] Indexed {indexed} memories...")
        except Exception as exc:
            skipped += 1
            print(f"[REINDEX] Skipped memory {memory_id}: {exc}")

    return indexed, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Reindex Chroma vectors from Mongo memories")
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Do not clear Chroma before reindexing (upsert into existing collection)",
    )
    args = parser.parse_args()

    reset_first = not args.no_reset
    mode = "RESET + REBUILD" if reset_first else "UPSERT"

    print("\n" + "=" * 60)
    print("Chroma Reindex Tool")
    print("=" * 60)
    print(f"Mode: {mode}")
    print("\nThis reads all memories from Mongo and (re)creates Chroma vectors.")

    if reset_first:
        confirm = input("Continue and reset Chroma collection? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("\nCancelled.")
            print("=" * 60 + "\n")
            return

    indexed, skipped = _reindex_memories(reset_first=reset_first)

    print("\nDone.")
    print(f"Indexed: {indexed}")
    print(f"Skipped: {skipped}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
