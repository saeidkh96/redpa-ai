import asyncio

from app.clients.ollama_client import ollama_client
from app.schemas.ollama import OllamaChatMessage


async def main() -> None:
    messages = [
        OllamaChatMessage(
            role="user",
            content=(
                "Explain Retrieval-Augmented Generation "
                "in three short sentences."
            ),
        ),
    ]

    print("Streaming response:\n")

    async for token in ollama_client.stream_chat(messages):
        print(
            token,
            end="",
            flush=True,
        )

    print("\n\nStream completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())