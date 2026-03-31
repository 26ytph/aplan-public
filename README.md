# 🕰️ 臺北時光機 (Taipei Time Machine)
**— 2026 YTP 黑客松 競賽專案 —**

> **「拋開死板的下拉選單，用最自然的一句話，帶你穿梭臺北的日與夜。」**

**臺北時光機** 是一個結合了「**即時情境感知 (Context-Aware)**」、「**語音意圖解析 (Intent Parsing)**」與「**多維度語意檢索 (Semantic RAG)**」的新世代旅遊推薦 Web 應用。我們將散落的開放資料重新解構，為喜歡自由彈性探索的旅客，提供最客製化、隨心所欲的智慧導覽體驗。

---

## 🏆 給評審的技術亮點 (Technical Architecture Highlights)

本專案完全由團隊與 AI 共同協力 (AI-Native) 打造，歷經 8 個 Sprint 的架構迭代，具備以下企業級 (Enterprise-grade) 亮點：

### 1. 🎯 Semantic UX 與動態語意意圖解析 (Intent Parsing)
拋棄傳統死板的資料庫 `Category` (如 spot, hotel) 下拉選單。
我們實作了**語意化探索標籤** (如 `☔ 室內避雨`, `🍜 美食小吃`, `🌳 自然探索`)。當使用者用語音輸入「外面下雨想躲雨找小吃」，系統底層的 LLM Adapter 會透過 **Pydantic Schema 強制約束** 解析意圖，精準點亮對應標籤，達成極致的 UX 體驗。

### 2. 🌍 即時情境聯動介面 (Context-Aware UI)
前端實裝了 **HTML5 原生 Geolocation API** 以獲取精準裝置座標，並搭載動態計算的 **24 小時時間輪盤**。
系統內部建立 `WeatherService` 靜默監聽經緯度與時間的變動，非同步呼叫 `Open-Meteo` 開源氣象模型 (具備無縫無痛熱切換 CWA 的能力)，瞬間根據時空背景切換 UI 的天氣圖示與溫度，讓大腦擁有最清晰的環境脈絡。

### 3. ⚡ 超低延遲多維度檢索與向量庫 (ChromaDB + SQLite)
我們以非同步架構爬取了 **Taipei Open Data** 與 **交通部 TDX**，經資料清洗後，透過 **Google Gemini Text Embedding API (768維度)** 賦予語意。
目前收錄高達 **2,367 筆** 菁英地標 (涵蓋大台北米其林餐廳、國家級自然景點、頂級百貨與 119 座捷運站週邊)。檢索時融合了：
1. **ChromaDB** 語意相似度檢索。
2. **SQLite** 關聯查詢與 **Tier 分級權重 (Michelin-style)** 星級加分。
3. **Haversine** 空間地理距離演算法，結合最新的懲罰公式 (`語意 * 1.0 + 距離處罰 * 0.2`)，並支援前台客製化搜尋半徑過濾。
**端到端檢索 (End-to-End Retrieval) 透過 `/fast-recommend` 服時僅約 0.5 秒！**

### 4. 🗺️ 動態地圖退路機制 (Dynamic Geographic Fallback)
針對優質但無官方照片的在地小吃或活動，我們解除了傳統的「無圖拋棄」限制。
開發了 `Dynamic Map Generation` 機制：依據 POI 的 `Lat/Lng`，系統會自動呼叫 **OpenStreetMap (OSM) 嵌入式動態地圖** 服務。配上專屬的高對比度深色濾鏡與空間座標標記，不僅確保了「有圖有真相」的資訊底線，還能讓使用者直接在卡片上滑動與縮放地圖！

### 5. 🚲 即時微交通情境層 (Real-time Micro-Mobility Layer)
超越傳統「景點推薦」的極限，我們解決了「如何前往」的痛點。
透過介接臺北市政府開放資料平台的 **YouBike 2.0 Azure Blob 動態即時端點**，系統會在 LLM 鎖定推薦景點後，利用 Haversine 演算法與 **60秒記憶體快取 (TTL Cache)** 機制，瞬間為使用者抓出「距離使用者最近且有車可借」以及「距離目的地最近且有位可還」的 YouBike 站點，優雅地以動態 UI 注入在推薦卡片底部。

---

## 🚀 快速上手 (Quick Start)

### 1. 系統環境需求
* **Python**: `3.10+`
* **API Key**: 取得一組免費的 [Google AI Studio (Gemini)](https://aistudio.google.com/app/apikey) API Key。

### 2. 安裝與資料注入
```bash
# 1. 複製專案並安裝依賴套件
git clone https://github.com/26ytph/aplan.git
cd aplan
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. 環境變數設定 (請開啟 .env 並填入您的 GEMINI_API_KEY)
cp .env.example .env

# 3. 執行 3 階段 ETL 注入腳本以建立 SQLite & ChromaDB 向量庫 (保護 API Rate Limit)
PYTHONPATH=. python3 src/data_pipeline/fetch_to_cache.py      # Stage 1: 抓取快取至本地
PYTHONPATH=. python3 src/data_pipeline/load_to_sqlite.py      # Stage 2: 載入關聯資料庫
PYTHONPATH=. python3 src/data_pipeline/embed_incremental.py   # Stage 3: 多金鑰池 (Multi-Key) 增量特徵向量化

# 4. 啟動 FastAPI 伺服器 (包含防死鎖保護機制)
./scripts/start_server.sh
# 停止伺服器時請務必使用 ./scripts/stop_server.sh 釋放 ChromaDB 檔案鎖定
```

開啟瀏覽器前往：`http://127.0.0.1:8000` ，盡情探索！

---

## 📚 深入專案文件 (Documentation)

為了保持主專案程式碼的純淨，所有詳盡的設計決策以及 AI 協同開發軌跡，皆已收納保管至專屬文件中：

| 分類 | 文件 | 說明 |
|------|------|------|
| 📜 專案背景 | [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | 專案全局技術上下文 |
| 📐 架構設計 | [system_architecture.md](docs/architecture/system_architecture.md) | 系統架構圖 (Mermaid) 與模組切分 |
| 🚀 實作軌跡 | [docs/journeys/](docs/journeys/) | 從 Phase 1 到 最新 Beta 發布的完整開發演進日誌 |
| 📝 測試策略 | [test_strategy.md](docs/testing/test_strategy.md) | 零腳本自動化前端體驗測試計畫 |
| 🤝 協作指南 | [AI_PRODUCTIVITY_HANDBOOK.md](docs/context/AI_PRODUCTIVITY_HANDBOOK.md) | AI 生產力、自動化技能與協作指引 |
| 🧪 QA 交付 | [BETA_VERIFICATION_HANDOFF.md](docs/testing/BETA_VERIFICATION_HANDOFF.md) | 交付 QA Team 的 Verification & Validation 指南 |

---
*Powered by Team Antigravity. Built for the 2026 YTP Hackathon.*
