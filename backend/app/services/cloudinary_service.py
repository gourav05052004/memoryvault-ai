import os
from pathlib import Path

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile, status


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


_CLOUDINARY_CONFIGURED = False


def _configure_cloudinary() -> None:
    global _CLOUDINARY_CONFIGURED
    if _CLOUDINARY_CONFIGURED:
        return

    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()

    if not cloud_name or not api_key or not api_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary credentials are not configured",
        )

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    _CLOUDINARY_CONFIGURED = True


def upload_file_to_cloudinary(file: UploadFile, resource_type: str = "auto") -> dict:
    """
    Upload a file to Cloudinary with public access.
    
    Args:
        file: The file to upload
        resource_type: "auto" (default), "image", "video", or "raw"
    """
    _configure_cloudinary()

    try:
        file.file.seek(0)
        
        upload_result = cloudinary.uploader.upload(
            file.file,
            resource_type=resource_type,
            folder="memoryvault",
            use_filename=True,
            unique_filename=True,
            overwrite=False,
            access_mode="public",
            type="upload",
        )
        file.file.seek(0)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload file to cloud storage",
        ) from exc

    secure_url = upload_result.get("secure_url")
    public_id = upload_result.get("public_id")
    resource_type = upload_result.get("resource_type")

    if not secure_url or not public_id or not resource_type:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from cloud storage provider",
        )

    return {
        "secure_url": secure_url,
        "public_id": public_id,
        "resource_type": resource_type,
    }


def get_signed_url(public_id: str, resource_type: str = "raw") -> str:
    """Generate a signed URL for viewing private resources like PDFs."""
    _configure_cloudinary()
    
    # Generate signed URL with 1 hour expiration
    signed_url = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type=resource_type,
        type="upload",
        sign_url=True,
        secure=True,
    )[0]
    
    return signed_url
