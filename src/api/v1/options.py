import json
import os

from fastapi import APIRouter, Depends
from src.api.v1.schemas import LocationOption, MetadataResponse
from src.db.repository import DatabaseRepository

router = APIRouter(
    prefix="/metadata",
    tags=["Metadata"],
)

def get_db_repo() -> DatabaseRepository:
    return DatabaseRepository()

@router.get("/", response_model=MetadataResponse)
async def get_metadata(repo: DatabaseRepository = Depends(get_db_repo)):
    """
    提供前端動態選項所需的 Metadata。
    包含：
    1. 所有可用的景點類別 
    2. 隨機抽選 5 個景點作為位置選項 (locations) 作為 Fallback
    3. 載入大台北 131+ 捷運站靜態字典，解決 LLM 猜測座標失準問題 (Phase 14)
    """
    semantic_tags = [
        "美食小吃", "藝文音樂", "歷史古蹟", "時尚購物", 
        "放鬆休息", "親子同樂", "自然探索", "室內避雨"
    ]
    
    # 原始的隨機地點
    locations_raw = await repo.get_sample_locations(limit=5)
    locations = [
        LocationOption(
            id=loc["id"], 
            name=loc["name"], 
            lat=loc["lat"], 
            lng=loc["lng"]
        ) for loc in locations_raw
    ]
    
    # [Phase 14 擴充] 載入 MRT 實體地點字典
    dict_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "location_dictionary.json")
    if os.path.exists(dict_path):
        with open(dict_path, "r", encoding="utf-8") as f:
            mrt_dict = json.load(f)
            # 建立固定的假 ID 以防衝突
            mock_id = 9000
            for name, coords in mrt_dict.items():
                locations.append(LocationOption(
                    id=mock_id,
                    name=name,
                    lat=coords["lat"],
                    lng=coords["lng"]
                ))
                mock_id += 1
                
    return MetadataResponse(categories=semantic_tags, locations=locations)
