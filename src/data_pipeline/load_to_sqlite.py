"""
Stage 2: LOAD → SQLite
從 JSON 快取讀取 POI 資料，寫入 SQLite。
新增 is_embedded 欄位以追蹤 Stage 3 的增量嵌入進度。
純本地操作，不消耗任何 API 配額。
"""
import asyncio, json, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.repository import DatabaseRepository
from src.core.config import get_settings

async def main():
    print("🚀 Stage 2: LOAD → SQLite")
    
    cache_path = "data_cache/pois.json"
    if not os.path.exists(cache_path):
        print(f"❌ 找不到快取檔案 {cache_path}，請先執行 Stage 1 (fetch_to_cache.py)")
        return
    
    with open(cache_path, "r", encoding="utf-8") as f:
        all_pois = json.load(f)
    print(f"📂 已讀取 {len(all_pois)} 筆 POI 快取")
    
    # 讀取各行政區補強資料 (Districts)
    dist_dir = "data_cache/districts"
    if os.path.exists(dist_dir):
        for filename in os.listdir(dist_dir):
            if filename.endswith(".json"):
                fpath = os.path.join(dist_dir, filename)
                with open(fpath, "r", encoding="utf-8") as f:
                    dist_pois = json.load(f)
                all_pois.extend(dist_pois)
                print(f"📂 已讀取 {filename} ({len(dist_pois)} 筆)，總數提升至 {len(all_pois)} 筆")
    
    # [備援] 讀取個別歷史 OSM 快取
    for old_file in ["data_cache/osm_beitou.json", "data_cache/osm_songshan.json"]:
        if os.path.exists(old_file):
            with open(old_file, "r", encoding="utf-8") as f:
                old_pois = json.load(f)
            all_pois.extend(old_pois)
            print(f"📂 已讀取 {old_file} ({len(old_pois)} 筆)，總數提升至 {len(all_pois)} 筆")
            
    mrt_path = "data_cache/mrt_stations.json"
    if os.path.exists(mrt_path):
        with open(mrt_path, "r", encoding="utf-8") as f:
            mrt_pois = json.load(f)
        all_pois.extend(mrt_pois)
        print(f"📂 已讀取 {mrt_path} ({len(mrt_pois)} 筆)，總數提升至 {len(all_pois)} 筆")
    
    # 初始化 SQLite
    settings = get_settings()
    db_path = settings.db_path
    
    repo = DatabaseRepository()
    await repo.init_db()
    
    # 確保 pois 表有 is_embedded 欄位
    import aiosqlite
    async with aiosqlite.connect(db_path) as db:
        # 檢查是否已有 is_embedded 欄位
        cursor = await db.execute("PRAGMA table_info(pois)")
        columns = [row[1] for row in await cursor.fetchall()]
        if "is_embedded" not in columns:
            await db.execute("ALTER TABLE pois ADD COLUMN is_embedded INTEGER DEFAULT 0")
            await db.commit()
            print("  └ ✅ 已新增 is_embedded 欄位")
            
        # 讀取現存的 POI，避免重複寫入打亂 ChromaDB ID
        cursor = await db.execute("SELECT name FROM pois")
        existing_names = set(row[0] for row in await cursor.fetchall())
        print(f"📂 資料庫中已有 {len(existing_names)} 筆 POI，將進行差異比對...")
    
    # 過濾出全新的 POI
    new_pois = [p for p in all_pois if p["name"] not in existing_names]
    print(f"🌟 本次將新增 {len(new_pois)} 筆全新資料到 SQLite...")
    
    # 寫入 SQLite
    count = 0
    for poi in new_pois:
        await repo.insert_poi(
            name=poi["name"],
            category=poi["category"],
            description=poi["description"],
            lat=poi.get("lat", 25.0330),
            lng=poi.get("lng", 121.5654),
            address=poi["address"],
            image_url=poi.get("image_url", ""),
            source=poi["source"]
        )
        count += 1
    
    print(f"\n✅ Stage 2 完成！共 {count} 筆全新 POI 已寫入 SQLite ({db_path})")
    
    # 分類統計驗證
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT category, COUNT(*) FROM pois GROUP BY category ORDER BY COUNT(*) DESC")
        rows = await cursor.fetchall()
        for cat, cnt in rows:
            print(f"  └ {cat}: {cnt} 筆")
        
        cursor = await db.execute("SELECT COUNT(*) FROM pois WHERE is_embedded = 0")
        row = await cursor.fetchone()
        print(f"\n📊 待嵌入: {row[0]} 筆")

if __name__ == "__main__":
    asyncio.run(main())
