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

async def check_mrt_quality():
    settings = get_settings()
    with open("src/data/location_dictionary.json", "r", encoding="utf-8") as f:
        locations = json.load(f)
        
    mrt_stations = []
    for name, coords in locations.items():
        if "站" in name:
            mrt_stations.append({"name": name, "lat": coords["lat"], "lng": coords["lng"]})
    
    print(f"📊 正在巡檢 {len(mrt_stations)} 個捷運站點的 1km 「優質 POI (Tier 1/2)」覆蓋率...")
    
    gaps = []
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        # 僅考慮 Tier 1 和 Tier 2
        cursor = await db.execute("SELECT name, lat, lng, tier FROM pois WHERE tier IN (1, 2)")
        premium_pois = await cursor.fetchall()
        
        for mrt in mrt_stations:
            mrt_lat = mrt["lat"]
            mrt_lng = mrt["lng"]
            nearby_count = 0
            for poi in premium_pois:
                if haversine(mrt_lat, mrt_lng, poi["lat"], poi["lng"]) <= 1.0:
                    nearby_count += 1
            
            if nearby_count < 1: # 每個站至少要有一個 Tier 1/2
                gaps.append(mrt)
                print(f"❌ 品質缺口: {mrt['name']} (無 Tier 1/2)")

    print(f"\n📊 偵測完成。共有 {len(gaps)} 個站點完全沒有高品質 POI。")
    with open("scripts/data/mrt_quality_gaps.json", "w", encoding="utf-8") as f:
        json.dump(gaps, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(check_mrt_quality())
