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
    with open("scripts/data/enriched_superstores_pois.json", "r", encoding="utf-8") as f:
        pois = json.load(f)
        
    print(f"📥 準備匯入 {len(pois)} 筆知名大型賣場 (Costco, IKEA)...")
    
    vector_db = VectorDBRepository()
    adapter = get_llm_adapter("gemini")
    
    async with aiosqlite.connect(settings.db_path) as db:
        inserted_count = 0
        for poi in pois:
            cursor = await db.execute("SELECT id FROM pois WHERE name = ? AND source = 'ENRICHED_PREMIUM'", (poi["name"],))
            row = await cursor.fetchone()
            if row:
                print(f"⏩ 跳過已存在的景點: {poi['name']}")
                continue
                
            cursor = await db.execute("""
                INSERT INTO pois (name, category, description, address, lat, lng, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (poi["name"], poi["category"], poi["description"], poi.get("address", ""), poi["lat"], poi["lng"], poi["source"]))
            sql_id = cursor.lastrowid
            
            text_for_embedding = f"景點名稱: {poi['name']}\n類別: {poi['category']}\n描述: {poi['description']}\n地址: {poi.get('address', '')}"
            embedding = await adapter.get_embedding(text_for_embedding)
            await vector_db.upsert_pois(ids=[str(sql_id)], embeddings=[embedding], documents=[text_for_embedding], metadatas=[{"poi_id": sql_id, "name": poi["name"], "category": poi["category"]}])
            await db.execute("UPDATE pois SET is_embedded = 1 WHERE id = ?", (sql_id,))
            print(f"✅ 成功匯入並向量化: {poi['name']}")
            inserted_count += 1
        await db.commit()
    print(f"🎉 腳本執行完畢！共新增 {inserted_count} 筆。")

if __name__ == "__main__":
    asyncio.run(main())
