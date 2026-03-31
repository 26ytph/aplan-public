import json
from typing import List, Dict, Any
from src.utils.llm_adapter import LLMAdapter
from src.api.v1.schemas import RecommendationRequest, RecommendationResponse, RecommendedPOI

class RecommendationEngine:
    """
    AI 核心推薦大腦 (Recommendation Engine)
    將檢索出的資料與使用者情境組裝，交由 LLM 進行分析與生成。
    """
    def __init__(self, llm_adapter: LLMAdapter):
        self.llm = llm_adapter

    async def generate_smart_itinerary(
        self, 
        request: RecommendationRequest, 
        candidate_pois: List[Dict[str, Any]], 
        social_trends: Dict[int, List[Dict[str, Any]]]
    ) -> RecommendationResponse:
        """
        核心演算法：根據情境與候選資料，呼叫 LLM 產出符合 Pydantic 模型格式的建議。
        """
        # 1. 準備提供給 LLM 的上下文 (Context)
        context_pois = []
        for poi in candidate_pois:
            poi_id = poi["id"]
            trends = social_trends.get(poi_id, [])
            trend_texts = [f"[{t['platform']}] {t['content']}" for t in trends]
            
            context_pois.append({
                "poi_id": poi_id,
                "name": poi["name"],
                "category": poi["category"],
                "description": poi["description"],
                "recent_social_trends": trend_texts
            })
            
        # 轉換為 JSON 字串放入 Prompt
        context_pois_str = json.dumps(context_pois, ensure_ascii=False, indent=2)
        
        # 2. 構建 System Prompt (強制 JSON 格式回傳)
        # [Phase 26] 多語系：根據前端語系動態注入翻譯指令
        LANG_NAMES = {"ja": "日文", "ko": "韓文", "en": "英文", "th": "泰文"}
        lang_instruction = ""
        if request.lang and request.lang != "zh-TW" and request.lang in LANG_NAMES:
            target = LANG_NAMES[request.lang]
            lang_instruction = f"""
        5. 【多語系翻譯指令】你必須用 **{target}** 撰寫 `itinerary_summary` 和所有 `reason` 欄位。
           景點名稱 `name` 請保留中文原名並附上{target}翻譯，格式為「原名 / 翻譯名」。
           地址 `address` 保持中文原文不翻譯。"""
        
        prompt = f"""
        你是一位臺北市的頂級旅遊體驗設計師。請根據以下使用者的當下情境與候選景點，設計一份客製化行程建議。
        
        【使用者情境】
        - 興趣標籤：{", ".join(request.interests) if request.interests else "探索臺北"}
        - 預計旅遊時間：{request.current_time or "未指定"}
        - 氣象資訊：{request.weather or "未指定"}
        
        【候選景點資料庫】 (包含景點基本資訊與近期的正向社群評論)
        {context_pois_str}
        
        【任務規則】
        1. 請從候選景點中挑選 2 到 3 個最符合情境的景點。注意：清單已由在地化引擎嚴格排序，請「優先挑選」排在最前面的選項 (序號越前越優先)。若使用者有提到「國際級」、「頂級」、「百貨」等字眼，請務必挑出相符的知名指標型地點，勿推薦一般小店或平價商旅。
        2. 為挑選出的每個景點撰寫 `reason` (推薦理由)。理由必須揉合「社群評論中的亮點」與「使用者的情境(如天氣/時間)」，口吻需親切、活潑，就像 Dcard 上的達人推薦，約 30-50 字。
        3. 撰寫一份 `itinerary_summary` (行程總結)，說明為何如此安排，約 50 字內。
        4. 所有欄位預設以繁體中文撰寫，除非下方有多語系翻譯指令。{lang_instruction}
        
        【JSON 輸出約束】
        你的回覆**必須只能**是一個合法的 JSON Object，不要加上 ```json 標籤，也不要有任何其他 markdown 或文字。
        JSON 的結構必須完全符合以下格式：
        {{
            "itinerary_summary": "字串內容",
            "recommended_pois": [
                {{
                    "poi_id": 數字,
                    "name": "景點名稱",
                    "reason": "推薦理由"
                }}
            ]
        }}
        """

        # 3. 呼叫 LLM
        try:
            # 必須傳入 response_schema 才能觸發 Gemini 的結構化輸出，以及在 Quota 不足時觸發正確的 Mock JSON
            raw_response = await self.llm.generate_content(prompt, response_schema=RecommendationResponse)
            # 清理可能不小心生成的 \n 或 markdown block
            clean_json_str = raw_response.strip().removeprefix("```json").removesuffix("```").strip()
            
            # 解析並映射回 Pydantic 結構
            response_dict = json.loads(clean_json_str)
            
            # 將經緯度與額外詳細資訊補回去 (因為 LLM 不用生成這些，以節省 Token)
            poi_map = {poi["id"]: poi for poi in candidate_pois}
            for rec_poi in response_dict.get("recommended_pois", []):
                original_poi = poi_map.get(rec_poi["poi_id"])
                if original_poi:
                    rec_poi["lat"] = original_poi.get("lat")
                    rec_poi["lng"] = original_poi.get("lng")
                    rec_poi["address"] = original_poi.get("address", "")
                    rec_poi["image_url"] = original_poi.get("image_url", "")
                    
            return RecommendationResponse(**response_dict)
            
        except Exception as e:
            # 容錯處理：若 LLM 全面崩潰或 API 額度耗盡，啟動強健的降級機制 (Graceful Degradation)
            # 既然 ChromaDB 已經算出最符合的 5 個 POI，我們就直接把它們組裝成假的回傳格式，硬上！
            print(f"🚨 推薦引擎 LLM 發生崩潰 ({str(e)})，切換為「離線 GPS 推薦模式」確保畫面正常！")
            
            fallback_pois = []
            poi_map = {poi["id"]: poi for poi in candidate_pois}
            
            # 取出前 3 個作為預設推薦
            for poi in candidate_pois[:3]:
                # 組裝最低限度的推薦理由
                cat = poi.get("category", "熱門地點")
                trends = social_trends.get(poi["id"], [])
                social_hint = f"網路上有 {len(trends)} 篇熱烈討論！" if trends else "在地人私藏的隱藏打卡點！"
                
                fallback_pois.append({
                    "poi_id": poi["id"],
                    "name": poi["name"],
                    "reason": f"【離線推薦】這是一間距離您最近的{cat}，{social_hint}",
                    "lat": poi.get("lat"),
                    "lng": poi.get("lng"),
                    "address": poi.get("address", ""),
                    "image_url": poi.get("image_url", "")
                })
            
            return RecommendationResponse(
                itinerary_summary="【系統提示：AI 額度已耗盡，啟動離線 GPS 推薦模式】這是為您從資料庫中強制比對出最接近目標，且符合您選擇特徵的附近精選地標！",
                recommended_pois=fallback_pois
            )
