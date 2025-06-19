"""Tests for chunker."""

from ingestion.chunker import chunk_text


def test_chunk_text_basic():
    """Verify chunk_text splits text."""
    text = "one two three four five six seven"
    chunks = chunk_text(text, max_chars=10)
    assert len(chunks) > 1
    assert "one" in chunks[0]
