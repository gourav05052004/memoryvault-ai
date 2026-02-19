from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import fitz
import pytesseract
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel
from pytesseract import TesseractNotFoundError

from ..config import TESSERACT_CMD
from ..db.mongo import get_memories_collection
from ..services.embedding_service import index_memory_vector
from ..services.groq_service import generate_summary_and_tags


router = APIRouter(tags=["uploads"])

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_PDF_MIME_TYPES = {"application/pdf"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}

ALLOWED_IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/jpg"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


class UploadMemoryResponse(BaseModel):
    id: str
    extractedTextLength: int
    message: str
    summary: str
    tags: list[str]


def _get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def _ensure_filename(filename: str | None) -> str:
    if filename is None or filename.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    return filename


def _build_unique_filename(filename: str) -> str:
    extension = _get_extension(filename)
    return f"{uuid4().hex}{extension}"


def _save_upload_file(file: UploadFile, destination: Path) -> int:
    file_bytes = file.file.read()
    destination.write_bytes(file_bytes)
    return len(file_bytes)


def _extract_text_from_pdf(file_path: Path) -> str:
    try:
        with fitz.open(file_path) as document:
            text = "\n".join(page.get_text() for page in document).strip()
            print(f"[PDF Extract] Extracted {len(text)} characters from PDF")
            return text
    except Exception as exc:
        print(f"[PDF Extract] Error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract text from PDF",
        ) from exc


def _extract_text_from_image(file_path: Path) -> str:
    try:
        with Image.open(file_path) as image:
            return pytesseract.image_to_string(image).strip()
    except TesseractNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tesseract OCR is not installed or not found in PATH",
        ) from exc
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process image for OCR",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract text from image",
        ) from exc


def _insert_memory_document(document: dict) -> str:
    collection = get_memories_collection()
    result = collection.insert_one(document)
    return str(result.inserted_id)


@router.post("/upload/pdf", response_model=UploadMemoryResponse, status_code=status.HTTP_201_CREATED)
def upload_pdf(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
) -> UploadMemoryResponse:
    original_filename = _ensure_filename(file.filename)
    extension = _get_extension(original_filename)

    if file.content_type not in ALLOWED_PDF_MIME_TYPES or extension not in ALLOWED_PDF_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are allowed",
        )

    unique_filename = _build_unique_filename(original_filename)
    destination = UPLOADS_DIR / unique_filename
    file_size = _save_upload_file(file, destination)

    extracted_text = _extract_text_from_pdf(destination)
    print(f"[PDF] Extracted text length: {len(extracted_text)}")

    generated_summary = ""
    generated_tags: list[str] = []
    resolved_title = title if title else Path(original_filename).stem

    try:
        print(f"[PDF] Generating summary for: {resolved_title}")
        generated = generate_summary_and_tags(extracted_text, resolved_title)
        generated_summary = str(generated.get("summary", "")).strip()
        generated_tags = [tag for tag in generated.get("tags", []) if isinstance(tag, str)]
        print(f"[PDF] Generated summary: {generated_summary[:100]}...")
        print(f"[PDF] Generated tags: {generated_tags}")
    except Exception as exc:
        print(f"[PDF] Error generating summary: {type(exc).__name__}")
        print(f"[PDF] Error details: {str(exc)}")
        import traceback
        print(f"[PDF] Full traceback:\n{traceback.format_exc()}")
        generated_summary = ""
        generated_tags = []

    now = datetime.now(timezone.utc)

    document = {
        "type": "pdf",
        "title": resolved_title,
        "fileName": unique_filename,
        "fileUrl": f"/uploads/{unique_filename}",
        "fileType": file.content_type,
        "fileSize": file_size,
        "extractedText": extracted_text,
        "summary": generated_summary,
        "tags": generated_tags,
        "createdAt": now,
        "updatedAt": now,
    }

    inserted_id = _insert_memory_document(document)

    try:
        index_memory_vector(
            memory_id=inserted_id,
            memory_type="pdf",
            title=resolved_title,
            tags=generated_tags,
            summary=generated_summary,
            extracted_text=extracted_text,
            created_at=now,
        )
    except Exception:
        pass

    return UploadMemoryResponse(
        id=inserted_id,
        extractedTextLength=len(extracted_text),
        message="PDF uploaded successfully",
        summary=generated_summary,
        tags=generated_tags,
    )


@router.post("/upload/image", response_model=UploadMemoryResponse, status_code=status.HTTP_201_CREATED)
def upload_image(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
) -> UploadMemoryResponse:
    original_filename = _ensure_filename(file.filename)
    extension = _get_extension(original_filename)

    if file.content_type not in ALLOWED_IMAGE_MIME_TYPES or extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PNG/JPG/JPEG files are allowed",
        )

    unique_filename = _build_unique_filename(original_filename)
    destination = UPLOADS_DIR / unique_filename
    file_size = _save_upload_file(file, destination)

    extracted_text = _extract_text_from_image(destination)
    print(f"[IMAGE] Extracted text length: {len(extracted_text)}")

    generated_summary = ""
    generated_tags: list[str] = []
    resolved_title = title if title else Path(original_filename).stem

    try:
        print(f"[IMAGE] Generating summary for: {resolved_title}")
        generated = generate_summary_and_tags(extracted_text, resolved_title)
        generated_summary = str(generated.get("summary", "")).strip()
        generated_tags = [tag for tag in generated.get("tags", []) if isinstance(tag, str)]
        print(f"[IMAGE] Generated summary: {generated_summary[:100]}...")
        print(f"[IMAGE] Generated tags: {generated_tags}")
    except Exception as exc:
        print(f"[IMAGE] Error generating summary: {type(exc).__name__}")
        print(f"[IMAGE] Error details: {str(exc)}")
        import traceback
        print(f"[IMAGE] Full traceback:\n{traceback.format_exc()}")
        generated_summary = ""
        generated_tags = []

    now = datetime.now(timezone.utc)

    document = {
        "type": "image",
        "title": resolved_title,
        "fileName": unique_filename,
        "fileUrl": f"/uploads/{unique_filename}",
        "fileType": file.content_type,
        "fileSize": file_size,
        "extractedText": extracted_text,
        "summary": generated_summary,
        "tags": generated_tags,
        "createdAt": now,
        "updatedAt": now,
    }

    inserted_id = _insert_memory_document(document)

    try:
        index_memory_vector(
            memory_id=inserted_id,
            memory_type="image",
            title=resolved_title,
            tags=generated_tags,
            summary=generated_summary,
            extracted_text=extracted_text,
            created_at=now,
        )
    except Exception:
        pass

    return UploadMemoryResponse(
        id=inserted_id,
        extractedTextLength=len(extracted_text),
        message="Image uploaded successfully",
        summary=generated_summary,
        tags=generated_tags,
    )
