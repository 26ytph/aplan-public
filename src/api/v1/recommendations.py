from fastapi import APIRouter, Depends, HTTPException, status
from src.utils.llm_adapter import LLMAdapter, get_llm_adapter
from src.api.v1.schemas import RecommendationRequest, RecommendationResponse
from src.core.retriever import Retriever
from src.core.recommendation_engine import RecommendationEngine

# 建立推薦系統專用的 Router
router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)

# === Dependencies ===

def get_llm_client() -> LLMAdapter:
    """FastAPI Dependency: 注入 LLM Adapter"""
    return get_llm_adapter(model_type="gemini")

def get_retriever() -> Retriever:
    """FastAPI Dependency: 注入資料檢索層"""
    return Retriever()

def get_engine(llm: LLMAdapter = Depends(get_llm_client)) -> RecommendationEngine:
    """FastAPI Dependency: 注入推薦大腦"""
    return RecommendationEngine(llm_adapter=llm)

# === Endpoints ===

@router.post("/", response_model=RecommendationResponse)
async def create_recommendation(
    request: RecommendationRequest,
    retriever: Retriever = Depends(get_retriever),
    engine: RecommendationEngine = Depends(get_engine)
):
    """
    產生即時客製化推薦行程 (Sprint 3 核心)
    1. 檢索出符合興趣且距離最近的候選 POIs。
    2. 針對這些 POIs 檢索近期的社群正向貼文。
    3. 丟給 LLM 進行情境推論與格式化輸出。
    """
    try:
        # Step 1: 檢索候選景點 (最多取 5 個)
        candidate_pois = await retriever.get_candidate_pois(request, limit=5)
        if not candidate_pois:
            raise HTTPException(status_code=404, detail="找不到符合條件的景點")
            
        # Step 2: 檢索這些景點的相關社群貼文
        poi_ids = [poi["id"] for poi in candidate_pois]
        social_trends = await retriever.get_positive_trends_for_pois(poi_ids, limit_per_poi=3)
        
        # Step 3: 交給 AI 大腦進行運算
        response = await engine.generate_smart_itinerary(
            request=request, 
            candidate_pois=candidate_pois, 
            social_trends=social_trends
        )
        
        return response
        
    except ValueError as ve:
        # LLM 解析錯誤
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"AI 生成格式錯誤: {str(ve)}"
        )
    except Exception as e:
        # 其他未預期錯誤
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"推薦引擎發生錯誤: {str(e)}"
        )
