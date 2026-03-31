import aiosqlite
import math
from typing import List, Dict, Any, Optional
from src.core.config import get_settings
from src.api.v1.schemas import RecommendationRequest
from src.utils.llm_adapter import get_llm_adapter
from src.db.vector_store import VectorDBRepository

class Retriever:
    """
    語意檢索層 (Semantic Retrieval Layer - Sprint 5)
    負責將意圖轉換為語意向量，從 ChromaDB 進行相似度搜尋。
    """
    def __init__(self):
        settings = get_settings()
        self.db_path = settings.db_path
        self.vector_db = VectorDBRepository()
        self.adapter = get_llm_adapter("gemini")

    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """簡易的 Haversine 公式計算兩點距離 (單位：公里)"""
        R = 6371.0 # 地球半徑 (km)
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(d_lat / 2) ** 2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(d_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    async def get_candidate_pois(self, request: RecommendationRequest, limit: int = 5) -> List[Dict[str, Any]]:
        """
        [Sprint 5 升級] 使用 Embedding 找尋相似 POIs。
        將 Request 的意圖轉成一句自然語言去配對，取代舊有的 SQL IN 查詢。
        """
        # 1. 組裝語意查詢句
        context_parts = []
        weather = getattr(request, 'weather', getattr(request, 'current_weather', None))
        current_time = getattr(request, 'current_time', None)
        
        if weather:
            context_parts.append(f"天氣是{weather}")
        if current_time:
            context_parts.append(f"時間在{current_time}")
            
        # [NEW] 如果有 raw_intent (例如 "想找個地方吃早餐")，直接把它當主詞，更能發揮 ChromaDB 語意搜尋威力
        if getattr(request, 'raw_intent', None):
            base_query = request.raw_intent
        else:
            interests_str = "、".join(request.interests) if request.interests else "好玩的"
            base_query = f"尋找適合 {interests_str} 的景點或活動"
        
        query_text = f"我想{base_query}"
        if context_parts:
            query_text = f"在{'，且'.join(context_parts)}的情況下，{query_text}"
            
        # 2. 獲取 Query Embedding
        try:
            query_embedding = await self.adapter.get_embedding(query_text)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("🚨 系統偵測到 Gemini API Quota 耗盡！降級為 Dummy Vector (純 GPS 檢索模式)！")
                query_embedding = [0.001] * 3072
            else:
                raise e
        
        # [NEW Phase 16] Hybrid Retrieval: 語意檢索結合 Metadata Hard Constraint
        # 以免發生「商業午餐談事情」配對到「商務旅館(Hotel)」的語意污染(Semantic Bleed)
        where_filter = None
        query_checker = (getattr(request, 'raw_intent', "") or "") + "".join(request.interests or [])
        
        target_cats = []
        if any(k in query_checker for k in ["美食", "餐廳", "午餐", "早餐", "晚餐", "吃", "咖啡", "下午茶", "小吃"]):
            target_cats.extend(["food", "Restaurant"])
        if any(k in query_checker for k in ["住宿", "飯店", "商旅", "旅館", "民宿", "旅宿"]):
            target_cats.extend(["hotel", "Hotel"])
        if any(k in query_checker for k in ["活動", "展覽", "音樂", "演出", "室內避雨"]):
            target_cats.extend(["event", "Activity", "spot"])
        if any(k in query_checker for k in ["捷運", "交通", "車站", "火車", "高鐵"]):
            target_cats.extend(["spot"])
            
        # [Phase 32.3] 針對四大 UI 探索標籤與特定關鍵字，加入強力的 Metadata 過濾輔助
        if any(k in query_checker for k in ["親子同樂", "自然探索", "nature", "踏青", "公園", "步道", "登山"]):
            target_cats.extend(["park", "nature", "spot"])
        if any(k in query_checker for k in ["放鬆休息"]):
            target_cats.extend(["food", "cafe", "spot", "park"])
        if any(k in query_checker for k in ["藝文音樂", "故宮", "古蹟", "博館"]):
            target_cats.extend(["spot", "event", "Activity"])
            
        if target_cats:
            # 移除重複的分類
            target_cats = list(set(target_cats))
            if len(target_cats) == 1:
                where_filter = {"category": target_cats[0]}
            else:
                where_filter = {"category": {"$in": target_cats}}
        else:
            # 預設防呆：如果沒明確說要住宿，就把 Hotel 系列過濾掉，避免佔用一般玩樂名額
            where_filter = {"category": {"$nin": ["hotel", "Hotel"]}}
            
        # 3. 從 Chroma 找近似結果
        # [Phase 23 Refactor] Dynamic FETCH_LIMIT：依搜尋半徑動態決定撈取量
        # 目的：從 Phase 21 的暴力 500 筆縮減為精準範圍搜尋，大幅降低記憶體用量
        radius = getattr(request, 'radius_km', None)
        if radius is not None:
            if radius <= 0.5:
                FETCH_LIMIT = 30     # 500m 近身探索 → 30 筆 (~0.4MB)
            elif radius <= 1:
                FETCH_LIMIT = 60     # 1km 散步範圍 → 60 筆 (~0.7MB)
            elif radius <= 2:
                FETCH_LIMIT = 100    # 2km 步行腳踏車 → 100 筆 (~1.2MB)
            else:
                FETCH_LIMIT = 150    # 5km 短程出遊 → 150 筆 (~1.8MB)
        elif request.latitude and request.longitude:
            FETCH_LIMIT = limit * 5  # 有 GPS 但沒指定半徑 → 基本倍數
        else:
            FETCH_LIMIT = limit      # 無 GPS → 最小量
            
        chroma_results = await self.vector_db.query_pois(
            query_embedding=query_embedding, 
            n_results=FETCH_LIMIT,
            where=where_filter
        )
        
        if not chroma_results:
            # 容錯機制：如果 metadata 太嚴格查無結果，放寬限制再查一次
            chroma_results = await self.vector_db.query_pois(
                query_embedding=query_embedding, 
                n_results=FETCH_LIMIT
            )
            
        if not chroma_results:
            return []
            
        # 4. 補回詳細的 SQLite 資料 (如分類、原始經緯度)
        poi_ids = [res['metadata']['poi_id'] for res in chroma_results]
        
        # [NEW LBS FALLBACK MERGE] Phase 21: 取回因 dummy vector 而被埋沒的在地小店
        if request.latitude and request.longitude and getattr(request, 'radius_km', None):
            # 近似換算：緯度 1度約111公里，經度在台灣約 100公里
            lat_offset = request.radius_km / 111.0
            lng_offset = request.radius_km / 100.0
            lat_min, lat_max = request.latitude - lat_offset, request.latitude + lat_offset
            lng_min, lng_max = request.longitude - lng_offset, request.longitude + lng_offset
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cat_clause = ""
                if target_cats:
                    placeholders = ",".join(["?"] * len(target_cats))
                    cat_clause = f"AND category IN ({placeholders})"
                
                query = f"""
                    SELECT id, name, description, tier, lat, lng FROM pois 
                    WHERE lat BETWEEN ? AND ? 
                    AND lng BETWEEN ? AND ?
                    {cat_clause}
                """
                params = [lat_min, lat_max, lng_min, lng_max]
                if target_cats:
                    params.extend(target_cats)
                
                cursor = await db.execute(query, params)
                local_rows = await cursor.fetchall()
                
                # [Phase 32.3] 擴大關鍵字補償，納入自然踏青與藝文指標
                query_keywords = [k for k in ["咖啡", "展覽", "火鍋", "拉麵", "早午餐", "甜點", "小吃", "牛肉麵", "素食", "餐酒館", "居酒屋", "早餐", "踏青", "登山", "步道", "景觀", "公園", "自然", "古蹟", "故宮"] if k in query_checker]
                
                dummy_semantic_map = {}
                for row in local_rows:
                    if row["id"] not in poi_ids:
                        poi_ids.append(row["id"])
                    
                    score = 0.7 # 預設：只符合大分類 (food)，語意普通
                    text_to_check = (row["name"] + " " + (row["description"] or "")).lower()
                    if query_keywords and any(k.lower() in text_to_check for k in query_keywords):
                        score = 0.25 # 關鍵字完全命中，給予極佳語意分數，霸佔在地推薦
                    elif "咖啡" in query_checker and ("cafe" in text_to_check or "coffee" in text_to_check):
                        score = 0.25
                        
                    dummy_semantic_map[row["id"]] = score

        poi_map = {}
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # 由於 SQLite IN tuple 限制，我們分批查詢或一次放進去
            placeholders = ",".join(["?"] * len(poi_ids))
            if poi_ids:
                cursor = await db.execute(f"SELECT * FROM pois WHERE id IN ({placeholders})", poi_ids)
                for row in await cursor.fetchall():
                    poi_map[row["id"]] = dict(row)
                
        # 5. 合併評分，若有 GPS 則用距離微調排序
        # [Phase 32 Refresh] 建立 ID 到語意距離的映射，需防禦舊資料 Metadata 缺漏
        semantic_map = {}
        for res in chroma_results:
            pid = res['metadata'].get('poi_id')
            if pid is None:
                #  fallback: 如果 metadata 沒存，嘗試從 ids 轉回 int
                try: pid = int(res['id'])
                except: continue
            semantic_map[pid] = res['distance']
        
        candidate_pois = []
        for sql_id, poi_info in poi_map.items():
            if sql_id in semantic_map:
                # [Phase 32] 根據 Tier 分級給予不同的排名權重 (Michelin-style Boost)
                # Tier 1: -0.3 (飛機等級), Tier 2: -0.2 (必去等級), Tier 3: -0.1 (在地質感)
                base_dist = semantic_map[sql_id]
                tier = poi_info.get("tier", 3)
                
                if tier == 1:
                    base_dist = max(0.01, base_dist - 0.3)
                elif tier == 2:
                    base_dist = max(0.01, base_dist - 0.2)
                elif tier == 3:
                    base_dist = max(0.01, base_dist - 0.1)
                    
                poi_info['semantic_distance'] = base_dist
            else:
                poi_info['semantic_distance'] = dummy_semantic_map.get(sql_id, 0.7)
            
            # 距離計算
            if request.latitude and request.longitude:
                dist_km = self._calculate_distance(
                    request.latitude, request.longitude, 
                    float(poi_info["lat"]), float(poi_info["lng"])
                )
                
                # 嚴格過濾：若超過使用者指定的半徑，則直接捨棄該候選項
                if getattr(request, 'radius_km', None) is not None and dist_km > request.radius_km:
                    continue
                    
                poi_info["distance_km"] = dist_km
            candidate_pois.append(poi_info)
            
        if request.latitude and request.longitude:
            # 綜合排序：優先看語義，再微調距離
            # [HOTFIX Phase 21] 閾值型距離懲罰 (Threshold Penalty)
            # 0.5公里內的點位視為「同等在地」，不加任何距離懲罰，純粹以語意精準度(Semantic)決出高下。
            # 超過 0.5公里才開始穩步懲罰，這樣既不會被 2km 外的神級名店洗版，也不會因為只看距離而推薦出「不是咖啡廳的牛肉麵」。
            # [Phase 32.4] 降低距離處罰權重 (Semantic Precedence)
            # 將 1km 的距離差距縮減為 0.2 的語意品質損分，讓高品質的「遠方景點」能擊敗普通的「近身景點」。
            candidate_pois.sort(key=lambda x: (x.get('semantic_distance', 0) * 1.0) + (max(0, x.get("distance_km", 0) - 0.5) * 0.2))
            
        return candidate_pois[:limit]

    async def get_positive_trends_for_pois(self, poi_ids: List[int], limit_per_poi: int = 3) -> Dict[int, List[Dict[str, Any]]]:
        """
        [Sprint 5 升級] 同樣透過 ChromaDB 的 Similarity Search 或直接回原 DB 撈 (維持原有)
        因為賽題強調語意檢索，可以利用 ChromaDB 來直接篩選 sentiment
        在這裡我們維持 SQL 邏輯以便快取，或可寫入 chroma 時加標籤。
        為了展示平滑過渡，保留使用 SQL 取 Trends。
        """
        if not poi_ids:
            return {}

        trends_map = {poi_id: [] for poi_id in poi_ids}
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            placeholders = ",".join(["?"] * len(poi_ids))
            
            query = f"""
                SELECT poi_id, content, sentiment, platform 
                FROM social_trends 
                WHERE poi_id IN ({placeholders}) AND sentiment IN ('positive', 'neutral')
                ORDER BY created_at DESC
            """
            cursor = await db.execute(query, poi_ids)
            rows = await cursor.fetchall()
            
            for row in rows:
                poi_id = row["poi_id"]
                if len(trends_map[poi_id]) < limit_per_poi:
                    trends_map[poi_id].append(dict(row))
                    
        return trends_map
