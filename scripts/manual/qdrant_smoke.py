import asyncio
import uuid

from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import (
    VectorStoreService,
)


async def main():

    embedding_service = EmbeddingService()

    vector_store = VectorStoreService()

    await vector_store.initialize()

    embedding = await embedding_service.embed_text(
        "RedPA AI is an agentic AI platform."
    )

    await vector_store.add_chunk(
        chunk_id=str(uuid.uuid4()),
        document_id="demo",
        chunk_index=0,
        text="RedPA AI is an agentic AI platform.",
        embedding=embedding,
    )

    print("Stored!")

    query = await embedding_service.embed_text(
        "What is RedPA?"
    )

    results = await vector_store.search(query)

    print(results)


asyncio.run(main())