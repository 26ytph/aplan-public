import asyncio
import json
from src.core.retriever import Retriever
from src.api.v1.schemas import RecommendationRequest
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine 公式計算距離 (公里)"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

async def run_tests():
    retriever = Retriever()
    print("="*60)
    print("🚀 Data Journey: Retriever 排序修復與情境自動化驗證")
    print("="*60)
    
    # --- Test Case A: 捷運三民站咖啡店 (Transit Hybrid + GPS Fix) ---
    print("\n🟢 [Test Case A] 捷運三民站附近的咖啡店 (驗證 LBS 降分修正與類別排除)")
    req_a = RecommendationRequest(
        user_id='test_A',
        latitude=25.0515,  # 南京三民站經緯度
        longitude=121.5606,
        radius_km=5.0,
        interests=['美食', '咖啡'],
        current_time='現在',
        weather='晴天',
        raw_intent='捷運三民站附近的咖啡店'
    )
    pois_a = await retriever.get_candidate_pois(req_a, limit=5)
    print(f"✅ 取得候選名單: {len(pois_a)} 筆")
    for i, p in enumerate(pois_a[:3]):
        dist = calculate_distance(req_a.latitude, req_a.longitude, float(p['lat']), float(p['lng']))
        print(f"  {i+1}. {p['name']} | 距離: {dist:.2f} km | 語意: {p.get('semantic_distance', 0):.4f} | 類別: {p['category']}")
        if i == 0 and dist > 1.0:
            print("  ❌ [警告] Top 1 推薦距離超過 1km，排序算法依然偏袒語意！")
            
    # --- Test Case B: 捷運北投站美食 (OSM Coverage + GPS Fix) ---
    print("\n🟢 [Test Case B] 捷運北投站附近的美食餐廳 (驗證 OSM 擴充資料沙漠綠化)")
    req_b = RecommendationRequest(
        user_id='test_B',
        latitude=25.1321,  # 北投站經緯度
        longitude=121.4984,
        radius_km=2.0,
        interests=['美食', '在地小吃'],
        current_time='現在',
        weather='晴天',
        raw_intent='捷運北投站附近的美食餐廳'
    )
    pois_b = await retriever.get_candidate_pois(req_b, limit=5)
    print(f"✅ 取得候選名單: {len(pois_b)} 筆")
    for i, p in enumerate(pois_b[:3]):
        dist = calculate_distance(req_b.latitude, req_b.longitude, float(p['lat']), float(p['lng']))
        print(f"  {i+1}. {p['name']} | 距離: {dist:.2f} km | 來源: {p['source']}")

    # --- Test Case C: 暴雨室內展覽 (Complex Weather Intent) ---
    print("\n🟢 [Test Case C] 下著暴雨的台北，找室內展覽喝咖啡 (驗證混和語意提取與天氣)")
    req_c = RecommendationRequest(
        user_id='test_C',
        latitude=25.0412,  # 國父紀念館周邊
        longitude=121.5576,
        radius_km=10.0,
        interests=['展覽', '咖啡', '室內避雨'],
        current_time='下午',
        weather='大雨滂沱',
        raw_intent='下著暴雨的台北，我想找個不會淋濕的地方看展覽喝咖啡。'
    )
    pois_c = await retriever.get_candidate_pois(req_c, limit=5)
    print(f"✅ 取得候選名單: {len(pois_c)} 筆")
    for i, p in enumerate(pois_c[:3]):
        # 我們期望看到設計館、美術館或室內展演空間
        print(f"  {i+1}. {p['name']} | 類別: {p['category']} | 描述截取: {p.get('description', '')[:20]}")

    print("\n" + "="*60)
    print("🎯 所有測試執行完畢。若距離皆符合常理，代表排序 Bug 已成功修復！")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_tests())
