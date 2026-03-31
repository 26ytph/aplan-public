import json
import os
import sys
import aiosqlite
import asyncio

# ⚠️ [Phase 23 備註] 本腳本的 DUMMY_VECTOR 機制已被取代。
# 自 Phase 22 起，所有 15,230 筆 POI 已透過 embed_incremental.py 完成真實 AI 嵌入。
# 未來若需新增 POI 資料，請直接使用 embed_incremental.py 作為向量化入口，
# 不要再使用本腳本的 DUMMY_VECTOR 流程。

# 加入專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.repository import DatabaseRepository
from src.db.vector_store import VectorDBRepository
from src.core.config import get_settings

# 設定
DISTRICTS_DIR = "data_cache/districts"
SIFTED_LIMIT_PER_DISTRICT = 150  # 每個行政區只取前 150 筆作為「精華」進行 AI 嵌入
DUMMY_VECTOR = [0.001] * 3072

async def process_and_load():
    print("🚀 啟動：高品質資料篩選與自動載入計畫 (Phase 19)")
    
    if not os.path.exists(DISTRICTS_DIR):
        print(f"❌ 找不到資料夾: {DISTRICTS_DIR}")
        return

    # 初始化 DB
    repo = DatabaseRepository()
    await repo.init_db()
    chroma_repo = VectorDBRepository()
    
    settings = get_settings()
    db_path = settings.db_path

    total_essence = 0
    total_dummy = 0

    # 遍歷所有行政區 JSON
    files = [f for f in os.listdir(DISTRICTS_DIR) if f.endswith(".json")]
    
    for filename in files:
        fpath = os.path.join(DISTRICTS_DIR, filename)
        with open(fpath, "r", encoding="utf-8") as f:
            pois = json.load(f)
        
        # 簡單的品質評分：敘述越長、來源標籤越豐富者優先
        # (這裡可以根據 OSM 原始資料擴充更多權重)
        pois.sort(key=lambda x: len(x.get("description", "")), reverse=True)
        
        essence = pois[:SIFTED_LIMIT_PER_DISTRICT]
        dummies = pois[SIFTED_LIMIT_PER_DISTRICT:]
        
        print(f"📂 處理 {filename}: 精華 {len(essence)} 筆, 備援 {len(dummies)} 筆")
        
        # 1. 寫入精華資料 (is_embedded = 0，待後續 embed_incremental.py 處理)
        for p in essence:
            try:
                await repo.insert_poi(
                    name=p["name"],
                    category=p["category"],
                    description=p["description"],
                    lat=p["lat"],
                    lng=p["lng"],
                    address=p["address"],
                    image_url=p.get("image_url", ""),
                    source=p["source"]
                )
                total_essence += 1
            except Exception: # 忽略重複名稱
                pass

        # 2. 寫入備援資料 (直接標記為 is_embedded = 1, 並塞入 Dummy Vector)
        async with aiosqlite.connect(db_path) as db:
            for p in dummies:
                try:
                    # 先插入 SQLite
                    cursor = await db.execute(
                        "INSERT INTO pois (name, category, description, lat, lng, address, image_url, source, is_embedded) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
                        (p["name"], p["category"], p["description"], p["lat"], p["lng"], p["address"], p.get("image_url", ""), p["source"])
                    )
                    new_id = cursor.lastrowid
                    
                    # 同步寫入 ChromaDB (使用 Dummy Vector)
                    doc = f"這是一個名為「{p['name']}」的備援場域。位於{p['address']}。"
                    await chroma_repo.upsert_pois(
                        ids=[f"real_poi_{new_id}"],
                        embeddings=[DUMMY_VECTOR],
                        documents=[doc],
                        metadatas=[{
                            "poi_id": new_id,
                            "name": p["name"],
                            "category": p["category"],
                            "source": f"{p['source']}_LBS_ONLY"
                        }]
                    )
                    total_dummy += 1
                except Exception: # 忽略重複名稱
                    pass
            await db.commit()

    print(f"\n✅ 載入完成！")
    print(f"  ✨ 新增精華資料 (待 AI 嵌入): {total_essence} 筆")
    print(f"  🧱 新增備援資料 (純 LBS 模式): {total_dummy} 筆")
    print(f"  💡 接下來請執行 python3 src/data_pipeline/embed_incremental.py 完成精華部分的向量化。")

if __name__ == "__main__":
    asyncio.run(process_and_load())
