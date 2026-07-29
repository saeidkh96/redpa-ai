import asyncio

from app.services.embedding_service import (
    EmbeddingService,
)


async def main() -> None:
    service = EmbeddingService()

    health = await service.health_check()
    print("Health check:")
    print(health)

    embedding = await service.embed_text(
        "RedPA AI document retrieval test"
    )

    print()
    print("Embedding generated successfully.")
    print(f"Vector dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")


if __name__ == "__main__":
    asyncio.run(main())