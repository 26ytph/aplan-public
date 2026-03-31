import asyncio
import json
import aiosqlite
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.db.vector_store import VectorDBRepository
from src.utils.llm_adapter import get_llm_adapter

async def reindex():
    settings = get_settings()
    db_path = settings.db_path
    vdb = VectorDBRepository()
    adapter = get_llm_adapter("gemini")
    
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        # 優先索引高品質的 Tier 1/2 資料
        cursor = await db.execute("SELECT * FROM pois WHERE is_embedded = 0 ORDER BY tier ASC, id ASC")
        rows = await cursor.fetchall()
        print(f"🔄 準備為 {len(rows)} 筆資料建立/更新索引 (優先處理高品質 Tier 1/2)...")
        
        batch_size = 20
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for row in batch:
                text = f"景點名稱: {row['name']}\n類別: {row['category']}\n描述: {row['description']}\n地址: {row['address']}"
                try:
                    emb = await adapter.get_embedding(text)
                    ids.append(str(row["id"]))
                    embeddings.append(emb)
                    documents.append(text)
                    metadatas.append({
                        "poi_id": row["id"],
                        "name": row["name"],
                        "category": row["category"],
                        "tier": row["tier"]
                    })
                except Exception as e:
                    print(f"❌ 索引失敗: {row['name']} - {e}")
                    
            if ids:
                await vdb.upsert_pois(ids, embeddings, documents, metadatas)
                # 更新 SQLite 狀態
                placeholders = ",".join(["?"] * len(ids))
                await db.execute(f"UPDATE pois SET is_embedded = 1 WHERE id IN ({placeholders})", ids)
                await db.commit()
                print(f"✅ 已完成批次 {i//batch_size + 1}/{len(rows)//batch_size + 1}")

if __name__ == "__main__":
    asyncio.run(reindex())
