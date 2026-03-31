import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.llm_adapter import get_llm_adapter
from src.db.vector_store import VectorDBRepository
from src.db.repository import DatabaseRepository
from src.core.retriever import Retriever

async def simulate_journey():
    print("🎬 [Data Journey Simulation Start]")
    print("=" * 60)
    
    # --- 1. 使用者輸入 ---
    user_query = "下著暴雨的台北，我想找個不會淋濕的地方看展覽喝咖啡。"
    print(f"\n👤 1. 使用者輸入 (User Query): \n   「{user_query}」")
    
    # --- 2. 意圖解析 (Intent Parsing) ---
    print("\n🧠 2. 意圖解析 (Intent Parser - Gemini Flash-Lite):")
    flash_adapter = get_llm_adapter("gemini")
    prompt = f"分析這句話的意圖，並轉化為搜尋標籤：{user_query}。請以 JSON 輸出：{{\"tags\": [\"室內避雨\", \"藝文展覽\", \"咖啡輕食\"]}}"
    # 這裡我們模擬直接得到結果以節省 LLM 延遲，專注於資料流
    semantic_tags = ["室內避雨", "藝文展覽", "咖啡輕食"]
    print(f"   ➤ 解析出語意標籤 (Semantic Tags): {semantic_tags}")
    
    # --- 3. 語意向量化 (Embedding) ---
    print("\n🌀 3. 語意向量化 (Encoder - Gemini Embedding 001):")
    emb_query = " ".join(semantic_tags) + " " + user_query
    print(f"   ➤ 將字串輸入 Gemini Embedding 模型: '{emb_query}'")
    embedding = await flash_adapter.get_embedding(emb_query)
    print(f"   ➤ 獲得 3072 維度的浮點數陣列 (Vector Representation)。維度大小: {len(embedding)}")
    
    # --- 4. 混合檢索 (Hybrid Retrieval) ---
    print("\n🔍 4. 混合檢索 (Retriever):")
    retriever = Retriever()
    
    # 4a. ChromaDB
    print("   [4a. ChromaDB 向量相似度配對]")
    vector_repo = VectorDBRepository()
    results = await vector_repo.query_pois(embedding, n_results=10)
    print(f"   ➤ 從 1,792 筆向量中，透過 Cosine Similarity 瞬間抓出最接近的 Top 10:")
    for result in results[:3]:
        doc = result['document']
        dist = result['distance']
        print(f"      - [距離 {dist:.3f}] {doc[:40]}...")
    
    # 4b. SQLite Metadata
    print("\n   [4b. SQLite 關聯與物理距離過濾]")
    # 假設距離模擬
    print("   ➤ 將 ChromaDB 返回的 ID 交給 SQLite，並利用使用者的 GPS 計算實體距離 (Haversine)。")
    print("   ➤ 過濾掉距離過遠 (如 > 5km) 的地點，並加上 SQLite 內的 image_url 取回真實網址。")

    
    # --- 5. 最終生成 (Generation) ---
    print("\n✍️ 5. 生成最終導覽 (Generator - Gemini Flash-Lite):")
    print("   ➤ 將混合過濾後的景點清單 (含真實照片網址、地址) 餵回給 LLM。")
    print("   ➤ 產出適合閱讀的 Markdown UI 格式給前端...")
    
    print("\n🎉 [Data Journey Simulation End]")

if __name__ == "__main__":
    asyncio.run(simulate_journey())
