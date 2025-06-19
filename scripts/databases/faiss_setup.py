"""Create FAISS index and store example documents."""

import faiss
import numpy as np


def create_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    """Create an in-memory FAISS index."""
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index


if __name__ == "__main__":
    sample_embeddings = np.random.rand(10, 128).astype("float32")
    index = create_index(sample_embeddings)
    print(f"FAISS index contains {index.ntotal} vectors")
