import json
import logging
import re
from datetime import datetime, timedelta

from google import genai
from google.genai import types

from ..config import GEMINI_API_KEY, GEMINI_CHAT_MODEL


REQUEST_TIMEOUT_SECONDS = 30
_GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
_FALLBACK_CHAT_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]
logger = logging.getLogger(__name__)


class ParsedQuery:
    """Structured representation of a user query."""
    
    def __init__(
        self,
        original_question: str,
        date_filter: str | None = None,
        date_range: dict | None = None,
        keywords: list[str] | None = None,
        memory_type: str | None = None,
    ):
        self.original_question = original_question
        self.date_filter = date_filter  # e.g., "last_week", "january", "last_month"
        self.date_range = date_range  # e.g., {"start": datetime, "end": datetime}
        self.keywords = keywords or []
        self.memory_type = memory_type  # e.g., "pdf", "image", "note"


def _chat_model_candidates() -> list[str]:
    ordered = [GEMINI_CHAT_MODEL, *_FALLBACK_CHAT_MODELS]
    unique: list[str] = []
    for model in ordered:
        if model and model not in unique:
            unique.append(model)
    return unique


def _post_gemini_parsing(prompt: str, system_prompt: str) -> str:
    """Call Gemini API for query parsing."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    if _GEMINI_CLIENT is None:
        raise RuntimeError("Gemini client is not initialized")

    combined_prompt = f"System instructions:\n{system_prompt}\n\nUser prompt:\n{prompt}"

    last_error: Exception | None = None

    for model_name in _chat_model_candidates():
        try:
            logger.debug("[QUERY_PARSER] Trying model=%s with thinking_config", model_name)
            response = _GEMINI_CLIENT.models.generate_content(
                model=model_name,
                contents=combined_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                ),
            )
        except Exception as thinking_exc:
            logger.warning(
                "[QUERY_PARSER] thinking_config call failed for model=%s: %s",
                model_name,
                thinking_exc,
            )
            try:
                logger.debug("[QUERY_PARSER] Retrying model=%s without thinking_config", model_name)
                response = _GEMINI_CLIENT.models.generate_content(
                    model=model_name,
                    contents=combined_prompt,
                    config=types.GenerateContentConfig(temperature=0.1),
                )
            except Exception as plain_exc:
                logger.warning(
                    "[QUERY_PARSER] plain call failed for model=%s: %s",
                    model_name,
                    plain_exc,
                )
                last_error = plain_exc
                continue

        content = getattr(response, "text", "")
        if isinstance(content, str) and content.strip():
            logger.info("[QUERY_PARSER] Parsed query successfully using model=%s", model_name)
            return content.strip()

        last_error = RuntimeError(f"Gemini API returned empty content for model {model_name}")

    raise RuntimeError(f"Gemini API call failed across model fallbacks: {last_error}")


def _extract_json_from_response(raw_text: str) -> dict:
    """Extract JSON from model response."""
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


def _convert_date_filter_to_range(date_filter: str | None) -> dict | None:
    """Convert date filter string to datetime range."""
    if not date_filter:
        return None

    now = datetime.utcnow()
    date_filter_lower = date_filter.lower().strip()

    # Last N days/weeks/months
    if "last" in date_filter_lower:
        if "week" in date_filter_lower or "7 days" in date_filter_lower:
            start_date = now - timedelta(days=7)
            return {"start": start_date, "end": now}
        elif "month" in date_filter_lower or "30 days" in date_filter_lower:
            start_date = now - timedelta(days=30)
            return {"start": start_date, "end": now}
        elif "3 months" in date_filter_lower:
            start_date = now - timedelta(days=90)
            return {"start": start_date, "end": now}
        elif "year" in date_filter_lower:
            start_date = now - timedelta(days=365)
            return {"start": start_date, "end": now}
        elif "day" in date_filter_lower:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return {"start": start_date, "end": now}

    # Today
    if "today" in date_filter_lower:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return {"start": start_date, "end": now}

    # Month names
    month_map = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    }

    for month_name, month_num in month_map.items():
        if month_name in date_filter_lower:
            # Check if year is specified
            year_match = re.search(r"\b(202[0-9]|19[0-9]{2})\b", date_filter_lower)
            year = int(year_match.group(1)) if year_match else now.year

            start_date = datetime(year, month_num, 1)
            if month_num == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
            else:
                end_date = datetime(year, month_num + 1, 1) - timedelta(seconds=1)

            return {"start": start_date, "end": end_date}

    return None


def parse_user_query(question: str) -> ParsedQuery:
    """
    Parse user question to extract structured metadata.
    
    Uses Gemini for lightweight query interpretation.
    Returns ParsedQuery with date filters, keywords, and type information.
    """
    if not question or not question.strip():
        return ParsedQuery(original_question=question)

    prompt = f"""Analyze this user question about their memories and extract structured metadata.
Return ONLY valid JSON with these EXACT keys:
- date_filter: null or a string describing the time period (e.g., "last week", "january", "last month", "today")
- keywords: array of 1-3 important keywords/search terms from the question
- memory_type: null or one of: "pdf", "image", "note"

Be conservative - only extract information clearly present in the question.
If not explicitly mentioned, set to null.

Examples:
Q: "What was discussed in my ML class last week?"
{{"date_filter": "last_week", "keywords": ["ML class", "discussion"], "memory_type": null}}

Q: "Show the resume I uploaded in January"
{{"date_filter": "january", "keywords": ["resume"], "memory_type": "pdf"}}

Q: "What were my project ideas related to healthcare?"
{{"date_filter": null, "keywords": ["project ideas", "healthcare"], "memory_type": null}}

User question: {question}

Return ONLY the JSON object, no other text."""

    system_prompt = (
        "You are a query parser. Extract metadata from user questions about memories. "
        "Return only valid JSON with the specified keys. Be conservative and only extract "
        "clearly mentioned information."
    )

    try:
        response = _post_gemini_parsing(prompt=prompt, system_prompt=system_prompt)
        parsed_data = _extract_json_from_response(response)

        date_filter = parsed_data.get("date_filter")
        keywords = parsed_data.get("keywords", [])
        memory_type = parsed_data.get("memory_type")

        # Validate memory_type
        if memory_type and memory_type not in ["pdf", "image", "note"]:
            memory_type = None

        # Ensure keywords is a list
        if not isinstance(keywords, list):
            keywords = []

        # Convert date_filter to date_range
        date_range = _convert_date_filter_to_range(date_filter)

        return ParsedQuery(
            original_question=question,
            date_filter=date_filter,
            date_range=date_range,
            keywords=[str(kw).strip() for kw in keywords if kw],
            memory_type=memory_type,
        )

    except Exception as e:
        logger.exception("[QUERY_PARSER] Falling back to basic parsing due to model error")
        return ParsedQuery(original_question=question)
