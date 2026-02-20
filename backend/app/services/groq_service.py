import json
import re
from collections import Counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import GROQ_API_KEY, GROQ_CHAT_MODEL


CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_TEXT_CHARS = 12000
MAX_TAGS = 15
MIN_TAGS = 8
REQUEST_TIMEOUT_SECONDS = 60
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is",
    "it", "its", "of", "on", "or", "that", "the", "to", "was", "were", "will", "with", "this",
    "these", "those", "your", "you", "our", "their", "they", "we", "can", "should", "any",
}


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
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured")

    payload = {
        "model": GROQ_CHAT_MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    }

    req = Request(
        CHAT_COMPLETIONS_URL,
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
        raise RuntimeError(f"Groq API HTTP {exc.code}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Groq API: {exc.reason}") from exc

    parsed = json.loads(raw)
    choices = parsed.get("choices") or []
    if not choices:
        raise RuntimeError("Groq API returned no choices")

    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else ""
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Groq API returned empty content")

    return content.strip()


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


def generate_answer(question: str, memories: list[dict], max_snippet_chars: int = 400) -> str:
    if not memories:
        return "No relevant memories found."

    context_blocks: list[str] = []
    for index, memory in enumerate(memories, start=1):
        snippet = str(memory.get("extractedText", ""))[:max_snippet_chars]
        block = (
            f"Memory {index}:\n"
            f"Title: {memory.get('title', '')}\n"
            f"Type: {memory.get('type', '')}\n"
            f"Summary: {memory.get('summary', '')}\n"
            f"Snippet: {snippet}\n"
        )
        context_blocks.append(block)

    prompt = (
        "Answer the question using ONLY the memory context below. "
        "Do not add facts not present in context. "
        "Return a concise answer in 1-2 short sentences. "
        "Then add a new line starting with 'Sources:' followed by 1-3 memory titles separated by '; '. "
        "Do not include summaries or extra text.\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{''.join(context_blocks)}"
    )

    system_prompt = "You are a precise assistant for memory retrieval and grounding."

    try:
        return _post_chat_completion(prompt=prompt, system_prompt=system_prompt, temperature=0.1)
    except Exception:
        best_title = str(memories[0].get("title", "")).strip() or "relevant memory"

        snippet = str(memories[0].get("summary", "")).strip()
        if not snippet:
            snippet = str(memories[0].get("extractedText", "")).strip()[:220]

        if snippet:
            return (
                f"{snippet}\n"
                f"Sources: {best_title}"
            )

        return (
            f"No concise answer found in the stored memories.\n"
            f"Sources: {best_title}"
        )
