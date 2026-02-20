import os
from pathlib import Path
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# Lazy import to avoid errors if supabase is not installed
_supabase_client = None


def _get_supabase_client():
    """Get or initialize the Supabase client."""
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    try:
        from supabase import create_client
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase SDK not installed. Run: pip install supabase",
        )
    
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = os.getenv("SUPABASE_KEY", "").strip()
    
    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase credentials are not configured. Add SUPABASE_URL and SUPABASE_KEY to .env",
        )
    
    _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client


def upload_file_to_supabase(file: UploadFile, bucket: str = "memoryvault") -> dict:
    """
    Upload a file to Supabase Storage.
    
    Args:
        file: The file to upload
        bucket: The Supabase bucket name (default: "memoryvault")
    
    Returns:
        dict with: file_path (relative), public_url (full URL), file_name
    """
    try:
        client = _get_supabase_client()
        
        # Generate a unique file path
        original_filename = file.filename or "file"
        file_extension = Path(original_filename).suffix
        file_stem = Path(original_filename).stem
        
        # Create path: bucket/timestamp_filename.ext
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        file_path = f"{file_stem}_{unique_id}{file_extension}"
        
        # Read file content
        file.file.seek(0)
        file_content = file.file.read()
        file.file.seek(0)
        
        # Upload to Supabase
        response = client.storage.from_(bucket).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type},
        )
        
        # Get public URL
        public_url = client.storage.from_(bucket).get_public_url(file_path)
        
        return {
            "file_path": file_path,
            "public_url": public_url,
            "file_name": original_filename,
            "file_size": len(file_content),
        }
        
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Supabase upload error: {type(exc).__name__}: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to upload file to Supabase: {str(exc)}",
        ) from exc


def delete_file_from_supabase(file_path: str, bucket: str = "memoryvault") -> bool:
    """Delete a file from Supabase Storage."""
    try:
        client = _get_supabase_client()
        client.storage.from_(bucket).remove([file_path])
        return True
    except Exception as exc:
        print(f"Supabase delete error: {type(exc).__name__}: {str(exc)}")
        return False
