import logging
import os
import traceback
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import fitz
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..db.mongo import get_memories_collection
from ..services.supabase_service import upload_file_to_supabase
from ..services.embedding_service import index_memory_vector
from ..services.gemini_service import generate_summary_and_tags
from ..services.ocr_service import extract_text_from_image as extract_text_from_image_ocr

logger = logging.getLogger(__name__)


router = APIRouter(tags=["uploads"])

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


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as document:
            text = "\n".join(page.get_text() for page in document).strip()
            logger.debug(f"Extracted {len(text)} characters from PDF")
            return text
    except Exception as exc:
        logger.error(f"PDF text extraction failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract text from PDF",
        ) from exc


def _extract_text_from_image(file_bytes: bytes) -> str:
	"""Extract text from image using EasyOCR (pure Python, no system dependencies)"""
	try:
		extracted_text = extract_text_from_image_ocr(file_bytes)
		if not extracted_text:
			logger.warning("No text detected in image")
		else:
			logger.debug(f"Extracted {len(extracted_text)} characters from image via EasyOCR")
		return extracted_text
	except ValueError as exc:
		logger.error(f"Invalid image file: {exc}")
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Invalid image file format",
		) from exc
	except RuntimeError as exc:
		logger.error(f"EasyOCR error: {exc}")
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Image processing failed. Please try another image.",
		) from exc
	except Exception as exc:
		logger.error(f"Unexpected OCR error: {type(exc).__name__}: {str(exc)}")
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Failed to process image",
		) from exc


def _insert_memory_document(document: dict) -> str:
    collection = get_memories_collection()
    result = collection.insert_one(document)
    return str(result.inserted_id)


@router.post("/upload/pdf", response_model=UploadMemoryResponse, status_code=status.HTTP_201_CREATED)
def upload_pdf(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    current_user: dict = Depends(get_current_user),
) -> UploadMemoryResponse:
    original_filename = _ensure_filename(file.filename)
    extension = _get_extension(original_filename)

    if file.content_type not in ALLOWED_PDF_MIME_TYPES or extension not in ALLOWED_PDF_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are allowed",
        )

    # Upload PDF to Supabase Storage
    supabase_result = upload_file_to_supabase(file, bucket="memoryvault")
    file_bytes = file.file.read()
    file_size = len(file_bytes)

    extracted_text = _extract_text_from_pdf(file_bytes)
    logger.info(f"PDF text extracted: {len(extracted_text)} chars")

    generated_summary = ""
    generated_tags: list[str] = []
    resolved_title = title if title else Path(original_filename).stem

    try:
        logger.debug(f"Generating summary for PDF: {resolved_title}")
        generated = generate_summary_and_tags(extracted_text, resolved_title)
        generated_summary = str(generated.get("summary", "")).strip()
        generated_tags = [tag for tag in generated.get("tags", []) if isinstance(tag, str)]
        logger.info(f"PDF summary generated: {len(generated_summary)} chars, {len(generated_tags)} tags")
    except Exception as exc:
        logger.error(f"PDF summary generation failed: {type(exc).__name__}: {str(exc)}")
        logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        generated_summary = ""
        generated_tags = []

    now = datetime.now(timezone.utc)

    document = {
        "userId": current_user["_id"],
        "type": "pdf",
        "title": resolved_title,
        "fileName": original_filename,
        "fileUrl": supabase_result["public_url"],
        "filePath": supabase_result["file_path"],
        "fileType": file.content_type,
        "fileSize": supabase_result["file_size"],
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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector indexing failed: {exc}",
        ) from exc

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
    current_user: dict = Depends(get_current_user),
) -> UploadMemoryResponse:
    original_filename = _ensure_filename(file.filename)
    extension = _get_extension(original_filename)

    if file.content_type not in ALLOWED_IMAGE_MIME_TYPES or extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PNG/JPG/JPEG files are allowed",
        )

    # Upload image to Supabase Storage
    supabase_result = upload_file_to_supabase(file, bucket="memoryvault")
    file_bytes = file.file.read()
    file_size = len(file_bytes)

    extracted_text = _extract_text_from_image(file_bytes)
    logger.info(f"Image text extracted: {len(extracted_text)} chars")

    generated_summary = ""
    generated_tags: list[str] = []
    resolved_title = title if title else Path(original_filename).stem

    try:
        logger.debug(f"Generating summary for image: {resolved_title}")
        generated = generate_summary_and_tags(extracted_text, resolved_title)
        generated_summary = str(generated.get("summary", "")).strip()
        generated_tags = [tag for tag in generated.get("tags", []) if isinstance(tag, str)]
        logger.info(f"Image summary generated: {len(generated_summary)} chars, {len(generated_tags)} tags")
    except Exception as exc:
        logger.error(f"Image summary generation failed: {type(exc).__name__}: {str(exc)}")
        logger.debug(f"Full traceback:\n{traceback.format_exc()}")
        generated_summary = ""
        generated_tags = []

    now = datetime.now(timezone.utc)

    document = {
        "userId": current_user["_id"],
        "type": "image",
        "title": resolved_title,
        "fileName": original_filename,
        "fileUrl": supabase_result["public_url"],
        "filePath": supabase_result["file_path"],
        "fileType": file.content_type,
        "fileSize": supabase_result["file_size"],
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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector indexing failed: {exc}",
        ) from exc

    return UploadMemoryResponse(
        id=inserted_id,
        extractedTextLength=len(extracted_text),
        message="Image uploaded successfully",
        summary=generated_summary,
        tags=generated_tags,
    )
