# 專案全局上下文 (Project Context)

> **給 AI 智能體的提示**：每次啟動新對話或執行新任務時，請優先讀取此檔案以同步專案狀態。

## 1. 專案目標與背景 (YTP 黑客松競賽)
* **專案目標**：開發「即時社群內容推播服務」，透過 AI 情境感知與推薦演算法，將原本散落於社群平台（PTT、Dcard、IG、Threads 等）的碎片化旅遊資訊，轉化為主動式、個人化且動態調整的智慧觀光體驗，協助自由行與年輕旅客進行深度探索，並帶動臺北夜間經濟與商圈發展。
* **施政痛點解決**：改善傳統網站靜態列表與自行跨平台搜尋的負擔，解決旅遊決策資訊破碎、在地小店能見度不均的問題。
* **目標客群**：喜好深度探索的自由行與年輕族群、臨時決定行程的國內外遊客，以及關注夜間活動/展演/市集/商圈的龐大消費客群。
* **預期效益**：提升旅遊滿意度與便利性、延長旅客停留時間、帶動夜市與巷弄商圈經濟轉換，並強化臺北智慧觀光品牌形象。
* **目前階段**：Beta Release (Phase 35)。已完成整合測試並正式向 QA Team 提交 `BETA_VERIFICATION_HANDOFF.md` 手冊。系統目前具備穩定且經過驗證的 YouBike 2.0 即時資料層、OSM 動態圖資退路機制以及 Agentic UI 聯動功能。全系統正式進入「Verification & Validation」驗證期，準備進行最後的壓力與邊界測試。

## 2. 技術棧 (Tech Stack)
* **應用類型**：Web Application (Mobile-First)
* **前端 (Frontend)**：
  * **主體**：HTML / CSS / Vanilla JavaScript (Server-Side 搭配 FastAPI Jinja2 模板引擎 `src/templates/` 進行初步渲染，靜態檔案透過 `src/static/` 提供)
  * **樣式**：Tailwind CSS (透過 CDN 引入，極簡開發)
  * **API 與互動**：Fetch API (非同步呼叫)、Web Speech API (語音辨識/聲控輸入)
* **後端 (Backend)**：Python / FastAPI (確保高效能的非同步 API 處理)
* **資料庫 (Database)**：
  * **核心關聯資料庫**：SQLite (透過 `aiosqlite` 非同步存取)，儲存景點 Meta、社群貼文與使用者設定。
  * **語意向量庫 (Sprint 5 升級)**：ChromaDB (`PersistentClient`)，儲存景點文本特徵，實現 RAG (Retrieval-Augmented Generation) 語意檢索。
* **AI 與核心技術 (零成本開發策略)**：
  * **核心應用**：NLP 語意分析 (意圖萃取)、語意向量檢索搜尋 (Semantic Search)、客製化景點推薦演算法。
  * **LLM 架構設計**：系統底層採用 **Adapter Pattern (轉接器模式)** 實作 (`src/utils/llm_adapter.py`)。
  * **使用的模型**：全面優先使用強大的 **Google Gemini API** (透過全新 `google-genai` SDK)。利用 `gemini-3.1-flash-lite-preview` 進行意圖解析與推薦生成，利用 `gemini-embedding-001` 進行文本向量化 (Embeddings)。
  * **未來擴充考量**：將 LLM 呼叫邏輯完全抽象化並封裝於獨立 Service，保留未來無縫切換或擴充至 Anthropic Claude API 或其他大型語言模型的彈性（初期實作不直接引入付費第三方 SDK）。

## 3. AI 協作最高指導原則
1. **先查閱再行動**：修改重大邏輯前，必須先閱讀 `docs/adr/` 中的架構決策紀錄。
2. **測試驅動**：任何 `src/` 內的程式碼變更，都必須同步更新或新增 `tests/` 內的測試案例。
3. **保持原子性**：提交變更或修改檔案時，請保持微型任務的原則，不要一次大規模重寫。

## 4. 團隊規範與結構約定 (Team Conventions)

> ⚠️ **跨模型強制規則**：以下規則適用於所有 AI 模型（Gemini、Claude、GPT 等），任何模型進入本專案時必須遵守，不得依照自身預設行為覆蓋。

### 4.1 目錄結構約定
* **AI 技能 (Skills)**：一律存放在 `.agents/skills/{skill-name}/SKILL.md`。**禁止**另建 `.cursor/`、`.claude/`、`.copilot/` 等替代路徑。
* **工作流 (Workflows)**：一律存放在 `.agents/workflows/{name}.md`。
* **文件目錄結構**：
  - `docs/context/` — 外部參考文件（競賽指引、規格書、協作指南）
  - `docs/journeys/` — AI 協同開發日誌（每個 Phase 一份 `.md`，命名格式：`NN_phaseN_描述.md`）
  - `docs/adr/` — Architecture Decision Records（命名格式：`ADR-NNN-標題.md`）

### 4.2 開發日誌義務
* 每完成一個重要 Phase 或里程碑，**必須**在 `docs/journeys/` 中產出一份開發紀錄，記錄：核心決策、踩過的坑、選用的技術方案。
* 此日誌是團隊間「AI 記憶傳遞」的核心載體。

### 4.3 接手專案時的標準流程
* 新對話啟動後，除了讀取本檔案，**還必須**讀取 `docs/journeys/` 中的所有日誌以同步前序開發脈絡。
* 可使用 `/handoff` 工作流自動完成此流程。

### 4.4 Git Commit 訊息規範
請嚴格遵循 [GIT_COMMIT_GUIDE.md](docs/context/GIT_COMMIT_GUIDE.md) 所記載之規範，主要依據 Conventional Commits 並針對 AI 世代優化：
* 結構性調整：`docs:` 或 `chore:` prefix
* 功能實作：`feat:` prefix
* 修復：`fix:` prefix
* 重構：`refactor:` prefix
* **AI 技能固化**：`skill:` prefix
