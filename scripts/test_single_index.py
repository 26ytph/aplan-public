import asyncio
import aiosqlite
from src.db.vector_store import VectorDBRepository
from src.utils.llm_adapter import get_llm_adapter

async def test():
    vdb = VectorDBRepository()
    adapter = get_llm_adapter("gemini")
    async with aiosqlite.connect("test.db") as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM pois WHERE tier = 1 LIMIT 1")
        row = await cursor.fetchone()
        print(f"Testing POI: {row['name']}")
        text = f"景點名稱: {row['name']}\n類別: {row['category']}\n描述: {row['description']}\n地址: {row['address']}"
        emb = await adapter.get_embedding(text)
        print(f"Embedding generated (len={len(emb)})")
        await vdb.upsert_pois([str(row['id'])], [emb], [text], [{"poi_id": row['id'], "name": row['name'], "tier": 1}])
        print("Upsert completed")
        count = await vdb.count_pois()
        print(f"Chroma count now: {count}")

if __name__ == "__main__":
    asyncio.run(test())
