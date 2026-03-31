import asyncio
import json
import aiosqlite
import math
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.config import get_settings

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def fill_gaps():
    settings = get_settings()
    with open("scripts/data/mrt_quality_gaps.json", "r", encoding="utf-8") as f:
        gaps = json.load(f)
        
    print(f"🛠️ 正在為 {len(gaps)} 個捷運站補強優質 POI...")
    
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        
        # 取得所有 Tier 3 且 category 包含 food/cafe 的候選人
        cursor = await db.execute("SELECT id, name, lat, lng, tier FROM pois WHERE tier = 3")
        candidates = await cursor.fetchall()
        
        upgraded_ids = []
        for mrt in gaps:
            mrt_lat = mrt["lat"]
            mrt_lng = mrt["lng"]
            
            # 依距離排序並取前 3 名
            nearby = []
            for c in candidates:
                dist = haversine(mrt_lat, mrt_lng, c["lat"], c["lng"])
                if dist <= 1.0:
                    nearby.append((dist, c["id"]))
            
            nearby.sort()
            for dist, poi_id in nearby[:3]:
                upgraded_ids.append(poi_id)
        
        unique_upgrades = list(set(upgraded_ids))
        print(f"✨ 決定將 {len(unique_upgrades)} 筆在地推薦升格為 Tier 2 (Featured)。")
        
        if unique_upgrades:
            placeholders = ",".join(["?"] * len(unique_upgrades))
            await db.execute(f"UPDATE pois SET tier = 2, is_embedded = 0 WHERE id IN ({placeholders})", unique_upgrades)
            await db.commit()
            
    print("🎉 補洞完成！請記得重跑 reindex_all.py 以同步向量庫。")

if __name__ == "__main__":
    asyncio.run(fill_gaps())
