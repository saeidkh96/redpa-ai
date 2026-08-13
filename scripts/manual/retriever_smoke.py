import asyncio
from uuid import UUID

from app.services.retriever_service import RetrieverService


async def main() -> None:
    retriever = RetrieverService(
        default_limit=5,
        default_score_threshold=0.20,
    )

    try:
        results = await retriever.retrieve_from_document(
            query="du muss?",
            user_id=UUID(
                "8bb4763b-94bc-4b6e-8e8f-4c994adab28d"
            ),
            document_id=UUID(
                "97f9b751-e589-4cd6-ad53-3021976ac096"
            ),
            limit=5,
            score_threshold=0.20,
        )

        if not results:
            print("No relevant chunks found.")
            return

        print(f"\nFound {len(results)} relevant chunks:\n")

        for index, result in enumerate(results, start=1):
            print("=" * 70)
            print(f"Result: {index}")
            print(f"Score: {result.score:.4f}")
            print(f"Document ID: {result.document_id}")
            print(f"Chunk Index: {result.chunk_index}")
            print(f"Chunk ID: {result.chunk_id}")
            print("-" * 70)
            print(result.text)
            print()

    finally:
        await retriever.close()


if __name__ == "__main__":
    asyncio.run(main())