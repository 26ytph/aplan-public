import asyncio
import json
import aiosqlite
from src.db.vector_store import VectorDBRepository
from src.core.config import get_settings

async def sync():
    settings = get_settings()
    vdb = VectorDBRepository()
    
    # 1. 取得 Chroma 中所有的 ID
    chroma_all = vdb.poi_collection.get()
    chroma_ids = chroma_all['ids']
    print(f"🔍 Chroma 中目前有 {len(chroma_ids)} 筆資料。")
    
    # 2. 取得 SQLite 中所有的 ID
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute("SELECT id FROM pois")
        rows = await cursor.fetchall()
        sqlite_ids = set(str(row[0]) for row in rows)
        print(f"🔍 SQLite 中目前有 {len(sqlite_ids)} 筆資料。")
        
    # 3. 找出死掉的 ID (在 Chroma 但不在 SQLite)
    dead_ids = [cid for cid in chroma_ids if cid not in sqlite_ids]
    print(f"🗑️ 發現 {len(dead_ids)} 筆過時資料需要從 Chroma 刪除。")
    
    if dead_ids:
        # 分批刪除避免 API 限制
        batch_size = 1000
        for i in range(0, len(dead_ids), batch_size):
            batch = dead_ids[i:i+batch_size]
            vdb.poi_collection.delete(ids=batch)
            print(f"✅ 已刪除批次 {i//batch_size + 1}")
            
    print("🎉 同步完成！")

if __name__ == "__main__":
    asyncio.run(sync())
