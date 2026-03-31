import asyncio
import sys
import os

# 確保可讀取 src 套件
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.retriever import Retriever
from src.api.v1.schemas import RecommendationRequest

async def test_retrieval():
    print("⏳ 初始化 Retriever...")
    retriever = Retriever()
    
    # 測試情境 1：抽象的語意需求 ("想找個買東西逛街的地方，晚上去")
    req1 = RecommendationRequest(
        user_id="test_1",
        interests=["商圈購物"], # 這是原本的標籤
        current_time="晚上 8 點"
    )
    
    # 我們在 Retriever 裡面的 query_text 組合邏輯為: "我想尋找適合 商圈購物 的景點或活動" 加上時間天氣
    
    print("\n==============================")
    print("🔍 測試一：標籤 [商圈購物], 晚上")
    results1 = await retriever.get_candidate_pois(req1, limit=3)
    for r in results1:
        print(f"👉 {r['name']} (距離分數: {r.get('semantic_distance', 'N/A')}) - {r['category']}")


    # 測試情境 2：完全空標籤 (倚靠自然語言)
    req2 = RecommendationRequest(
        user_id="test_2",
        interests=["看風景喝咖啡"], # 不是內建標籤
        weather="大雨滂沱"
    )
    print("\n==============================")
    print("🔍 測試二：非內建標籤 [看風景喝咖啡], 大雨滂沱")
    results2 = await retriever.get_candidate_pois(req2, limit=3)
    for r in results2:
        print(f"👉 {r['name']} (距離分數: {r.get('semantic_distance', 'N/A')}) - {r['category']}")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
