"""Streaming utilities for ingestion."""

import asyncio
from typing import AsyncGenerator, Iterable


async def stream_chunks(
    chunks: Iterable[str], delay: float = 0.0
) -> AsyncGenerator[str, None]:
    """Asynchronously yield chunks."""
    for chunk in chunks:
        yield chunk
        if delay:
            await asyncio.sleep(delay)
