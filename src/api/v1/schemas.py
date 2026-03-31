from pydantic import BaseModel, Field
from typing import List, Optional

# === HTTP Request ===

class RecommendationRequest(BaseModel):
    """
    前端傳來的推薦請求結構。
    強制進行資料型別與範圍驗證。
    """
    user_id: str = Field(..., description="使用者 ID 或匿名 Session ID")
    interests: List[str] = Field(
        default_factory=list, 
        description="使用者選取的主題標籤（如：夜間美食、文青散策）"
    )
    latitude: Optional[float] = Field(None, description="使用者目前緯度")
    longitude: Optional[float] = Field(None, description="使用者目前經度")
    current_time: Optional[str] = Field(None, description="使用者當下時間或預計旅遊時間 (如：晚上 8 點)")
    weather: Optional[str] = Field(None, description="當地即時氣象資訊 (如：晴天、微雨)")
    raw_intent: Optional[str] = Field(None, description="使用者最原始的輸入語句 (可供語意檢索直接使用)")
    radius_km: Optional[float] = Field(None, description="使用者指定的絕對地理搜索半徑 (如：方圓 3 公里)")
    lang: Optional[str] = Field("zh-TW", description="前端語系代碼 (zh-TW/ja/ko/en/th)，非 zh-TW 時推薦結果會自動翻譯")

# === HTTP Response ===

class UBikeStation(BaseModel):
    station_name: str = Field(..., description="YouBike 站點名稱")
    available_bikes: int = Field(0, description="目前可借車輛數")
    empty_docks: int = Field(0, description="目前可還空位數")
    distance_m: int = Field(0, description="距離計算基準點的實體距離(公尺)")

class UBikeRecommendation(BaseModel):
    """
    附屬於景點推薦卡的微交通建議
    """
    start_station: Optional[UBikeStation] = Field(None, description="距離使用者最近且有車可借的站點")
    end_station: Optional[UBikeStation] = Field(None, description="距離景點最近且有位可還的站點")

class RecommendedPOI(BaseModel):
    """
    單一推薦景點的詳細資訊結構
    """
    poi_id: int = Field(..., description="對應 SQLite pois 表中的 ID")
    name: str = Field(..., description="景點或消費場域名稱")
    reason: str = Field(..., description="LLM 結合社群輿情與使用者情境所撰寫的客製化推薦理由")
    address: Optional[str] = Field(None, description="真實地址")
    image_url: Optional[str] = Field(None, description="景點照片網址")
    lat: Optional[float] = Field(None, description="景點緯度")
    lng: Optional[float] = Field(None, description="景點經度")
    ubike_info: Optional[UBikeRecommendation] = Field(None, description="專屬微交通建議 (起迄站點資訊)")

class RecommendationResponse(BaseModel):
    """
    回傳給前端的標準化推薦結果結構。
    此結構的 JSON Schema 也會作為 System Prompt 傳給 LLM 進行強制約束。
    """
    itinerary_summary: str = Field(..., description="整趟客製化行程的總結建議 (約 50-100 字，口吻親切)")
    recommended_pois: List[RecommendedPOI] = Field(..., description="推薦的景點與活動清單 (通常 2-4 個)")

# === Intent Parsing (Sprint 4.3) ===

class IntentRequest(BaseModel):
    """
    前端傳來的意圖解析請求，包含使用者自然語言與當下畫面的可用選項。
    """
    user_input: str = Field(..., description="使用者輸入的自然語言 (語音或打字)")
    available_locations: List[str] = Field(..., description="畫面下拉選單中可選的地點名稱")
    available_tags: List[str] = Field(..., description="畫面上所有的可選標籤名稱")

class IntentResponse(BaseModel):
    """
    LLM 解析後的結構化意圖，供前端 JS 去尋找對應的 DOM 元素。
    """
    selected_location: Optional[str] = Field(None, description="使用者提及的地點 (優先從 available_locations 選取，若該清單沒有但使用者明確提到地名則直接回傳地名，皆無則 null)")
    selected_weather: Optional[str] = Field(None, description="使用者提及的天氣 (如：晴時多雲、大雨滂沱、寒流來襲，若無則 null)")
    selected_time: Optional[str] = Field(None, description="使用者提及的時間 (如：清晨五點、晚上、週末下午，若無則 null)")
    selected_tags: List[str] = Field(default_factory=list, description="使用者提及的興趣標籤 (必須在 available_tags 中)")
    radius_km: Optional[float] = Field(None, description="使用者指定的絕對地理搜索半徑 (如：方圓 3 公里 -> 3.0，附近 -> 1.0，沒有提到範圍則 null)")

# === Metadata (Frontend Options) ===

class LocationOption(BaseModel):
    """前端下拉選單中的地點選項"""
    id: int
    name: str
    lat: float
    lng: float

class MetadataResponse(BaseModel):
    """提供前端動態選項所需的 Metadata"""
    categories: List[str]
    locations: List[LocationOption]

# === Fast-Track One-Shot (Phase 27) ===

class FastRecommendRequest(BaseModel):
    """
    One-Shot 快速推薦請求：前端直接傳入原始語句，後端一次完成
    意圖解析 (Regex) + RAG 檢索 + LLM 推薦 + 翻譯。
    """
    user_input: str = Field(..., description="使用者輸入的自然語言")
    lang: Optional[str] = Field("zh-TW", description="前端語系代碼")
    latitude: Optional[float] = Field(None, description="使用者目前所在(或UI選擇)的緯度")
    longitude: Optional[float] = Field(None, description="使用者目前所在(或UI選擇)的經度")
    radius_km: Optional[float] = Field(None, description="UI現有的搜索半徑 (公里)")
    current_time: Optional[str] = Field(None, description="UI現有的出遊時間")
    current_weather: Optional[str] = Field(None, description="UI現有的天氣")
    current_location_name: Optional[str] = Field(None, description="UI現有的位置名稱")
    available_locations: List[str] = Field(default_factory=list, description="畫面下拉選單中可選的地點名稱")
    available_tags: List[str] = Field(default_factory=list, description="畫面上所有的可選標籤名稱")

class FastRecommendResponse(BaseModel):
    """
    One-Shot 合併回應：同時包含意圖解析結果 + 推薦結果，
    前端拿到後一次性更新 UI + 渲染卡片。
    """
    # 意圖解析結果 (供前端同步更新 UI 條件)
    selected_location: Optional[str] = Field(None)
    resolved_lat: Optional[float] = Field(None, description="後端解析出的最終緯度")
    resolved_lng: Optional[float] = Field(None, description="後端解析出的最終經度")
    selected_weather: Optional[str] = Field(None)
    selected_time: Optional[str] = Field(None)
    selected_tags: List[str] = Field(default_factory=list)
    radius_km: Optional[float] = Field(None)
    # 推薦結果 (直接渲染) 
    itinerary_summary: str = Field(..., description="AI 行程總結")
    recommended_pois: List[RecommendedPOI] = Field(..., description="推薦景點清單")
