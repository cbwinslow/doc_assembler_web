"""Simple helper to store documents in ChromaDB."""

from typing import Sequence

import chromadb


def store_documents(docs: Sequence[str], collection_name: str = "docs") -> None:
    """Store documents in ChromaDB collection."""
    client = chromadb.Client()
    collection = client.get_or_create_collection(collection_name)
    for i, doc in enumerate(docs):
        collection.add(documents=[doc], ids=[str(i)])


if __name__ == "__main__":
    example_docs = ["hello world", "another document"]
    store_documents(example_docs)
    print("Stored example documents in ChromaDB.")
