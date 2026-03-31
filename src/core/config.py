from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    """
    全域設定檔 (Global Configuration)
    以 Pydantic BaseSettings 定義，自動從環境變數或 .env 檔案載入並驗證型別。
    """
    
    # Application Settings
    ENVIRONMENT: str = Field(default="development", description="系統執行環境")
    HOST: str = Field(default="0.0.0.0", description="API Server 綁定 IP")
    PORT: int = Field(default=8000, description="API Server 監聽埠號")
    
    # Database Settings
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./test.db", 
        description="非同步 SQLite 資料庫連線字串"
    )
    
    # AI Service Settings
    GEMINI_API_KEY: str = Field(
        ..., # ... 代表必填項
        description="Google Gemini API Key，必須於 .env 或環境變數中提供"
    )
    
    # 擴充金鑰陣列 (支援 Quota 耗盡時自動輪換)
    GEMINI_API_KEY_1: str | None = Field(default=None, description="Google Gemini API Key 1")
    GEMINI_API_KEY_2: str | None = Field(default=None, description="Google Gemini API Key 2")
    GEMINI_API_KEY_3: str | None = Field(default=None, description="Google Gemini API Key 3")
    GEMINI_API_KEY_4: str | None = Field(default=None, description="Google Gemini API Key 4")
    GEMINI_API_KEY_5: str | None = Field(default=None, description="Google Gemini API Key 5")
    GEMINI_API_KEY_6: str | None = Field(default=None, description="Google Gemini API Key 6")
    GEMINI_API_KEY_7: str | None = Field(default=None, description="Google Gemini API Key 7")

    # 保留未來擴充使用
    ANTHROPIC_API_KEY: str | None = Field(
        default=None, 
        description="Anthropic Claude API Key (預留)"
    )

    @property
    def gemini_api_keys(self) -> list[str]:
        """聚合所有有效的 Gemini API Key，去除空值與重複項，預設將主 Key 放第一"""
        keys = [self.GEMINI_API_KEY]
        key_list = [
            self.GEMINI_API_KEY_1, self.GEMINI_API_KEY_2, self.GEMINI_API_KEY_3,
            self.GEMINI_API_KEY_4, self.GEMINI_API_KEY_5, self.GEMINI_API_KEY_6,
            self.GEMINI_API_KEY_7
        ]
        for k in key_list:
            if k and str(k).strip() and k not in keys:
                keys.append(k)
        return keys

    @property
    def db_path(self) -> str:
        """將 SQLAlchemy 格式的 DATABASE_URL 轉換為 aiosqlite 原生路徑"""
        if self.DATABASE_URL.startswith("sqlite+aiosqlite:///"):
            return self.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        return "./test.db"

    # pydantic-settings > 2.0 寫法：設定抓取來源為 .env 與字元編碼
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # 忽略 .env 中未定義於 Settings 的多餘變數
    )

@lru_cache()
def get_settings() -> Settings:
    """
    建立並回傳 Settings 單例 (Singleton)，
    利用 lru_cache 確保只在第一次呼叫時讀取與解析環境變數。
    """
    return Settings()
