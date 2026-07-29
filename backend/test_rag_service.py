import asyncio
from uuid import UUID

from app.services.rag_service import (
    RAGService,
)


USER_ID = UUID(
    "8bb4763b-94bc-4b6e-8e8f-4c994adab28d"
)

DOCUMENT_ID = UUID(
    "97f9b751-e589-4cd6-ad53-3021976ac096"
)


async def main() -> None:
    rag_service = RAGService(
        default_limit=5,
        default_score_threshold=0.20,
        default_max_context_characters=12_000,
    )

    try:
        result = await rag_service.answer(
            question=(
                "What does the uploaded document say?"
            ),
            user_id=USER_ID,
            document_id=DOCUMENT_ID,
            limit=5,
            score_threshold=0.20,
        )

        print("\nRAG Answer")
        print("=" * 70)
        print(result.answer)

        print("\nRAG Information")
        print("=" * 70)
        print(f"Model: {result.model}")
        print(f"Provider: {result.provider}")
        print(
            f"Context used: "
            f"{result.context_used}"
        )
        print(
            f"Retrieved chunks: "
            f"{result.retrieval_count}"
        )
        print(
            f"Context characters: "
            f"{result.context_characters}"
        )
        print(
            f"Context truncated: "
            f"{result.context_truncated}"
        )

        print("\nSources")
        print("=" * 70)

        if not result.sources:
            print("No sources were used.")

        for source in result.sources:
            print(
                f"Source {source.source_number}"
            )
            print(
                f"Document ID: "
                f"{source.document_id}"
            )
            print(
                f"Chunk ID: "
                f"{source.chunk_id}"
            )
            print(
                f"Chunk Index: "
                f"{source.chunk_index}"
            )
            print(
                f"Score: "
                f"{source.score:.4f}"
            )
            print(
                f"Text: "
                f"{source.text}"
            )
            print("-" * 70)

        print("\nUsage")
        print("=" * 70)

        for key, value in result.usage.items():
            print(f"{key}: {value}")

    finally:
        await rag_service.close()


if __name__ == "__main__":
    asyncio.run(main())