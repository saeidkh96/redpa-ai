import asyncio

from redpa_sdk import AsyncRedPA


async def main() -> None:
    async with AsyncRedPA() as client:
        print(await client.health())
        print(await client.workflows(limit=10))


if __name__ == "__main__":
    asyncio.run(main())
