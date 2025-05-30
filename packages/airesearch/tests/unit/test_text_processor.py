"""Tests for text processing utilities."""
import pytest
from airesearch.utils.text_processor import (
    preprocess_text,
    extract_keywords,
    calculate_text_similarity,
    extract_entities,
    create_text_summary
)

def test_text_preprocessing(sample_text: str):
    """Test text preprocessing functionality."""
    processed_text = preprocess_text(sample_text)
    
    assert processed_text.islower()
    assert "." not in processed_text
    assert "," not in processed_text
    assert "  " not in processed_text

def test_keyword_extraction(sample_text: str):
    """Test keyword extraction functionality."""
    keywords = extract_keywords(sample_text, top_n=5)
    
    assert isinstance(keywords, list)
    assert len(keywords) <= 5
    assert all(isinstance(k, str) for k in keywords)
    assert "machine" in keywords or "learning" in keywords

def test_keyword_extraction_limits():
    """Test keyword extraction with different limits."""
    text = "word1 word2 word3 word4 word5"
    
    # Test with different top_n values
    assert len(extract_keywords(text, top_n=3)) == 3
    assert len(extract_keywords(text, top_n=10)) == 5  # Only 5 words available

def test_text_similarity():
    """Test text similarity calculation."""
    text1 = "The quick brown fox"
    text2 = "The quick brown fox jumps"
    text3 = "The lazy dog sleeps"
    
    # Test identical texts
    assert calculate_text_similarity(text1, text1) == 1.0
    
    # Test similar texts
    similarity1 = calculate_text_similarity(text1, text2)
    assert 0 < similarity1 < 1
    
    # Test different texts
    similarity2 = calculate_text_similarity(text1, text3)
    assert similarity2 < similarity1

def test_entity_extraction(sample_text: str):
    """Test entity extraction functionality."""
    entities = extract_entities(sample_text)
    
    assert isinstance(entities, dict)
    assert "dates" in entities
    assert "numbers" in entities
    assert "urls" in entities
    
    assert "2024-03-15" in entities["dates"]
    assert "25" in entities["numbers"]
    assert "https://pytorch.org" in entities["urls"]

def test_text_summarization():
    """Test text summarization functionality."""
    long_text = "First sentence. Second sentence. Third sentence. Fourth sentence."
    
    # Test with different length limits
    summary1 = create_text_summary(long_text, max_length=20)
    summary2 = create_text_summary(long_text, max_length=100)
    
    assert len(summary1) <= 20
    assert len(summary2) <= 100
    assert len(summary1) < len(summary2)

def test_empty_input_handling():
    """Test handling of empty or invalid inputs."""
    assert preprocess_text("") == ""
    assert extract_keywords("") == []
    assert calculate_text_similarity("", "") == 0.0
    assert extract_entities("") == {"dates": [], "numbers": [], "urls": []}
    assert create_text_summary("") == ""

