# 🧪 Beta Verification & Validation Handoff Guide
> 臺北時光機 (Taipei Time Machine) - QA 團隊交付與驗證手冊

本文件旨在為 QA Team 提供 Beta Release (Phase 34) 的全面驗證框架。本專案採行 **Agentic E2E Testing** 策略，優先使用自然語言或 AI 驅動腳本進行全系統驗證。

---

## 1. 🌍 系統服務基準 (Service Baselines)

在開始測試前，請確保開發環境已正確啟動：
*   **啟動指令**：`./scripts/start_server.sh` (確保 FastAPI 獲取 8000 Port)。
*   **關閉指令**：`./scripts/stop_server.sh` (⚠️ **重要**：必須以此指令關閉，以釋放 SQLite/ChromaDB 鎖定，防止資料庫死鎖損毀)。
*   **環境變數**：`.env` 需包含有效的 `GEMINI_API_KEY`。

---

## 2. 🛡️ 核心功能驗證地圖 (Verification Map)

本章節定義了如何「技術性驗證」系統各個模組是否如預期運作。

| 模組功能 (Feature) | 驗證腳本 (Automation Script) | 預期結果 (Expected Outcome) |
| :--- | :--- | :--- |
| **YouBike 即時情境層** | `tests/e2e_reports/system_resilience/test_ubike_integration.py` | 成功獲取 1700+ 站點，精準計算 500m 內租還資訊，含 available_bikes > 0 邏輯。 |
| **語意意圖解析 (RAG)** | `tests/e2e_reports/ai_intent_flow/run_cityhall_rain_baseline.py` | 使用者輸入「下大雨」時，UI 需正確鎖定 ☔ 圖示，且推薦卡片需包含室內行程（如台北探索館）。 |
| **OSM 動態地圖退路** | **手動測試**：搜尋已知無圖片景點 (例如：內湖 Costco) | 景點卡片不應出現空白，應自動渲染包含紅色標記點的 OpenStreetMap 灰階圖資。 |
| **多國語系切換 (I18N)** | `tests/e2e_reports/manual_ui_flow/run_e2e_i18n_english.py` | 切換至 English 時，介面導航項與靜態文字需 100% 同步翻修。 |

---

## 3. 🧩 情境確認與邊界測試 (Validation & Edge Cases)

本章節著重於使用者體驗與異常處理的「Validation」。請嘗試以下場景以挑戰系統強韌度：

*   **📍 座標邊界挑戰**：
    *   將座標點設為「陽明山深處」或「基隆市邊界」。
    *   **預期**：YouBike 元件應優雅消失（因為 1km 內無站點），系統不應崩潰。
*   **☔ 天氣與意圖衝突挑戰**：
    *   當現在天氣是「晴天」，但使用者輸入「我想去躲雨」。
    *   **預期**：AI 意圖應擁有最高優先權 (AI-Lock)，UI 天氣圖標應切換為雨天，並暫停自動輪詢即時氣象。
*   **🧠 語意混淆挑戰**：
    *   輸入一句完全無關的胡言亂語。
    *   **預期**：LLM 應能正確判斷為「無意圖」並返回友善的引導回覆。

---

## 4. 📂 測試資產目錄說明

*   **`tests/e2e_reports/ai_intent_flow/`**：收納 AI 語意解析的 Baseline 錄影與腳本。
*   **`tests/e2e_reports/manual_ui_flow/`**：收納傳統 UI 交互測試資產。
*   **`tests/e2e_reports/system_resilience/`**：收納關乎系統穩定性、API 效能與距離演算法的單元/整合測試。
*   **`tests/e2e_videos/`**：存放由 Playwright/Browser Subagent 產出的最新成功操作錄影。

---

## 5. 📧 異常回報 (Reporting Bugs)

發現異常時，請務必隨附 `tests/e2e_views/` 下對應的失敗截圖，並在 Issue 中標註測試所在的 **Phase 版本號**。

> **QA Team Mission**：本專案的使命是確保每一位旅客在臺北的雨天，都能透過一句話找到溫暖的棲身之所。請用最嚴格的標準挑戰它！
