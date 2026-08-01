"""
routers/upload.py
-----------------
POST /api/upload — accepts a .py file, validates it, saves to uploads/ dir.
Returns a file_id used to reference it in subsequent /scan calls.
"""

import os
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.config import get_settings
from backend.models.schemas import UploadResponse

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a Python source file for security scanning.

    - Only `.py` files are accepted.
    - File size is limited to `MAX_UPLOAD_SIZE_MB` (default 10 MB).
    - Returns a `file_id` to use with `POST /api/scan`.
    """
    # Validate extension
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(
            status_code=400,
            detail="Only Python (.py) files are supported.",
        )

    content = await file.read()

    # Validate size
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {settings.max_upload_size_mb} MB.",
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Save to uploads/ with a unique ID
    file_id = str(uuid.uuid4())
    os.makedirs(settings.uploads_dir, exist_ok=True)
    dest_path = Path(settings.uploads_dir) / f"{file_id}.py"
    dest_path.write_bytes(content)

    logger.info("File uploaded: %s (%d bytes) → %s", file.filename, len(content), dest_path)

    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        size_bytes=len(content),
        message="File uploaded successfully. Use file_id with POST /api/scan.",
    )
