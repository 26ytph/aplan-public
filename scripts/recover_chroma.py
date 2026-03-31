import asyncio
import aiosqlite
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.db.vector_store import VectorDBRepository
from src.utils.llm_adapter import get_llm_adapter

async def quick_reindex():
    vdb = VectorDBRepository()
    adapter = get_llm_adapter('gemini')
    async with aiosqlite.connect('test.db') as db:
        db.row_factory = aiosqlite.Row
        # 先重建 Tier 1 與 Tier 2 的核心菁英名單 (保證品質覆蓋)
        cursor = await db.execute('SELECT * FROM pois WHERE tier IN (1, 2) LIMIT 200')
        rows = await cursor.fetchall()
        print(f"🚀 [Recovery] Syncing {len(rows)} elite POIs into fresh ChromaDB...")
        
        for row in rows:
            text = f"景點名稱: {row['name']}\n類別: {row['category']}\n描述: {row['description']}\n地址: {row['address']}"
            try:
                emb = await adapter.get_embedding(text)
                await vdb.upsert_pois(
                    ids=[str(row['id'])], 
                    embeddings=[emb], 
                    documents=[text], 
                    metadatas=[{'poi_id': row['id'], 'name': row['name'], 'tier': row['tier']}]
                )
                await db.execute('UPDATE pois SET is_embedded = 1 WHERE id = ?', (row['id'],))
            except Exception as e:
                print(f"❌ Error syncing {row['name']}: {e}")
                
        await db.commit()
    print("✅ Elite sync completed successfully.")

if __name__ == "__main__":
    asyncio.run(quick_reindex())
