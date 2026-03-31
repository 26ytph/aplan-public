import asyncio
import sys
import os

# 確保路徑正確
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.retriever import Retriever
from src.api.v1.schemas import RecommendationRequest

async def test_retriever():
    retriever = Retriever()
    
    # 模擬 郊外踏青 Query
    req = RecommendationRequest(
        user_id="test",
        latitude=25.0392,
        longitude=121.5658,
        radius_km=5.0,
        raw_intent="郊外踏青",
        interests=["nature", "踏青"]
    )
    
    print(f"🔍 [Retriever Test] Query: {req.raw_intent} @ {req.latitude}, {req.longitude} (5km)")
    
    pois = await retriever.get_candidate_pois(req, limit=10)
    
    print("\n候選景點排名 (前 10 名)：")
    for i, poi in enumerate(pois, 1):
        print(f"{i}. {poi['name']} | Tier: {poi.get('tier')} | Dist: {poi.get('distance_km'):.2f}km | SemanticDist: {poi.get('semantic_distance'):.4f}")

if __name__ == "__main__":
    asyncio.run(test_retriever())
