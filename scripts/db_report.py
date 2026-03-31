import sqlite3
import os
import time
import asyncio
import sys
sys.path.append('/Users/ytp-thomas/Desktop/APlan')
from src.core.retriever import Retriever
from src.api.v1.schemas import RecommendationRequest
from src.core.config import get_settings

settings = get_settings()
DB_PATH = settings.db_path
print("DB Path:", DB_PATH)

def get_dir_size(path):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total

async def measure_retrieval():
    retriever = Retriever()
    req = RecommendationRequest(
        user_id="test",
        raw_intent="找個安靜的地方喝咖啡",
        latitude=25.033,
        longitude=121.565
    )
    start = time.time()
    await retriever.get_candidate_pois(req, limit=5)
    end = time.time()
    return end - start

async def main():
    if os.path.exists(DB_PATH):
        sqlite_size = os.path.getsize(DB_PATH) / (1024 * 1024)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT count(*) FROM pois")
        count = c.fetchone()[0]
        
        c.execute("SELECT DISTINCT category FROM pois")
        categories = [r[0] for r in c.fetchall()]
        print(f"==============================")
        print(f"📊 SQLite 資料庫狀態")
        print(f"  └ POI 總筆數: {count}")
        print(f"  └ 檔案大小: {sqlite_size:.2f} MB")
        print(f"  └ 存在的分類標籤: {categories}")
    else:
        print("SQLite DB not found at", DB_PATH)

    chroma_path = "/Users/ytp-thomas/Desktop/APlan/.gemini/chroma_db"
    if os.path.exists(chroma_path):
        chroma_size = get_dir_size(chroma_path) / (1024 * 1024)
        print(f"==============================")
        print(f"🧠 ChromaDB 向量庫狀態")
        print(f"  └ 目錄大小: {chroma_size:.2f} MB")

    latency = await measure_retrieval()
    print(f"==============================")
    print(f"⚡ 檢索效能測試 (Semantic Retrieval)")
    print(f"  └ Gemini Embedding + Chroma Query + SQLite Join 耗時: {latency:.3f} 秒")
    print(f"==============================")

if __name__ == "__main__":
    asyncio.run(main())
