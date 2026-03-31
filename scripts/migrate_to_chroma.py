import asyncio
import sys
import os

# 確保可讀取 src 套件
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.repository import DatabaseRepository
from src.db.vector_store import VectorDBRepository
from src.utils.llm_adapter import get_llm_adapter

async def migrate_pois_to_chroma():
    """
    將 SQLite 中的所有 POI 讀出，打 Embedding 後寫入 ChromaDB。
    """
    print("⏳ 初始化資料庫存取層與 LLM...", flush=True)
    sqlite_repo = DatabaseRepository()
    chroma_repo = VectorDBRepository()
    adapter = get_llm_adapter("gemini")
    
    # 1. 取得 SQLite 內所有景點
    print("⏳ 從 SQLite 讀取 POIs...", flush=True)
    all_pois = await sqlite_repo.get_all_pois()
    if not all_pois:
        print("沒有找到景點資料，請先執行 generate_mock_data.py")
        return
        
    ids = []
    documents = []
    metadatas = []
    
    # 2. 準備文本並取得 Embeddings
    print(f"⏳ 開始為 {len(all_pois)} 筆景點取得 Embedding...", flush=True)
    embeddings = []
    
    for poi in all_pois:
        # 將對話/場景豐富的資訊寫入 Document 幫助語意匹配
        doc_text = f"這是一個名為「{poi['name']}」的景點。分類屬於「{poi['category']}」。詳細描述：{poi['description']}"
        
        # 由於速率限制，實務上可加上 delay 或批次，但此為 Demo 15 筆，應可直接打
        try:
            emb = await adapter.get_embedding(doc_text)
            
            ids.append(f"poi_{poi['id']}")
            documents.append(doc_text)
            embeddings.append(emb)
            metadatas.append({
                "poi_id": poi['id'],
                "name": poi['name'],
                "category": poi['category']
            })
            print(f"✅ 成功處理: {poi['name']}")
        except Exception as e:
            print(f"❌ 處理 {poi['name']} 失敗: {e}")
            
    # 3. 寫入 ChromaDB
    print(f"⏳ 寫入 {len(ids)} 筆資料至 ChromaDB...", flush=True)
    if ids:
        await chroma_repo.upsert_pois(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        print("🎉 POI 向量建置完成！(語意搜尋已啟用)")
    else:
        print("⚠️ 沒有資料可寫入。")

if __name__ == "__main__":
    asyncio.run(migrate_pois_to_chroma())
