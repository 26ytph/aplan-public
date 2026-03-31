import asyncio
import sys
import os

sys.path.append(os.getcwd())
try:
    from src.core.retriever import Retriever
    from src.api.v1.schemas import RecommendationRequest
except ImportError:
    print("Error: Could not import Retriever or Schemas")
    sys.exit(1)

async def debug_journey():
    print("🚀 [Step 1] 初始化檢索器與載入語意模型...")
    r = Retriever()
    
    intent = "下著暴雨，我想找個不會淋濕的地方看展覽喝咖啡"
    lat, lng = 25.039, 121.564  # 台北市政府
    
    # 建構 Request
    req = RecommendationRequest(
        user_id="debug_user",
        user_input=intent,
        latitude=lat,
        longitude=lng,
        radius_km=10.0,
        interests=["spot", "food", "cafe"],
        weather="暴雨",
        current_time="下午"
    )
    req.raw_intent = intent

    print(f"\n📍 [Step 2] 使用者情境\n語句: {intent}\n位置: 台北市政府 (Lat: {lat}, Lng: {lng})\n設定：距離處罰係數 0.2 + Tier提拔機制")
    
    # Step 3A: Mock "What ChromaDB saw" by stripping GPS momentarily
    req_chroma_only = RecommendationRequest(
        user_id="debug_user_2",
        user_input=intent,
        latitude=None,  # No GPS = No Distance penalty
        longitude=None,
        radius_km=10.0,
        interests=["spot", "food", "cafe"]
    )
    req_chroma_only.raw_intent = intent
    print("\n🔍 [Step 3A] 先看純語意 (無物理距離懲罰與GPS)...")
    raw_results = await r.get_candidate_pois(request=req_chroma_only, limit=5)
    for idx, p in enumerate(raw_results, 1):
        print(f" {idx}. {p['name']} | 距離: 無限制 | Tier: {p.get('tier',3)} | 原始語意距離: {p.get('semantic_distance', 0):.3f}")

    print("\n🔍 [Step 3B] 最終 Hybrid 推薦 (啟動 SQLite 距離 0.2 懲罰 + Tier提拔)...")
    results = await r.get_candidate_pois(request=req, limit=5)
    
    print("\n🏆 [最終前 5 名推薦結果]")
    for idx, p in enumerate(results, 1):
        print(f"{idx}. {p['name']} | 分類: {p['category']} | {p.get('distance_km', 0):.2f}km | Tier: {p.get('tier', 3)} | 最終權重分數(越低越好): {p.get('semantic_distance', 0):.3f}")

if __name__ == "__main__":
    asyncio.run(debug_journey())
