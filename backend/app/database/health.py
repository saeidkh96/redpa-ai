from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def check_database_connection(engine: AsyncEngine) -> bool:
    """
    Check whether PostgreSQL is reachable and can execute a query.
    """

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            return result.scalar_one() == 1
    except Exception:
        return False