import asyncio
from app.clients.n8n_client import N8NClient

async def main():
    result = await N8NClient().execute(
        "redpa-automation-test",
        {"message": "Hello from FastAPI"},
    )
    print(result)

asyncio.run(main())
