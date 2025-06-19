"""Text chunking utilities."""

from typing import List


def chunk_text(text: str, max_chars: int = 1000) -> List[str]:
    """Split text into chunks of approximately max_chars characters."""
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for word in words:
        if length + len(word) + 1 > max_chars:
            chunks.append(" ".join(current))
            current = [word]
            length = len(word) + 1
        else:
            current.append(word)
            length += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks
