"""OCR service using OCR.space API for text extraction from images."""

import logging

import httpx

from ..config import OCR_SPACE_API_KEY


logger = logging.getLogger(__name__)

OCR_SPACE_URL = "https://api.ocr.space/parse/image"
OCR_TIMEOUT_SECONDS = 12.0


async def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image bytes using OCR.space API.

    Args:
        image_bytes: Raw image bytes (PNG, JPEG, etc.)

    Returns:
        Extracted text as a single string. Returns an empty string when no text is found.

    Raises:
        RuntimeError: If OCR request/response handling fails
        ValueError: If input image bytes are empty
    """
    if not image_bytes:
        raise ValueError("Image bytes are empty")

    if not OCR_SPACE_API_KEY:
        logger.error("OCR_SPACE_API_KEY is not configured")
        raise RuntimeError("OCR_SPACE_API_KEY is missing")

    headers = {"apikey": OCR_SPACE_API_KEY}
    data = {
        "language": "eng",
        "isOverlayRequired": "false",
        "OCREngine": "2",
    }
    files = {
        "file": ("image.jpg", image_bytes, "application/octet-stream"),
    }

    try:
        async with httpx.AsyncClient(timeout=OCR_TIMEOUT_SECONDS) as client:
            response = await client.post(
                OCR_SPACE_URL,
                headers=headers,
                data=data,
                files=files,
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.TimeoutException as exc:
        logger.error("OCR.space request timed out after %.1fs", OCR_TIMEOUT_SECONDS)
        raise RuntimeError("OCR request timed out") from exc
    except httpx.HTTPStatusError as exc:
        logger.error("OCR.space HTTP error: %s - %s", exc.response.status_code, exc.response.text)
        raise RuntimeError("OCR request failed") from exc
    except Exception as exc:
        logger.error("OCR.space request error: %s: %s", type(exc).__name__, str(exc))
        raise RuntimeError("Failed to call OCR service") from exc

    exit_code = payload.get("OCRExitCode")
    if exit_code != 1:
        error_message = payload.get("ErrorMessage") or payload.get("ErrorDetails") or "Unknown OCR error"
        logger.error("OCR.space unsuccessful OCRExitCode=%s, error=%s", exit_code, error_message)
        raise RuntimeError(f"OCR failed with exit code {exit_code}")

    parsed_results = payload.get("ParsedResults") or []
    parsed_texts = [
        str(result.get("ParsedText", "")).strip()
        for result in parsed_results
        if isinstance(result, dict)
    ]
    extracted_text = "\n".join(text for text in parsed_texts if text).strip()

    if not extracted_text:
        logger.warning("OCR.space returned success but no text was extracted")
        return ""

    logger.debug("OCR.space extracted %s characters", len(extracted_text))
    return extracted_text
