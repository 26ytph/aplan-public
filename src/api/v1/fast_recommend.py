"""
Phase 27 (方案 C): Parallel LLM Intent + ChromaDB Fast-Track
────────────────────────────────────────────────────────────
流程：
  ┌─ asyncio.gather ──────────────────────────────────────┐
  │  Task A: LLM 意圖解析 (location/time/weather/tags)    │ ~3s
  │  Task B: ChromaDB 語意搜尋 (raw_intent + 設備 GPS)    │ ~0.1s
  └──────────────────────┬────────────────────────────────┘
                         ▼
  Step 2: 用 Intent 解析到的地點覆蓋 GPS 座標
  Step 3: 若 GPS 改變 → 重跑 ChromaDB (帶正確 GPS)        ~0.1s
  Step 4: LLM 推薦 + 翻譯 (唯一的第二次 AI 呼叫)          ~7s
────────────────────────────────────────────────────────────
總延遲: max(3s, 0.1s) + 0.1s + 7s ≈ 10s (比舊流程 ~13s 快 ~3s)
"""
import asyncio
import json
import os
import time
import re
from typing import List, Dict, Any, Tuple, Optional

from fastapi import APIRouter, Depends, HTTPException, status
import aiosqlite

from src.utils.llm_adapter import LLMAdapter, get_llm_adapter
from src.api.v1.schemas import (
    FastRecommendRequest, FastRecommendResponse,
    IntentRequest, IntentResponse,
    RecommendationRequest, RecommendationResponse
)
from src.api.v1.intent import _parse_with_regex
from src.core.retriever import Retriever
from src.core.recommendation_engine import RecommendationEngine

router = APIRouter(
    prefix="/fast-recommend",
    tags=["Fast-Track Recommendation"],
)

def get_llm_client() -> LLMAdapter:
    return get_llm_adapter(model_type="gemini")

def get_retriever() -> Retriever:
    return Retriever()

def get_engine(llm: LLMAdapter = Depends(get_llm_client)) -> RecommendationEngine:
    return RecommendationEngine(llm_adapter=llm)

# === 地點座標字典 (Lazy Loading with Auto-Reload) ===
_LOCATION_DICT = None
_DICT_MTIME = 0

def _get_location_dict() -> dict:
    """延遲載入且具備 Auto-Reload 機制，確保實體檔案更新時能即時反應"""
    global _LOCATION_DICT, _DICT_MTIME
    
    dict_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "location_dictionary.json")
    
    # 檢查檔案最後修改時間
    try:
        current_mtime = os.path.getmtime(dict_path)
    except OSError:
        current_mtime = 0

    # 如果記憶體中已有資料且檔案沒動過，直接回傳
    if _LOCATION_DICT is not None and current_mtime <= _DICT_MTIME:
        return _LOCATION_DICT
    
    # 執行載入或重載
    if os.path.exists(dict_path):
        try:
            with open(dict_path, "r", encoding="utf-8") as f:
                _LOCATION_DICT = json.load(f)
            _DICT_MTIME = current_mtime
            print(f"📍 [Fast-Track] 地點字典同步成功: {len(_LOCATION_DICT)} 筆")
        except Exception as e:
            print(f"❌ [Fast-Track] 載入失敗: {e}")
            if _LOCATION_DICT is None: _LOCATION_DICT = {}
    else:
        _LOCATION_DICT = {}
        
    return _LOCATION_DICT


async def _llm_parse_intent(user_input: str, available_locations: list, available_tags: list) -> IntentResponse:
    """
    LLM 意圖解析 (複用 intent.py 的 Prompt 邏輯)。
    新增解析 radius_km 以支援精細的距離搜尋。
    失敗時降級為 Regex。
    """
    llm = get_llm_adapter(model_type="gemini")
    available_weather = ["晴時多雲", "大雨滂沱", "寒流來襲", "微涼無雨"]
    
    prompt = f"""
    你是一個精準的 UI 意圖解析器 (Intent Parser)。
    你的任務是閱讀使用者的口語輸入，並將其轉化為高維度的檢索特徵。
    
    【可用選項清單】
    - 可選的地點 (Locations): {available_locations}
    - 可選的天氣 (Weather): {available_weather}
    - 系統預設標籤 (Default Tags): {available_tags}
    
    【使用者輸入】
    "{user_input}"
    
    【任務規則】
    1. 從輸入中找出最符合的地點。優先從 Locations 清單中挑選；若無則回傳使用者明確提及的「具體區域或地標」(例如: 西門町、大巨蛋)。**極重要限制**：絕對不可將單純的縣市名稱 (如: Taipei, 台北, 台灣) 或模糊代名詞 (如: 這裡、附近、這附近) 視為具體地點，若使用者僅提及這些泛稱，請務必回傳 null！若完全沒提到地點也回傳 null。
    2. 從輸入中找出最符合的天氣 (必須從 Weather 中挑選，沒提到回傳 null)。
    3. 從輸入中萃取最符合的時間段或情境 (若無回傳 null)。
    4. 從輸入中判斷使用者是否特別指定了搜索範圍，並轉換為公里數 (例如「附近/周邊」-> 1.0,「500公尺內」-> 0.5,「極近」-> 0.3,「遠一點/大範圍」-> 5.0)。若無明確提及則回傳 null。
    5. 【標籤萃取 (極重要)】: 請從「系統預設標籤」中挑出1項符合的類別，**並且**必須根據使用者的具體需求，額外自由生成 1~3 個「動態 Hash Tags」(例如: 咖啡店、插座、安靜、夜景)。
       總共請回傳 1~4 個標籤字串 (混合預設標籤與你自由生成的動態標籤)。
    
    【JSON 輸出約束】
    你的回覆**必須只能**是一個合法的 JSON Object。絕不允許包含 ```json 之類的 markdown 標記。
    JSON 格式：
    {{
        "selected_location": "地點名稱" 或 null,
        "selected_weather": "天氣名稱" 或 null,
        "selected_time": "時間內容" 或 null,
        "selected_tags": ["標籤名稱"],
        "radius_km": 數字 或 null
    }}
    """
    
    try:
        raw_response = await llm.generate_content(prompt, response_schema=IntentResponse)
        clean = raw_response.strip()
        if clean.startswith("```json"): clean = clean[len("```json"):]
        elif clean.startswith("```"): clean = clean[len("```"):]
        if clean.endswith("```"): clean = clean[:-len("```")]
        clean = clean.strip()
        start_idx = clean.find('{')
        end_idx = clean.rfind('}')
        if start_idx != -1 and end_idx != -1:
            clean = clean[start_idx:end_idx+1]
        return IntentResponse(**json.loads(clean))
    except Exception as e:
        print(f"⚠️ [Fast-Track] LLM Intent 失敗 ({str(e)[:80]}...)，降級為 Regex")
        intent_req = IntentRequest(
            user_input=user_input,
            available_locations=available_locations,
            available_tags=available_tags
        )
        # Regex 不支援 radius_km，但至少不會崩潰
        return _parse_with_regex(intent_req)



async def _resolve_location_to_gps(location_name: str, db_path: str) -> Tuple[Optional[float], Optional[float]]:
    """解析地名為 GPS 座標 (1. 字典比對 -> 2. 資料庫模糊搜尋)"""
    loc_dict = _get_location_dict()
    
    if not location_name:
        return None, None
    
    location_name = location_name.strip()
    # 去掉常見後綴：「大巨蛋附近」→「大巨蛋」
    cleaned = re.sub(r'(附近|旁邊|周邊|一帶|那邊|那裡|這邊|這裡|商圈|站)$', '', location_name)
    
    print(f"📍 [GPS Resolve] 嘗試解析: 「{location_name}」 (清理後: {cleaned})")
    
    # 1. 字典比對 (快軌)
    if cleaned in loc_dict:
        c = loc_dict[cleaned]
        print(f"📍 [GPS Resolve] ✅ 字典精確命中: 「{cleaned}」")
        return c["lat"], c["lng"]
    
    for dict_name, coords in loc_dict.items():
        if cleaned in dict_name or dict_name in cleaned:
            print(f"📍 [GPS Resolve] ✅ 字典模糊命中: 「{dict_name}」")
            return coords["lat"], coords["lng"]
            
    # 2. 資料庫回補 (對付字典未收錄的名勝，如 大巨蛋)
    print(f"📍 [GPS Resolve] 字典未命中，嘗試從資料庫回補...")
    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            # 搜尋名稱完全匹配或包含關係的 POI
            cursor = await db.execute(
                "SELECT lat, lng, name FROM pois WHERE name LIKE ? OR ? LIKE '%' || name || '%' ORDER BY length(name) ASC LIMIT 1",
                (f"%{cleaned}%", cleaned)
            )
            row = await cursor.fetchone()
            if row:
                print(f"📍 [GPS Resolve] ✅ 資料庫命中: 「{row['name']}」 → ({row['lat']}, {row['lng']})")
                return row["lat"], row["lng"]
    except Exception as e:
        print(f"❌ [GPS Resolve] 資料庫查詢失敗: {e}")
        
    return None, None


@router.post("/", response_model=FastRecommendResponse)
async def fast_recommend(
    request: FastRecommendRequest,
    retriever: Retriever = Depends(get_retriever),
    engine: RecommendationEngine = Depends(get_engine)
):
    """
    方案 C: Parallel LLM Intent + ChromaDB → GPS 修正 → LLM Recommend
    """
    t_start = time.time()
    
    # Task A: LLM 意圖解析
    intent_task = _llm_parse_intent(
        user_input=request.user_input,
        available_locations=request.available_locations,
        available_tags=request.available_tags
    )
    
    # Task B: ChromaDB 初步搜尋 (先用 UI 傳來的現有狀態)
    initial_rec_request = RecommendationRequest(
        user_id="fast_track_user",
        interests=[],
        latitude=request.latitude,
        longitude=request.longitude,
        current_time=request.current_time,
        weather=request.current_weather,
        raw_intent=request.user_input,
        radius_km=request.radius_km,
        lang=request.lang
    )
    chromadb_task = retriever.get_candidate_pois(initial_rec_request, limit=5)
    
    # 並行跑！
    intent, initial_candidates = await asyncio.gather(intent_task, chromadb_task)
    
    t_parallel = time.time()
    print(f"⚡ [Fast-Track] Intent: loc={intent.selected_location}, tags={intent.selected_tags}, radius={intent.radius_km}, time={intent.selected_time}")
    
    # ================================================================
    # [Phase 28] UI 狀態與 AI 意圖的繼承與融合 (State Inheritance)
    # ================================================================
    
    # 1. Location & GPS
    resolved_lat = request.latitude
    resolved_lng = request.longitude
    final_location_name = request.current_location_name
    gps_changed = False
    
    if intent.selected_location:
        lat, lng = await _resolve_location_to_gps(intent.selected_location, retriever.db_path)
        if lat is not None and lng is not None:
            resolved_lat = lat
            resolved_lng = lng
            final_location_name = intent.selected_location
            gps_changed = True
            print(f"⚡ [Fast-Track] 📌 AI 地點優先生效: 「{final_location_name}」→ ({resolved_lat}, {resolved_lng})")
        else:
            print(f"⚡ [Fast-Track] ⚠️ 地點「{intent.selected_location}」無法解析，維持 UI 目前位置: 「{final_location_name}」")
            # 若真解不出來，還是把 LLM 抓出的名字傳回 UI，但沿用 UI 原 GPS
            final_location_name = intent.selected_location 
    else:
        print(f"⚡ [Fast-Track] 🔹 語意無指定地點，繼承 UI 目前位置: 「{final_location_name}」")
    
    # 2. Radius
    final_radius = intent.radius_km if intent.radius_km is not None else request.radius_km
    if final_radius != request.radius_km:
        print(f"⚡ [Fast-Track] 📌 AI 範圍優先生效: {request.radius_km} -> {final_radius}")
        
    # 3. Time & Weather
    final_time = intent.selected_time if intent.selected_time else request.current_time
    final_weather = intent.selected_weather if intent.selected_weather else request.current_weather
    if intent.selected_time: print(f"⚡ [Fast-Track] 📌 AI 時間優先生效: {final_time}")
    if intent.selected_weather: print(f"⚡ [Fast-Track] 📌 AI 天氣優先生效: {final_weather}")
    
    # ================================================================
    # 若 GPS 或 範圍有改變，重跑 ChromaDB (精準搜尋)
    # ================================================================
    need_rerun_chroma = gps_changed or (final_radius != request.radius_km)
    
    if need_rerun_chroma:
        corrected_request = RecommendationRequest(
            user_id="fast_track_user",
            interests=intent.selected_tags or [],
            latitude=resolved_lat,
            longitude=resolved_lng,
            raw_intent=request.user_input,
            radius_km=final_radius,
            lang=request.lang
        )
        candidate_pois = await retriever.get_candidate_pois(corrected_request, limit=5)
    else:
        candidate_pois = initial_candidates
    
    if not candidate_pois:
        raise HTTPException(status_code=404, detail="找不到符合條件的景點")
    
    # ================================================================
    # Step 4: LLM 推薦 + 翻譯
    # ================================================================
    try:
        rec_request = RecommendationRequest(
            user_id="fast_track_user",
            interests=intent.selected_tags or [],
            latitude=resolved_lat,
            longitude=resolved_lng,
            current_time=final_time,
            weather=final_weather,
            raw_intent=request.user_input,
            radius_km=final_radius,
            lang=request.lang
        )
        
        poi_ids = [poi["id"] for poi in candidate_pois]
        social_trends = await retriever.get_positive_trends_for_pois(poi_ids, limit_per_poi=3)
        
        rec_response = await engine.generate_smart_itinerary(
            request=rec_request,
            candidate_pois=candidate_pois,
            social_trends=social_trends
        )
        
        # ================================================================
        # [Phase 13+] 微交通即時情境層 (YouBike 2.0)
        # ================================================================
        try:
            from src.api.v1.services.ubike import UBikeService
            from src.api.v1.schemas import UBikeRecommendation, UBikeStation
            
            # 先找距離使用者最近的借車點 (必須有車)
            start_station_model = None
            if resolved_lat is not None and resolved_lng is not None:
                start_raw = await UBikeService.find_nearest_station(
                    resolved_lat, resolved_lng, require_bikes=True, max_distance_m=1000)
                if start_raw:
                    start_station_model = UBikeStation(
                        station_name=start_raw.get('sna', '').replace('YouBike2.0_', ''),
                        available_bikes=int(start_raw.get('available_rent_bikes', 0)),
                        empty_docks=int(start_raw.get('available_return_bikes', 0)),
                        distance_m=start_raw['calculated_distance_m']
                    )

            # 針對每個推薦景點，尋找附近可還車的點 (必須有位)
            for poi in rec_response.recommended_pois:
                end_station_model = None
                if poi.lat and poi.lng:
                    end_raw = await UBikeService.find_nearest_station(
                        poi.lat, poi.lng, require_docks=True, max_distance_m=1000)
                    if end_raw:
                        end_station_model = UBikeStation(
                            station_name=end_raw.get('sna', '').replace('YouBike2.0_', ''),
                            available_bikes=int(end_raw.get('available_rent_bikes', 0)),
                            empty_docks=int(end_raw.get('available_return_bikes', 0)),
                            distance_m=end_raw['calculated_distance_m']
                        )
                
                # 若至少有一端有站點，就掛載這個附屬元件
                if start_station_model or end_station_model:
                    poi.ubike_info = UBikeRecommendation(
                        start_station=start_station_model,
                        end_station=end_station_model
                    )
                    print(f"🚲 [YouBike] 成功為「{poi.name}」掛載微交通情報！")
        except Exception as e:
            print(f"⚠️ [YouBike] 取得微交通建議失敗，優雅降級 (不影響推薦系統): {str(e)}")
            
        t_end = time.time()
        print(f"🏆 [Fast-Track] 總耗時: {(t_end - t_start)*1000:.0f}ms")
        
        return FastRecommendResponse(
            selected_location=final_location_name,
            resolved_lat=resolved_lat,
            resolved_lng=resolved_lng,
            selected_weather=final_weather,
            selected_time=final_time,
            selected_tags=intent.selected_tags,
            radius_km=final_radius,
            itinerary_summary=rec_response.itinerary_summary,
            recommended_pois=rec_response.recommended_pois
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fast-Track 推薦引擎錯誤: {str(e)}"
        )
