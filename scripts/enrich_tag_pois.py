import asyncio
import json
import aiosqlite
import sys
import os

# 將專案根目錄加入路徑以便匯入 src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_settings
from src.db.vector_store import VectorDBRepository
from src.utils.llm_adapter import get_llm_adapter

async def main():
    settings = get_settings()
    db_path = settings.db_path
    print(f"📦 [Enrichment] 目標資料庫: {db_path}")
    
    with open("scripts/data/enriched_tags_pois.json", "r", encoding="utf-8") as f:
        pois = json.load(f)
        
    print(f"📥 準備匯入 {len(pois)} 筆增強型標籤景點...")
    
    vector_db = VectorDBRepository()
    adapter = get_llm_adapter("gemini")
    
    async with aiosqlite.connect(db_path) as db:
        # 建立資料表 (防呆)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pois (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                address TEXT,
                image_url TEXT,
                source TEXT,
                lat REAL,
                lng REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_embedded INTEGER DEFAULT 0
            )
        """)
        
        inserted_count = 0
        for poi in pois:
            # 檢查是否已存在
            cursor = await db.execute("SELECT id FROM pois WHERE name = ? AND source = 'ENRICHED_TAGS'", (poi["name"],))
            row = await cursor.fetchone()
            
            if row:
                print(f"⏩ 跳過已存在的景點: {poi['name']}")
                continue
                
            # Insert into SQLite
            cursor = await db.execute("""
                INSERT INTO pois (name, category, description, address, lat, lng, image_url, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                poi["name"], poi["category"], poi["description"], 
                poi.get("address", ""), poi["lat"], poi["lng"], 
                poi.get("image_url", ""), poi["source"]
            ))
            
            sql_id = cursor.lastrowid
            
            # Generate Embedding
            text_for_embedding = f"景點名稱: {poi['name']}\n類別: {poi['category']}\n描述: {poi['description']}\n地址: {poi.get('address', '')}"
            try:
                embedding = await adapter.get_embedding(text_for_embedding)
                
                # Insert into ChromaDB
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
                
                # 更新 SQLite 狀態
                await db.execute("UPDATE pois SET is_embedded = 1 WHERE id = ?", (sql_id,))
                print(f"✅ 成功匯入並向量化: {poi['name']}")
                inserted_count += 1
            except Exception as e:
                print(f"❌ 向量化失敗: {poi['name']} - {e}")
                
        await db.commit()
    print(f"🎉 腳本執行完畢！共新增 {inserted_count} 筆。")

if __name__ == "__main__":
    asyncio.run(main())
