"""Basic tests for AI research functionality."""

import pytest
import torch
import numpy as np


def test_pytorch_import():
    """Test that PyTorch is available and working."""
    assert torch.cuda.is_available() == False  # We're using CPU-only version
    tensor = torch.rand(3, 3)
    assert tensor.shape == (3, 3)


def test_numpy_operations():
    """Test basic NumPy operations."""
    arr = np.array([[1, 2], [3, 4]])
    assert arr.shape == (2, 2)
    assert np.sum(arr) == 10


@pytest.mark.asyncio
async def test_async_operation():
    """Test that async operations are working."""
    async def dummy_async_func():
        return "success"
    
    result = await dummy_async_func()
    assert result == "success"

