import asyncio
import json
import aiosqlite
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from src.core.config import get_settings
from src.db.vector_store import VectorDBRepository
from src.utils.llm_adapter import get_llm_adapter

async def main():
    settings = get_settings()
    with open("scripts/data/enriched_hilton_pois.json", "r", encoding="utf-8") as f:
        pois = json.load(f)
    vector_db = VectorDBRepository()
    adapter = get_llm_adapter("gemini")
    
    async with aiosqlite.connect(settings.db_path) as db:
        for poi in pois:
            cursor = await db.execute("""
                INSERT INTO pois (name, category, description, address, lat, lng, image_url, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (poi["name"], poi["category"], poi["description"], poi.get("address", ""), poi["lat"], poi["lng"], poi.get("image_url", ""), poi["source"]))
            sql_id = cursor.lastrowid
            
            text_for_embedding = f"景點名稱: {poi['name']}\n類別: {poi['category']}\n描述: {poi['description']}\n地址: {poi.get('address', '')}"
            embedding = await adapter.get_embedding(text_for_embedding)
            
            await vector_db.upsert_pois(ids=[str(sql_id)], embeddings=[embedding], documents=[text_for_embedding], metadatas=[{"poi_id": sql_id, "name": poi["name"], "category": poi["category"]}])
            await db.execute("UPDATE pois SET is_embedded = 1 WHERE id = ?", (sql_id,))
            print(f"✅ 成功匯入並向量化: {poi['name']}")
        await db.commit()

asyncio.run(main())
