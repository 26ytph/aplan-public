import asyncio
import aiosqlite
import sys
import os

# 確保路徑正確
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.db.vector_store import VectorDBRepository

async def verify_phase32():
    print("🔍 驗證 Phase 32 (Gourmet Global Expansion & MRT Coverage) 執行成果...\n")
    
    settings = get_settings()
    
    print("1️⃣ [SQLite 關聯資料庫] 結構與資料分佈驗證")
    async with aiosqlite.connect(settings.db_path) as db:
        # 1. 檢查表格結構
        cursor = await db.execute("PRAGMA table_info(pois)")
        columns = [row[1] for row in await cursor.fetchall()]
        has_tier = "tier" in columns
        print(f" - ✅ 'tier' 欄位是否存在於 pois 表格中: {has_tier}")
        
        # 2. 檢查 Tier 分佈 (驗證 130+ 國際級美食與 79 筆 MRT 升級)
        cursor = await db.execute("SELECT tier, count(*) FROM pois GROUP BY tier ORDER BY tier")
        rows = await cursor.fetchall()
        print(" - 📊 全庫 Tier 等級數量統計:")
        for t, c in rows:
            t_name = f"Tier {t}" if t is not None else "Tier N/A"
            print(f"   > {t_name}: {c} 筆")
            
        # 3. 抽查幾筆大家熟知的出國/頂級必訪餐廳 (驗證 Inflow)
        print("\n - 🌟 指標級名店實質抽查 (Tier 1/2):")
        cursor = await db.execute("SELECT name, tier FROM pois WHERE name LIKE '%頤宮%' OR name LIKE '%RAW%' OR name LIKE '%鼎泰豐%' LIMIT 3")
        famous_rows = await cursor.fetchall()
        for name, tier in famous_rows:
            print(f"   > {name} (目前為 Tier {tier})")
            
    print("\n2️⃣ [ChromaDB 向量資料庫] 語意與 Metadata 同步驗證")
    try:
        vdb = VectorDBRepository()
        # 嘗試利用 ChromaDB 的原生語法，透過 Tier 的 metadata 來過濾過濾出三筆
        results = vdb.poi_collection.get(limit=3, where={"tier": {"$in": [1, 2]}})
        
        if results and results.get("metadatas") and len(results["metadatas"]) > 0:
            print(f" - ✅ 成功證明 ChromaDB 的向量標籤內已包含 'tier' 屬性！")
            for meta in results["metadatas"]:
                print(f"   🎟️ 檢索出的向量景點: {meta.get('name')} | 元數據標籤 Tier: {meta.get('tier')}")
        else:
            print(" - ⚠️ 警告：ChromaDB 中找不到帶有 Tier 1/2 metadata 的向量。可能未同步！")
    except Exception as e:
        print(f" - ❌ ChromaDB 驗證出現技術錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(verify_phase32())
