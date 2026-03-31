import asyncio
import aiosqlite
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.db.vector_store import VectorDBRepository

async def check():
    settings = get_settings()
    db_path = settings.db_path
    
    print("=== 資料庫狀態報告 ===")
    print("\n1. SQLite 關聯資料庫狀態")
    async with aiosqlite.connect(db_path) as db:
        # 總筆數
        cursor = await db.execute("SELECT count(*) FROM pois")
        total = (await cursor.fetchone())[0]
        print(f"總計景點數 (Total POIs): {total}")
        
        # 向量化進度
        cursor = await db.execute("SELECT is_embedded, count(*) FROM pois GROUP BY is_embedded")
        embedded_stats = await cursor.fetchall()
        for is_embedded, count in embedded_stats:
            status = "已建立向量 (Indexed)" if is_embedded else "等待建立 (Pending)"
            print(f"  - {status}: {count}")
            
        # Tier 分布
        cursor = await db.execute("SELECT tier, count(*) FROM pois GROUP BY tier ORDER BY tier")
        tier_stats = await cursor.fetchall()
        print("\nTier 等級分布:")
        for tier, count in tier_stats:
            tier_name = f"Tier {tier}" if tier is not None else "Tier N/A (一般)"
            print(f"  - {tier_name}: {count}")
            
        # 資料來源
        cursor = await db.execute("SELECT source, count(*) FROM pois GROUP BY source")
        source_stats = await cursor.fetchall()
        print("\n資料來源:")
        for source, count in source_stats:
            print(f"  - {source}: {count}")

    print("\n2. ChromaDB 向量資料庫狀態")
    try:
        vdb = VectorDBRepository()
        chroma_count = await vdb.count_pois()
        print(f"成功注入向量數 (Embedded Vectors): {chroma_count}")
        
        if chroma_count < total:
            print(f"⚠️ 警告: 尚有 {total - chroma_count} 筆景點等待轉換入 ChromaDB。")
    except Exception as e:
        print(f"❌ ChromaDB 連線失敗或損毀: {e}")

if __name__ == "__main__":
    asyncio.run(check())
