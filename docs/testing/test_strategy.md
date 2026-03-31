# 臺北時光機 (Taipei Time Machine) - 智能體自動化測試計畫 (Agentic E2E Testing Plan)

## 1. 測試理念與目標 (Philosophy & Goals)
本專案導入前沿的 **Agentic E2E Testing (智能體端到端自動化測試)** 流程。捨棄傳統撰寫繁瑣且易碎的 UI 定位腳本 (如 Cypress、Selenium)，改由 Antigravity Browser Subagent 透過自然語言指令 (Natural Language Prompt)，結合大語言模型視覺與 DOM 樹解析能力，直接模擬真實使用者的操作行為。

**目標：**
1. 確保核心功能 (如：UI 渲染、Agentic UI 動態連動、意圖解析、推薦結果) 在改版變更後維持穩定。
2. 實現「說話即測試」的零腳本 (Zero-script) 測試體驗。
3. 自動產出直觀的測試報告與操作錄影，作為後續維護與交接的標準檢驗依據。

---

## 2. 標準測試提交流程 (Testing Workflow)

測試流程分為以下四個標準階段：

### Phase 1: 規劃與劇本定義 (Plan)
由開發團隊或 PM 以自然語言定義測試劇本 (Test Scenario)。劇本只需用白話文描述「情境」、「輸入」與「預期輸出」。
*   *範例場景*：「傳統手動點選路徑測試」、「用語音/文字輸入複雜情境測試」。

### Phase 2: 自動化執行 (Execute)
指示 Antigravity 啟動 `Browser Subagent` 工具，帶入 Phase 1 的劇本。
*   Subagent 會自動在背景開啟 Chrome (Headless 或 UI 模式)。
*   動態尋找 DOM 節點 (輸入框、按鈕、下拉選單)。
*   模擬鍵盤敲擊與滑鼠點擊。

### Phase 3: 驗證與報告產出 (Report)
Subagent 完成所有步驟後，會蒐集以下資訊作為「測試憑證」：
1.  **最終狀態截圖 (Screenshot)**：證明 UI 畫面成功渲染。
2.  **互動過程錄影 (WebM / WebP Recording)**：記錄滑鼠軌跡與動態變化。
3.  **文字報告 (Observation Report)**：由 Subagent 撰寫的執行觀察，包含何處符合預期、何處遇到 UI 限制。

### Phase 4: 分類歸檔 (Archive)
為保持專案鷹架 (Scaffolding) 整潔，測試憑證與報告須移出暫存區，歸檔至專屬目錄。

---

## 3. 測試目錄歸檔結構 (Archive Structure)

我們將在專案根目錄下建立 `tests/e2e_reports/` 資料夾，以**測試劇本類型**作為子目錄，集中保管歷次的測試產出：

```text
APlan/
├── src/
├── docs/
└── tests/
    ├── unit/                           # (未來擴充: Python 後端單元測試)
    └── e2e_reports/                    # [新增] Agentic E2E 測試報告總管
        ├── manual_ui_flow/             # 傳統手動點選路徑測試紀錄
        │   ├── test_{scenario}_report_{date}.md      # 測試紀錄文字報告
        │   ├── test_{scenario}_recording_{date}.webp # 操作錄影
        │   └── test_{scenario}_result_{date}.png     # 最終推薦截圖
        │
        ├── ai_intent_flow/             # AI 語意解析路徑測試紀錄
        │   ├── test_{scenario}_report_{date}.md
        │   ├── test_{scenario}_recording_{date}.webp
        │   └── test_{scenario}_result_{date}.png
        │
        ├── fallback_edge_cases/        # 極端情境與錯誤容受測試 (如 Quota 耗盡防呆)
        │
        └── system_resilience/          # 系統韌性與架構測試
            ├── test_service_lifecycle.md # 驗證 start_server.sh / stop_server.sh 防止資料庫死鎖機制
            └── test_tier_ranking.md      # 驗證 Tier 星級加分在同等距離下是否生效

## 4. 近期歸檔行動計畫 (Next Actions)
一旦此計畫確認，我們將把歷次執行的成功自動化測試，按上述結構移入 `tests/e2e_reports/`：
1. **[AI 語意路徑] 清晨五點吃早餐測試** ➔ 歸檔至 `ai_intent_flow`
2. **[AI 語意路徑] 松山文創散策測試** ➔ 歸檔至 `ai_intent_flow`
3. **[傳統點選路徑] 信義商圈購物測試** ➔ 歸檔至 `manual_ui_flow`
4. **[核心推薦邏輯] 內湖看夜景 (碧山巖 Tier 霸榜測試)** ➔ 歸檔至 `system_resilience/test_tier_ranking.md`
5. **[運維架構] Uvicorn 與 ChromaDB 衝突排解測試** ➔ 歸檔至 `system_resilience/test_service_lifecycle.md`
