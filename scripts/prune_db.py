import asyncio
import aiosqlite
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.db.vector_store import VectorDBRepository

async def prune_database():
    settings = get_settings()
    db_path = settings.db_path
    vector_db = VectorDBRepository()
    
    # 定義要刪除的來源模式
    # Tier 3: 民生超市、超商
    # Tier 4: OSM 巨量街邊店 (主要是 food 類別)
    sources_to_delete_patterns = [
        "MOEA_%",
        "OSM_%",
        "OSM"
    ]
    
    excluded_sources = ["ENRICHED_PREMIUM", "ENRICHED_TAGS", "TDX_API"]
    
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        
        # 1. 找出所有非 Tier 1 & Tier 2 的資料
        # 我們排除掉明確要留下的來源，剩下的如果符合 OSM 或 MOEA 模式就刪除
        query = f"""
            SELECT id, name, source, category FROM pois 
            WHERE source NOT IN ({','.join(['?']*len(excluded_sources))})
        """
        cursor = await db.execute(query, excluded_sources)
        rows = await cursor.fetchall()
        
        ids_to_delete = [str(row['id']) for row in rows]
        print(f"🔍 總共發現 {len(ids_to_delete)} 筆待刪除的 Tier 3/4 候選資料。")
        
        if not ids_to_delete:
            print("✅ 沒有發現需要刪除的資料。")
            return

        # 2. 從 ChromaDB 刪除 (分批處理)
        batch_size = 500
        for i in range(0, len(ids_to_delete), batch_size):
            batch = ids_to_delete[i:i+batch_size]
            try:
                # 使用 to_thread 確保與 VectorDBRepository 的其他 I/O 模式一致
                await asyncio.to_thread(
                    vector_db.poi_collection.delete,
                    ids=batch
                )
                print(f"🗑️ ChromaDB: 已刪除第 {i} 到 {min(i+batch_size, len(ids_to_delete))} 筆...")
            except Exception as e:
                print(f"⚠️ ChromaDB 刪除批次失敗: {e}")

        # 3. 從 SQLite 刪除 (分批處理以避免 SQLite 參數上限錯誤)
        for i in range(0, len(ids_to_delete), batch_size):
            batch = ids_to_delete[i:i+batch_size]
            placeholders = ",".join(["?"] * len(batch))
            await db.execute(f"DELETE FROM pois WHERE id IN ({placeholders})", batch)
            
        await db.commit()
        print(f"✅ SQLite: 成功移除 {len(ids_to_delete)} 筆資料。")

    print("🎉 資料庫瘦身完成！目前僅保留 Tier 1 (Enriched) 與 Tier 2 (TDX Official)。")

if __name__ == "__main__":
    asyncio.run(prune_database())
