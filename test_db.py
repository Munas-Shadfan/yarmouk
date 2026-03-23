import os
import asyncio
from psycopg_pool import AsyncConnectionPool
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def test_db():
    print(f"Connecting to {DATABASE_URL}")
    try:
        async with AsyncConnectionPool(DATABASE_URL) as pool:
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    res = await cur.fetchone()
                    print(f"Success: {res}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
