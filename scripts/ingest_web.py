"""Simple web ingestion script using the ingestion package."""

import asyncio

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from ingestion import chunk_text, stream_chunks


async def fetch_text(url: str) -> str:
    """Fetch plain text from the given URL."""
    async with ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            return soup.get_text(separator=" ")


async def main(url: str) -> None:
    """Ingest the page and print chunk previews."""
    text = await fetch_text(url)
    chunks = chunk_text(text)
    async for chunk in stream_chunks(chunks):
        print(chunk[:80])


if __name__ == "__main__":
    import sys

    asyncio.run(main(sys.argv[1]))
