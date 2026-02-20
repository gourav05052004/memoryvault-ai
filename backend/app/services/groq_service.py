import json
import re
from collections import Counter

from groq import Groq

from ..config import GROQ_API_KEY, GROQ_CHAT_MODEL


MAX_TEXT_CHARS = 12000
MAX_TAGS = 15
MIN_TAGS = 8
REQUEST_TIMEOUT_SECONDS = 60
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is",
    "it", "its", "of", "on", "or", "that", "the", "to", "was", "were", "will", "with", "this",
    "these", "those", "your", "you", "our", "their", "they", "we", "can", "should", "any",
}

_GROQ_SETTINGS = {
    "api_key": GROQ_API_KEY,
    "model": GROQ_CHAT_MODEL,
}
_GROQ_CLIENT = Groq(api_key=_GROQ_SETTINGS["api_key"]) if _GROQ_SETTINGS["api_key"] else None


def _truncate_text(text: str) -> str:
    cleaned_text = text.strip()
    if len(cleaned_text) <= MAX_TEXT_CHARS:
        return cleaned_text
    return cleaned_text[:MAX_TEXT_CHARS]


def _extract_json_block(raw_text: str) -> dict:
    candidate = raw_text.strip()

    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?", "", candidate).strip()
        if candidate.endswith("```"):
            candidate = candidate[:-3].strip()

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", candidate)
        if not match:
            raise
        return json.loads(match.group(0))


def _clean_tags(tags: list) -> list[str]:
    cleaned_tags: list[str] = []

    for raw_tag in tags:
        if not isinstance(raw_tag, str):
            continue

        normalized = raw_tag.strip().lstrip("#")
        normalized = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
        if not normalized:
            continue
        if normalized not in cleaned_tags:
            cleaned_tags.append(normalized)
        if len(cleaned_tags) >= MAX_TAGS:
            break

    return cleaned_tags


def _build_fallback_summary_and_tags(text: str, title: str) -> dict:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return {
            "summary": f"{title.strip() or 'Memory'} was saved, but no extractable text was found.",
            "tags": ["memory", "document", "saved", "content", "review"],
        }

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    summary_lines = meaningful_sentences[:2] if meaningful_sentences else [cleaned[:240]]
    fallback_summary = "\n".join(summary_lines).strip()[:700]

    words = re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", cleaned.lower())
    filtered_words = [word for word in words if word not in STOP_WORDS]
    counts = Counter(filtered_words)

    fallback_tags: list[str] = []
    title_tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", title.lower())
    for token in title_tokens:
        if token not in fallback_tags:
            fallback_tags.append(token)

    for word, _ in counts.most_common(MAX_TAGS):
        if word not in fallback_tags:
            fallback_tags.append(word)
        if len(fallback_tags) >= MAX_TAGS:
            break

    if len(fallback_tags) < MIN_TAGS:
        for default_tag in [
            "memory", "document", "notes", "reference", "important", "archive",
            "content", "information", "data", "resource", "saved", "knowledge"
        ]:
            if default_tag not in fallback_tags:
                fallback_tags.append(default_tag)
            if len(fallback_tags) >= MIN_TAGS:
                break

    return {
        "summary": fallback_summary,
        "tags": fallback_tags[:MAX_TAGS],
    }


def _post_chat_completion(prompt: str, system_prompt: str, temperature: float = 0.2) -> str:
    if not _GROQ_SETTINGS["api_key"]:
        raise RuntimeError("GROQ_API_KEY is not configured")
    if _GROQ_CLIENT is None:
        raise RuntimeError("Groq client is not initialized")

    try:
        response = _GROQ_CLIENT.chat.completions.create(
            model=_GROQ_SETTINGS["model"],
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:
        raise RuntimeError(f"Groq SDK call failed: {exc}") from exc

    choices = getattr(response, "choices", None) or []
    if not choices:
        raise RuntimeError("Groq API returned no choices")

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", "") if message else ""
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Groq API returned empty content")

    return content.strip()


def generate_direct_answer(question: str) -> str:
    if not question.strip():
        raise RuntimeError("Question cannot be empty")

    system_prompt = (
        "You are a helpful assistant. Answer the user's question directly and concisely."
    )
    return _post_chat_completion(
        prompt=question.strip(),
        system_prompt=system_prompt,
        temperature=0.2,
    )


def generate_summary_and_tags(text: str, title: str) -> dict:
    truncated_text = _truncate_text(text)
    if not truncated_text:
        return _build_fallback_summary_and_tags(text=text, title=title)

    prompt = (
        "Return ONLY valid JSON with keys summary and tags. "
        "Summary rules: 2 to 4 short lines, plain text, remove noisy symbols, fix spacing, "
        "and keep clean sentence case. "
        "Tags rules: Generate 10 to 15 diverse tags for optimal searchability. "
        "Include multiple types of tags: "
        "(1) Main topics/subjects, "
        "(2) Categories or domains (e.g., science, business, education, technical), "
        "(3) Key concepts or themes, "
        "(4) Named entities (people, places, organizations if present), "
        "(5) Action verbs or processes mentioned, "
        "(6) Temporal markers (dates, time periods if present), "
        "(7) Related keywords for search. "
        "Keep tags short (1-3 words), lowercase, no hashtags, no emojis.\n\n"
        f"Title: {title}\n"
        f"Text:\n{truncated_text}\n\n"
        "Output format:\n"
        '{"summary": "...", "tags": ["tag1", "tag2", ...]}'
    )

    system_prompt = (
        "You organize memory records, clean noisy text, and strictly return valid JSON. "
        "Never include markdown or extra keys."
    )

    try:
        raw_response = _post_chat_completion(prompt=prompt, system_prompt=system_prompt)
        parsed = _extract_json_block(raw_response)

        summary = str(parsed.get("summary", "")).strip()
        tags = _clean_tags(parsed.get("tags", []))

        if not summary or len(tags) < MIN_TAGS:
            fallback = _build_fallback_summary_and_tags(text=truncated_text, title=title)
            if not summary:
                summary = fallback["summary"]
            if len(tags) < MIN_TAGS:
                tags = fallback["tags"]

        return {
            "summary": summary,
            "tags": tags[:MAX_TAGS],
        }
    except Exception:
        return _build_fallback_summary_and_tags(text=truncated_text, title=title)


def generate_answer(question: str, memories: list[dict], max_snippet_chars: int = 8000) -> str:
    """
    Generate grounded answer based on retrieved memories using Groq LLM.
    
    Optimized for extracting structured data from documents.
    """
    if not memories:
        return "No relevant memories found."

    context_blocks: list[str] = []
    for index, memory in enumerate(memories, start=1):
        snippet = str(memory.get("extractedText", ""))[:max_snippet_chars]
        summary = str(memory.get("summary", "")).strip()
        memory_type = str(memory.get("type", "")).upper()
        memory_title = str(memory.get("title", "Memory"))

        # DEBUG: Log what we're working with
        print(f"\n[DEBUG] Memory {index}:")
        print(f"  Title: {memory_title}")
        print(f"  Type: {memory_type}")
        print(f"  Extracted Text Length: {len(snippet)} chars")
        print(f"  Summary: {summary[:100]}...")
        print(f"  First 500 chars of content: {snippet[:500]}...")

        block = (
            f"Memory {index}:\n"
            f"Title: {memory_title}\n"
            f"Type: {memory_type}\n"
            f"Content:\n{snippet}\n"
        )

        context_blocks.append(block)

    # Smarter prompt for structured data extraction
    prompt = (
        "You are extracting SPECIFIC information from documents. "
        "Your task is to find the answer to the user's question - NOT to answer about other fields.\n\n"
        "CRITICAL RULES:\n"
        "1. Focus on answering ONLY the exact question asked. Ignore information about other fields.\n"
        "2. Look for EXACT FIELD NAMES in the content that match the question:\n"
        "   - If asking about 'Reg No', find 'Reg No' field\n"
        "   - If asking about 'Purpose of Visit', find 'Purpose of Visit' field\n"
        "   - If asking about 'Room', find 'Room' field\n"
        "3. Extract only the VALUE (not the field name or surrounding text)\n"
        "4. Return ONLY the extracted value in 1-2 sentences maximum.\n"
        "5. Add 'Source: [Memory Title]' on a new line.\n"
        "6. If not found after careful search, say 'Not found in memories.'\n"
        "7. Double-check that your answer is relevant to the question asked.\n\n"
        f"User Question: {question}\n\n"
        f"Document Content:\n{''.join(context_blocks)}\n"
        "---\n"
        f"User asked: {question}\n"
        "Find the answer to this specific question only. Do not return information about other fields."
    )

    print(f"\n[DEBUG] Sending to Groq:")
    print(f"  Question: {question}")
    print(f"  Prompt length: {len(prompt)} chars")
    print(f"  Context blocks: {len(context_blocks)}")
    print(f"  First 1000 chars of prompt:\n{prompt[:1000]}")

    system_prompt = (
        "You are an expert at extracting specific information from documents. "
        "You carefully read the full content and identify field names and their values. "
        "You extract data accurately and concisely. "
        "You never fabricate information. "
        "You always cite your source."
    )

    try:
        answer = _post_chat_completion(prompt=prompt, system_prompt=system_prompt, temperature=0.1)
        print(f"\n[DEBUG] Groq Response: {answer}")
        print(f"[DEBUG] Question: {question}\n")
        
        # Post-process to enforce 1-2 sentences max
        sentences = answer.split('\n')
        source_line = ""
        answer_parts = []
        
        for line in sentences:
            if line.strip().lower().startswith("source:"):
                source_line = line.strip()
            else:
                answer_parts.append(line.strip())
        
        answer_text = " ".join(answer_parts).strip()
        sentence_list = re.split(r'(?<=[.!?])\s+', answer_text)
        limited_answer = " ".join(sentence_list[:2])
        
        if source_line:
            return f"{limited_answer}\n\nSource: {source_line.replace('Source: ', '')}"
        return limited_answer
    except Exception as e:
        raise RuntimeError(f"LLM answer generation failed: {e}") from e

