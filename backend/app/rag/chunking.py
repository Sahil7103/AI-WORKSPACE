"""
Document chunking strategies.
"""

from typing import List


class DocumentChunker:
    """Split documents into chunks for embedding."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize chunker.

        Args:
            chunk_size: Number of characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text to chunk

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            # Get chunk
            end = min(start + self.chunk_size, len(text))
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            # Move to next chunk with overlap
            start = end - self.chunk_overlap

            # Avoid infinite loop on last chunk
            if end >= len(text):
                break

        return chunks


def chunk_by_sentences(text: str, max_chunk_size: int = 500) -> List[str]:
    """
    Split text by sentences with size constraint.

    Args:
        text: Input text
        max_chunk_size: Maximum characters per chunk

    Returns:
        List of sentence-based chunks
    """
    import re

    # Split by sentence
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chunk_size:
            current_chunk += " " + sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def chunk_by_paragraphs(text: str, max_chunk_size: int = 500) -> List[str]:
    """
    Split text by paragraphs with size constraint.

    Args:
        text: Input text
        max_chunk_size: Maximum characters per chunk

    Returns:
        List of paragraph-based chunks
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) < max_chunk_size:
            current_chunk += "\n\n" + para if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
