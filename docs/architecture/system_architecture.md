# 系統架構圖 (System Architecture)

本圖具象化了「臺北時光機」在 **Phase 33 準備階段** 的完整架構。系統採用了現代化的 **Hybrid RAG (混合檢索增強生成)** 架構，並結合前端 **Agentic UI (代理化介面)** 體驗。

```mermaid
graph TD
    %% 定義 Client 區塊
    subgraph Client ["Client 端 (Browser / Mobile)"]
        UI["使用者介面<br/>(HTML / Tailwind CSS)"]
        Voice["Web Speech API<br/>(語音輸入)"]
        JS["互動邏輯<br/>(Vanilla JS / Fetch API)"]
        
        UI <--> JS
        Voice --> JS
    end

    %% 定義 API Server 區塊
    subgraph Server ["FastAPI Server (Python)"]
        API_Gateway["API 路由層 (Routers)<br/><code>/metadata</code>, <code>/parse-intent</code>, <code>/fast-recommend</code>"]
        
        subgraph Core ["核心業務邏輯 (Core)"]
            Retriever["混合檢索層 (Hybrid Retriever)<br/>語意檢索 + 距離處罰 + Tier 分級加權"]
            RecEngine["推薦引擎 (Recommendation Engine)<br/>Prompt 組裝與回覆生成"]
        end
        
        Adapter["LLM Adapter 轉接器<br/>(封裝 google-genai SDK)"]
        StaticFiles["Static Files & Jinja2 Templates<br/>src/static/ & src/templates/"]
        
        API_Gateway --> Retriever
        API_Gateway --> RecEngine
        Retriever --> Adapter
        RecEngine --> Adapter
    end

    %% 運維與服務管理
    subgraph Ops ["服務生命週期管理 (Ops)"]
        Lifecycle["啟動/關閉腳本<br/>(start_server.sh / stop_server.sh)"]
        Lifecycle -.-> |"防止 ChromaDB 檔案鎖定衝突"| Server
    end

    %% 定義外部 AI 服務
    subgraph External_AI ["外部 AI 服務 (Google Gemini)"]
        Gemini_Flash["Gemini-3.1-Flash-Lite<br/>(意圖解析 / 推薦生成)"]
        Gemini_Embed["Gemini Embedding 001<br/>(文本特徵向量化)"]
    end

    %% 定義資料庫區塊
    subgraph Databases ["資料儲存層"]
        SQLite[("SQLite 關聯資料庫<br/>(景點 Meta、Tier 星級、社群貼文)")]
        Chroma[("ChromaDB 向量資料庫<br/>(PersistentClient)")]
    end

    %% 連線設定
    JS <--> |"REST API (JSON)"| API_Gateway
    
    Retriever <--> |"Metadata / 地理過濾"| SQLite
    Retriever <--> |"Cosine Similarity"| Chroma
    
    Adapter <--> |"API Call"| Gemini_Flash
    Adapter <--> |"API Call"| Gemini_Embed

    %% 樣式設定
    classDef clientStyle fill:#e0f7fa,stroke:#00acc1,stroke-width:2px;
    classDef serverStyle fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px;
    classDef dbStyle fill:#fff3e0,stroke:#fb8c00,stroke-width:2px;
    classDef aiStyle fill:#e8f5e9,stroke:#4caf50,stroke-width:2px;
    classDef opsStyle fill:#ffebee,stroke:#e53935,stroke-width:2px,stroke-dasharray: 5 5;

    class UI,Voice,JS clientStyle;
    class API_Gateway,Retriever,RecEngine,Adapter serverStyle;
    class SQLite,Chroma dbStyle;
    class Gemini_Flash,Gemini_Embed aiStyle;
    class Lifecycle opsStyle;
```

## 架構設計亮點說明
1. **Frontend**: 零建置工具 (Zero-build) 架構，僅依靠瀏覽器原生的 Web Speech API 與 Fetch API 即可完成極高互動性的 Agentic 體驗。
2. **LLM Adapter**: 透過轉接器模式隔離了外部 SDK 的變動風險（例如我們在開發過程中無縫克服了 Free Tier Quota 的問題與新舊 SDK 的過渡）。
3. **Dual-Database 策略**: 
   - **ChromaDB**: 負責處理人類模糊、自然語言的「語意比對」(例如："想找個安靜的地方避雨")。
   - **SQLite**: 負責儲存結構化的實體關聯資料 (如精確的經緯度、分類標籤、店家實際介紹等)。
   - **Retriever (檢索層)** 會將兩者完美 Join，提供給 LLM 最豐沛的 Context。
