"""
File Upload Utility
Handles PDF file uploads, saves to temp storage, and provides file management.
"""

import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException

# Upload directory — use temp dir for serverless/Render compatibility
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".xlsx", ".txt"}
MAX_FILE_SIZE_MB = 20


async def save_upload(file: UploadFile) -> dict:
    """
    Save an uploaded file to disk with a unique name.
    
    Returns:
        {
            "file_id": str,
            "original_filename": str,
            "saved_path": str,
            "size_bytes": int
        }
    """
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()

    # Validate size
    size_bytes = len(content)
    if size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE_MB}MB"
        )

    # Save with unique name
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{ext}"
    saved_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(saved_path, "wb") as f:
        f.write(content)

    return {
        "file_id": file_id,
        "original_filename": file.filename,
        "saved_path": saved_path,
        "size_bytes": size_bytes,
    }


def delete_upload(file_path: str) -> bool:
    """Delete an uploaded file after processing."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except OSError:
        return False


def cleanup_uploads():
    """Remove all uploaded files. Call periodically or on startup."""
    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR)
        Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
