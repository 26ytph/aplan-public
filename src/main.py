from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.core.config import get_settings

# 獲取全域設定
settings = get_settings()

def create_app() -> FastAPI:
    """
    FastAPI 應用程式依賴注入工廠模式
    """
    app = FastAPI(
        title="臺北時光機 (即時社群內容推播服務)",
        description="2026 YTP 黑客松專案 A - 核心後端 API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 設定 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # 開發階段暫時開放所有來源，上線前須限縮
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from src.api.v1 import recommendations, options, intent, context, fast_recommend
    
    # 註冊 v1 API 路由 (APIRouter)
    app.include_router(recommendations.router, prefix="/api/v1")
    app.include_router(options.router, prefix="/api/v1")
    app.include_router(intent.router, prefix="/api/v1")
    app.include_router(context.router, prefix="/api/v1")
    app.include_router(fast_recommend.router, prefix="/api/v1")

    from fastapi import Request
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates

    # 掛載靜態檔案目錄 (用於 CSS/JS)
    app.mount("/static", StaticFiles(directory="src/static"), name="static")

    # 設定 Jinja2 樣板目錄
    templates = Jinja2Templates(directory="src/templates")

    @app.get("/", tags=["Frontend"])
    async def serve_frontend(request: Request):
        """渲染並回傳首頁"""
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "app_name": "臺北時光機 (即時社群內容推播服務)"}
        )

    return app

app = create_app()

if __name__ == "__main__":
    # 若直接以 python 執行此檔案，則啟動 uvicorn (僅供開發測試)
    uvicorn.run(
        "src.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=True if settings.ENVIRONMENT == "development" else False
    )
