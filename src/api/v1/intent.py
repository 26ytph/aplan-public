import json
from fastapi import APIRouter, Depends, HTTPException, status
from src.utils.llm_adapter import LLMAdapter, get_llm_adapter
from src.api.v1.schemas import IntentRequest, IntentResponse

router = APIRouter(
    prefix="/parse-intent",
    tags=["Intent Parsing"],
)

def get_llm_client() -> LLMAdapter:
    return get_llm_adapter(model_type="gemini")

@router.post("/", response_model=IntentResponse)
async def parse_user_intent(
    request: IntentRequest,
    llm: LLMAdapter = Depends(get_llm_client)
):
    """
    將使用者的自然語言 (打字或語音) 解析為畫面上可用的 UI 選項。
    """
    
    available_weather = ["晴時多雲", "大雨滂沱", "寒流來襲", "微涼無雨"] # 為了 Demo 放一些預設選項
    
    prompt = f"""
    你是一個精準的 UI 意圖解析器 (Intent Parser)。
    你的任務是閱讀使用者的口語輸入，並將其轉化為高維度的檢索特徵。
    
    【可用選項清單】
    - 可選的地點 (Locations): {request.available_locations}
    - 可選的天氣 (Weather): {available_weather}
    - 系統預設標籤 (Default Tags): {request.available_tags}
    
    【使用者輸入】
    "{request.user_input}"
    
    【任務規則】
    1. 從輸入中找出最符合的地點。優先從 Locations 清單中挑選；若無則回傳使用者明確提及的「具體區域或地標」(例如: 西門町、大巨蛋)。**極重要限制**：絕對不可將單純的縣市名稱 (如: Taipei, 台北, 台灣) 或模糊代名詞 (如: 這裡、附近、這附近) 視為具體地點，若使用者僅提及這些泛稱，請務必回傳 null！若完全沒提到地點也回傳 null。
    2. 從輸入中找出最符合的天氣 (必須從 Weather 中挑選，沒提到回傳 null)。
    3. 從輸入中萃取最符合的時間段或情境 (若無回傳 null)。
    4. 【標籤萃取 (極重要)】: 請從「系統預設標籤」中挑出1項符合的類別，**並且**必須根據使用者的具體需求，額外自由生成 1~3 個「動態 Hash Tags」(例如: 咖啡店、插座、安靜、夜景)。
       總共請回傳 1~4 個標籤字串 (混合預設標籤與你自由生成的動態標籤)。
    
    【JSON 輸出約束】
    你的回覆**必須只能**是一個合法的 JSON Object。絕不允許包含 ```json 之類的 markdown 標記。
    JSON 格式：
    {{
        "selected_location": "地點名稱" 或 null,
        "selected_weather": "天氣名稱" 或 null,
        "selected_time": "時間內容" 或 null,
        "selected_tags": ["標籤名稱"]
    }}
    """
    
    try:
        # 主路線：Gemini 結構化輸出
        raw_response = await llm.generate_content(prompt, response_schema=IntentResponse)
        
        # 更強健的 JSON 清理
        clean_json_str = raw_response.strip()
        if clean_json_str.startswith("```json"):
            clean_json_str = clean_json_str[len("```json"):]
        elif clean_json_str.startswith("```"):
            clean_json_str = clean_json_str[len("```"):]
            
        if clean_json_str.endswith("```"):
            clean_json_str = clean_json_str[:-len("```")]
            
        clean_json_str = clean_json_str.strip()
        
        # 尋找第一個 { 和最後一個 } 以避免其他文字干擾
        start_idx = clean_json_str.find('{')
        end_idx = clean_json_str.rfind('}')
        if start_idx != -1 and end_idx != -1:
             clean_json_str = clean_json_str[start_idx:end_idx+1]
        
        response_dict = json.loads(clean_json_str)
        
        return IntentResponse(**response_dict)
        
    except Exception as e:
        # [Phase 23] 降級路線：如果 Gemini 掛了 (429/503/Timeout)，使用本地 Regex 切割
        print(f"⚠️ [Intent Fallback] Gemini 不可用 ({str(e)[:80]}...)，切換為 Regex 降級模式")
        return _parse_with_regex(request)


def _parse_with_regex(request: IntentRequest) -> IntentResponse:
    """
    [Phase 23] 輕量級 Regex 意圖解析器 — Gemini 降級備援
    無需 API 呼叫，0ms 回應。透過關鍵字比對從使用者輸入中擷取意圖。
    """
    text = request.user_input
    
    # 1. 地點比對：先從可用地點清單配對，再嘗試自由擷取地名
    selected_location = None
    if request.available_locations:
        for loc in request.available_locations:
            if loc in text:
                selected_location = loc
                break
    
    # [Phase 24.1] 若清單沒配到，嘗試用 Regex 擷取自由地名
    if not selected_location:
        import re
        # 常見的地點模式：「XX附近」「在XX」「到XX」「去XX」
        location_patterns = [
            r'(?:在|到|去|往|從|離|靠近)\s*([^\s，,。！、]{2,8}(?:站|路|街|市|廟|園|館|場|山|湖|橋|寺|宮|里|區))',
            r'([^\s，,。！、]{2,8}(?:站|路|街|市|廟|園|館|場|山|湖|橋|寺|宮|里|區))\s*(?:附近|旁邊|周邊|一帶|那邊)',
            r'(?:在|到|去|往|從)\s*([^\s，,。！、]{2,6})',
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                selected_location = match.group(1).strip()
                break
    
    # 2. 天氣比對
    selected_weather = None
    weather_keywords = {
        "暴雨": "暴雨", "大雨": "大雨滂沱",
        "雨": "大雨滂沱", "下雨": "大雨滂沱", "避雨": "大雨滂沱",
        "晴": "晴時多雲", "好天氣": "晴時多雲", "出太陽": "晴時多雲",
        "冷": "寒流來襲", "寒": "寒流來襲",
        "涼": "微涼無雨",
    }
    for keyword, weather_val in weather_keywords.items():
        if keyword in text:
            selected_weather = weather_val
            break
    
    # 3. 時間比對
    selected_time = None
    time_keywords = {
        "早餐": "早上", "早上": "早上", "早晨": "早上",
        "午餐": "中午", "中午": "中午",
        "下午茶": "下午", "下午": "下午",
        "晚餐": "傍晚", "晚上": "晚上", "宵夜": "深夜", "夜": "晚上",
    }
    for keyword, time_val in time_keywords.items():
        if keyword in text:
            selected_time = time_val
            break
    
    # 4. 標籤萃取：從系統預設標籤 + 動態關鍵字生成
    selected_tags = []
    tag_rules = {
        "美食小吃": ["吃", "美食", "小吃", "餐", "食"],
        "藝文音樂": ["展覽", "音樂", "藝術", "美術", "博物"],
        "歷史古蹟": ["古蹟", "歷史", "廟", "寺", "老街"],
        "時尚購物": ["購物", "逛街", "百貨", "買"],
        "放鬆休息": ["放鬆", "休息", "公園", "散步", "安靜"],
        "親子同樂": ["親子", "小孩", "兒童", "家庭"],
        "自然探索": ["自然", "登山", "步道", "花", "植物"],
        "室內避雨": ["室內", "避雨", "雨天"],
    }
    
    for tag, keywords in tag_rules.items():
        if any(k in text for k in keywords):
            selected_tags.append(tag)
    
    # 動態 Hash Tags
    dynamic_tags = {
        "咖啡": "#咖啡", "café": "#咖啡", "coffee": "#咖啡",
        "火鍋": "#火鍋", "拉麵": "#拉麵", "牛肉麵": "#牛肉麵",
        "甜點": "#甜點", "蛋糕": "#甜點",
        "早午餐": "#早午餐", "brunch": "#早午餐",
        "素食": "#素食", "蔬食": "#素食",
        "夜景": "#夜景", "酒吧": "#酒吧",
        "義式": "#義式料理", "義大利": "#義大利麵", "披薩": "#披薩",
        "日式": "#日式料理", "壽司": "#壽司",
    }
    for keyword, tag in dynamic_tags.items():
        if keyword in text:
            selected_tags.append(tag)
    
    # 保底：如果什麼都沒匹配到，至少給一個預設標籤
    if not selected_tags:
        selected_tags = ["美食小吃"]
    
    return IntentResponse(
        selected_location=selected_location,
        selected_weather=selected_weather,
        selected_time=selected_time,
        selected_tags=selected_tags[:4]  # 最多 4 個標籤
    )

