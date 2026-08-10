import asyncio
from uuid import UUID

from app.services.context_builder_service import (
    ContextBuilderService,
)
from app.services.retriever_service import (
    RetrieverService,
)


USER_ID = UUID(
    "8bb4763b-94bc-4b6e-8e8f-4c994adab28d"
)

DOCUMENT_ID = UUID(
    "97f9b751-e589-4cd6-ad53-3021976ac096"
)


async def main() -> None:
    retriever = RetrieverService(
        default_limit=5,
        default_score_threshold=0.20,
    )

    context_builder = ContextBuilderService(
        max_characters=12_000,
        include_source_headers=True,
    )

    try:
        chunks = await retriever.retrieve_from_document(
            query="What does the document say?",
            user_id=USER_ID,
            document_id=DOCUMENT_ID,
            limit=5,
            score_threshold=0.20,
        )

        built_context = context_builder.build(chunks)

        print("\nBuilt Context")
        print("=" * 70)
        print(built_context.context)

        print("\nContext Information")
        print("=" * 70)
        print(
            f"Sources: {len(built_context.sources)}"
        )
        print(
            f"Characters: "
            f"{built_context.total_characters}"
        )
        print(
            f"Truncated: {built_context.truncated}"
        )

        print("\nSources")
        print("=" * 70)

        for source in built_context.sources:
            print(
                f"Source {source.source_number}: "
                f"document={source.document_id}, "
                f"chunk={source.chunk_index}, "
                f"score={source.score:.4f}"
            )

    finally:
        await retriever.close()


if __name__ == "__main__":
    asyncio.run(main())