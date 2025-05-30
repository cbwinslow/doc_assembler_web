"""
Text processing utilities for research tasks.

This module provides utilities for text preprocessing, keyword extraction,
and other NLP-related tasks used in the research process.
"""
from typing import List, Dict, Set, Optional
import re
import string
from collections import Counter

def preprocess_text(text: str) -> str:
    """
    Preprocess text for analysis.

    Args:
        text: Raw text to process

    Returns:
        Preprocessed text string
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """
    Extract keywords from text.

    Args:
        text: Preprocessed text
        top_n: Number of top keywords to return

    Returns:
        List of extracted keywords
    """
    # Split into words
    words = text.split()
    
    # Remove common stop words (simplified version)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to'}
    words = [w for w in words if w not in stop_words]
    
    # Count word frequencies
    word_freq = Counter(words)
    
    # Get top N keywords
    return [word for word, _ in word_freq.most_common(top_n)]

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using simple Jaccard similarity.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity score between 0 and 1
    """
    # Preprocess texts
    set1 = set(preprocess_text(text1).split())
    set2 = set(preprocess_text(text2).split())
    
    # Calculate Jaccard similarity
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities from text (simplified version).

    Args:
        text: Input text

    Returns:
        Dictionary of entity types and their values
    """
    entities: Dict[str, List[str]] = {
        'dates': [],
        'numbers': [],
        'urls': []
    }
    
    # Extract dates (simple pattern)
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    entities['dates'] = re.findall(date_pattern, text)
    
    # Extract numbers
    number_pattern = r'\b\d+\.?\d*\b'
    entities['numbers'] = re.findall(number_pattern, text)
    
    # Extract URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    entities['urls'] = re.findall(url_pattern, text)
    
    return entities

def create_text_summary(text: str, max_length: int = 200) -> str:
    """
    Create a simple summary of the text.

    Args:
        text: Input text
        max_length: Maximum length of the summary

    Returns:
        Summarized text
    """
    # Split into sentences (simple approach)
    sentences = text.split('.')
    
    # Select first few sentences that fit within max_length
    summary = ''
    for sentence in sentences:
        if len(summary) + len(sentence) <= max_length:
            summary += sentence.strip() + '. '
        else:
            break
    
    return summary.strip()

