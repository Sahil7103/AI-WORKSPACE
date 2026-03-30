"""
File handling utilities.
"""

import os
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings
from app.utils.logger import logger


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_uploaded_file(filename: str, file: BinaryIO) -> str:
    """Save an uploaded file and return its path."""
    try:
        # Validate file size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        max_size = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_size:
            raise ValueError(
                f"File size exceeds maximum of {settings.max_file_size_mb}MB"
            )

        # Create safe filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        file_path = UPLOAD_DIR / safe_filename

        # Save file
        with open(file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)

        logger.info(f"File saved: {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        raise


async def read_file_content(file_path: str) -> str:
    """Read content from a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise


async def delete_file(file_path: str):
    """Delete a file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        raise
