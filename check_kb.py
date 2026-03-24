import asyncio
import dotenv
import os
from psycopg_pool import AsyncConnectionPool
from agent.tools.knowledge_base import search_knowledge, set_pool

dotenv.load_dotenv()

async def test():
    pool = AsyncConnectionPool(conninfo=os.getenv('DATABASE_URL'), open=False)
    await pool.open()
    set_pool(pool)
    
    print("--- Searching for Islam Massad ---")
    results_islam = await search_knowledge("Islam Massad")
    for r in results_islam:
        print(f"[{r['score']:.2f}] {r['url']}: {r['content'][:100]}...")
        
    print("\n--- Searching for Malek Alsharairi ---")
    results_malek = await search_knowledge("Malek Alsharairi")
    for r in results_malek:
        print(f"[{r['score']:.2f}] {r['url']}: {r['content'][:100]}...")
        
    await pool.close()

if __name__ == "__main__":
    asyncio.run(test())
