"""
File handling utilities.
"""

import os
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from fastapi import UploadFile

from app.core.config import settings
from app.utils.logger import logger


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_uploaded_file(upload_file: UploadFile) -> tuple[str, int]:
    """Save an uploaded file and return its path plus byte size."""
    try:
        file_bytes = await upload_file.read()
        file_size = len(file_bytes)

        max_size = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_size:
            raise ValueError(
                f"File size exceeds maximum of {settings.max_file_size_mb}MB"
            )

        safe_filename = "".join(
            c for c in upload_file.filename if c.isalnum() or c in "._-"
        )
        file_path = UPLOAD_DIR / safe_filename

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        logger.info(f"File saved: {file_path}")
        return str(file_path), file_size

    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        raise


def _read_text_file(file_path: str) -> str:
    """Read plain-text content with a safe fallback."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1", errors="ignore") as f:
            return f.read()


def _read_docx_content(file_path: str) -> str:
    """Extract basic text content from a DOCX file without extra dependencies."""
    try:
        with zipfile.ZipFile(file_path) as archive:
            xml_bytes = archive.read("word/document.xml")

        root = ET.fromstring(xml_bytes)
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        text_nodes = [node.text for node in root.findall(".//w:t", namespace) if node.text]
        return "\n".join(text_nodes).strip()
    except Exception as exc:
        logger.warning(f"Could not extract DOCX content from {file_path}: {exc}")
        return ""


def _read_pdf_content(file_path: str) -> str:
    """Extract PDF text when optional parsers are available."""
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(file_path)
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except ModuleNotFoundError:
        logger.warning(
            "PDF parser not installed; storing uploaded PDF without extracted text"
        )
        return ""
    except Exception as exc:
        logger.warning(f"Could not extract PDF content from {file_path}: {exc}")
        return ""


async def read_file_content(file_path: str, file_type: str) -> str:
    """Read content from a supported file type."""
    try:
        normalized_type = (file_type or "").lower()
        if normalized_type == "docx":
            return _read_docx_content(file_path)
        if normalized_type == "pdf":
            return _read_pdf_content(file_path)
        return _read_text_file(file_path)
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
