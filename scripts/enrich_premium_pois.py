import asyncio
import json
import aiosqlite
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.db.vector_store import VectorDBRepository
from src.utils.llm_adapter import get_llm_adapter

async def main():
    settings = get_settings()
    db_path = settings.db_path
    print(f"📦 [Enrichment] 目標資料庫: {db_path}")
    
    with open("scripts/data/enriched_premium_pois.json", "r", encoding="utf-8") as f:
        pois = json.load(f)
        
    print(f"📥 準備匯入 {len(pois)} 筆頂級名勝 (Premium POIs)...")
    
    vector_db = VectorDBRepository()
    adapter = get_llm_adapter("gemini")
    
    async with aiosqlite.connect(db_path) as db:
        inserted_count = 0
        for poi in pois:
            cursor = await db.execute("SELECT id FROM pois WHERE name = ? AND source = 'ENRICHED_PREMIUM'", (poi["name"],))
            row = await cursor.fetchone()
            
            if row:
                print(f"⏩ 跳過已存在的景點: {poi['name']}")
                continue
                
            cursor = await db.execute("""
                INSERT INTO pois (name, category, description, address, lat, lng, image_url, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                poi["name"], poi["category"], poi["description"], 
                poi.get("address", ""), poi["lat"], poi["lng"], 
                poi.get("image_url", ""), poi["source"]
            ))
            
            sql_id = cursor.lastrowid
            text_for_embedding = f"景點名稱: {poi['name']}\n類別: {poi['category']}\n描述: {poi['description']}\n地址: {poi.get('address', '')}"
            try:
                embedding = await adapter.get_embedding(text_for_embedding)
                metadata = {
                    "poi_id": sql_id,
                    "name": poi["name"],
                    "category": poi["category"]
                }
                await vector_db.upsert_pois(
                    ids=[str(sql_id)],
                    embeddings=[embedding],
                    documents=[text_for_embedding],
                    metadatas=[metadata]
                )
                await db.execute("UPDATE pois SET is_embedded = 1 WHERE id = ?", (sql_id,))
                print(f"✅ 成功匯入並向量化: {poi['name']}")
                inserted_count += 1
            except Exception as e:
                print(f"❌ 向量化失敗: {poi['name']} - {e}")
                
        await db.commit()
    print(f"🎉 腳本執行完畢！共新增 {inserted_count} 筆。")

if __name__ == "__main__":
    asyncio.run(main())
