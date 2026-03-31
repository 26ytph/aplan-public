import asyncio
import os
import sys
import re

# 修正匯入路徑
sys.path.append(os.getcwd())

from src.core.retriever import Retriever
from src.core.recommendation_engine import RecommendationEngine
from src.api.v1.schemas import RecommendationRequest, IntentRequest
from src.api.v1.intent import _parse_with_regex, get_llm_client

async def simulate_fast_recommend(user_input: str):
    retriever = Retriever()
    # 修正：傳入 llm_adapter
    engine = RecommendationEngine(llm_adapter=get_llm_client())
    
    # 模擬前端傳入的初始狀態 (台北市政府)
    initial_lat, initial_lng = 25.039, 121.564
    available_locations = ["台北市政府", "台北 101", "松山文創園區"]
    available_tags = ["美食小吃", "藝文音樂", "歷史古蹟", "時尚購物", "放鬆休息", "親子同樂", "自然探索", "室內避雨"]
    
    print(f"\n🚀 [測試語句]: 「{user_input}」")
    
    # 1. 意圖解析 (模擬 Regex Fallback)
    intent_req = IntentRequest(
        user_input=user_input,
        available_locations=available_locations,
        available_tags=available_tags
    )
    intent = _parse_with_regex(intent_req)
    print(f"📊 [意圖解析]: Weather={intent.selected_weather}, Tags={intent.selected_tags}")
    
    # 2. 構建請求
    final_lat = initial_lat
    final_lng = initial_lng
    final_weather = intent.selected_weather or "晴時多雲"
    
    request = RecommendationRequest(
        user_id="debug_user",
        interests=intent.selected_tags,
        latitude=final_lat,
        longitude=final_lng,
        weather=final_weather,
        raw_intent=user_input
    )
    
    # 3. 檢索
    candidates = await retriever.get_candidate_pois(request)
    print(f"🔍 [檢索候選人]: 找到 {len(candidates)} 個景點")
    
    # 4. 生成導覽
    poi_ids = [p["id"] for p in candidates]
    social_trends = await retriever.get_positive_trends_for_pois(poi_ids)
    
    # 注意：這裡就是 LLM 生成的地方，結果筆數 (2-4) 由 LLM 決定
    response = await engine.generate_smart_itinerary(request, candidates, social_trends)
    
    print(f"✨ [AI 推薦結果] (共 {len(response.recommended_pois)} 筆):")
    for i, poi in enumerate(response.recommended_pois):
        print(f"  {i+1}. {poi.name}")
    print(f"📝 [總結]: {response.itinerary_summary[:100]}...")

async def main():
    # 測試中文
    await simulate_fast_recommend("下著暴雨，我在台北市政府，我想找個不會淋濕的地方看展覽喝咖啡")
    # 測試英文
    await simulate_fast_recommend("Heavy Rain, Taipei City Hall, see exhibitions and drink coffee.")

if __name__ == "__main__":
    asyncio.run(main())
