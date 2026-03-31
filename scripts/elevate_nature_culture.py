import asyncio
import aiosqlite
import sys
import os

# 確保路徑正確
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.db.vector_store import VectorDBRepository

# 定義要提拔的關鍵字與對應等級
ELEVAION_TIERS = {
    1: [
        "國立故宮博物院", "中正紀念堂", "國父紀念館", "景福門"
    ],
    2: [
        # 自然景觀
        "陽明山", "象山步道", "象山親山步道", "大安森林公園", "碧潭", "關渡自然", 
        "北投溫泉公園", "士林官邸", "大湖公園", "碧山巖", "劍潭山",
        # 藝文歷史里程碑
        "龍山寺", "西門紅樓", "華山1914", "松山文創", "台北孔廟", "大龍峒保安宮", 
        "台北當代藝術館", "中山堂", "剝皮寮", "國立台灣大學"
    ]
}

async def elevate():
    settings = get_settings()
    vdb = VectorDBRepository()
    
    print("🚀 [Phase 32.2 Elevation] 啟動國家級景點權重提拔程序...")
    
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        
        elevated_ids = []
        
        for tier, keywords in ELEVAION_TIERS.items():
            for kw in keywords:
                # 執行 SQLite 更新
                cursor = await db.execute(
                    "UPDATE pois SET tier = ? WHERE (name LIKE ?) AND tier > ?", 
                    (tier, f"%{kw}%", tier)
                )
                affected = cursor.rowcount
                
                # 取得被更新的 ID 用於 ChromaDB 同步
                cursor = await db.execute("SELECT id, name FROM pois WHERE (name LIKE ?) AND tier = ?", (f"%{kw}%", tier))
                rows = await cursor.fetchall()
                for row in rows:
                    elevated_ids.append(row['id'])
                    print(f"  ✨ 提拔成功: {row['name']} -> Tier {tier}")

        await db.commit()
        print(f"\n✅ SQLite 更新完成，共計提拔 {len(elevated_ids)} 個指標景點。")

        # 同步更新 ChromaDB 的 Metadata
        if elevated_ids:
            print(f"🔄 正在同步 ChromaDB 的 Tier Metadata...")
            # 批次取回最新資料
            placeholders = ','.join(['?'] * len(elevated_ids))
            cursor = await db.execute(f"SELECT id, name, tier FROM pois WHERE id IN ({placeholders})", elevated_ids)
            latest_rows = await cursor.fetchall()
            
            for row in latest_rows:
                # 雖然 Chroma 不直接支援部分 metadata 更新，但我們可以透過 get + update (或者 upsert)
                # 由於我們已經有完整資料，使用 update 更新 metadata
                vdb.poi_collection.update(
                    ids=[str(row['id'])],
                    metadatas=[{"poi_id": row['id'], "name": row['name'], "tier": row['tier']}]
                )
            print(f"✅ ChromaDB 同步完成。")

if __name__ == "__main__":
    asyncio.run(elevate())
