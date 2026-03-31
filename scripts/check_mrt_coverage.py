import asyncio
import json
import aiosqlite
import math
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.config import get_settings

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # 地球半徑 (km)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def check_mrt_coverage():
    settings = get_settings()
    
    with open("src/data/location_dictionary.json", "r", encoding="utf-8") as f:
        locations = json.load(f)
        
    mrt_stations = []
    for name, coords in locations.items():
        if "站" in name:
            mrt_stations.append({
                "name": name,
                "lat": coords["lat"],
                "lng": coords["lng"]
            })
    print(f"🚉 正在巡檢 {len(mrt_stations)} 個捷運站點的 1km 覆蓋率...")
    
    gaps = []
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        
        # 預載入所有 POI 到記憶體（目前僅 2200 筆，OK）
        cursor = await db.execute("SELECT name, lat, lng, tier FROM pois")
        all_pois = await cursor.fetchall()
        
        for mrt in mrt_stations:
            mrt_lat = mrt["lat"]
            mrt_lng = mrt["lng"]
            
            # 找出 1km 內的 POI 數量
            nearby_count = 0
            for poi in all_pois:
                if haversine(mrt_lat, mrt_lng, poi["lat"], poi["lng"]) <= 1.0:
                    nearby_count += 1
            
            if nearby_count < 3:
                gaps.append({
                    "name": mrt["name"],
                    "lat": mrt_lat,
                    "lng": mrt_lng,
                    "count": nearby_count
                })
                print(f"⚠️ 缺口偵測: {mrt['name']} (僅 {nearby_count} 筆)")

    print(f"\n📊 巡檢結束。總計 {len(gaps)} 個站點需要補強。")
    with open("scripts/data/mrt_coverage_gaps.json", "w", encoding="utf-8") as f:
        json.dump(gaps, f, ensure_ascii=False, indent=2)
    print("📁 缺口清單已儲存至 scripts/data/mrt_coverage_gaps.json")

if __name__ == "__main__":
    asyncio.run(check_mrt_coverage())
