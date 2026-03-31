# 🛠️ Phase 2 效能優化與測試最佳實務 (Performance & Testing Log)

**時間：** 2026年3月
**目標：** 解決初期雛形的效能瓶頸、確立團隊協作與版控規範，並建立高強度的自動化 E2E 測試標準。

在奠定了 Phase 1 的 AI 核心與 UI 基礎後，專案進入了注重「可維護性」、「非同步效能」與「自動化驗證」的 Phase 2 階段。以下記錄三個極為關鍵的 Sprint 技術挑戰與決策。

---

## 1. 🚀 後端效能優化 Sprint (Non-blocking Async I/O)

### 📌 痛點與挑戰
- 舊版 `vector_store.py` 在 `upsert_pois`、`query_pois` 等方法中，直接使用了 `chromadb` 的同步 (Synchronous) 磁碟 I/O 操作。
- 由於 FastAPI 是建立在 `asyncio` 事件循環之上，這會導致當有大量相似度搜尋請求湧入時，**整個伺服器的 Event Loop 被嚴重阻塞 (Blocked)**，造成其他請求排隊等待，大幅降低了系統的高併發吞吐量。

### 🔧 實作決策與重構
- 導入了 `asyncio.to_thread()` 將所有同步的 ChromaDB 磁碟操作封裝入獨立執行緒 (Thread Pool) 執行。
- 此舉確保了 FastAPI 的核心 Event Loop 得以持續保持閒置狀態以接應新請求，在高併發測試中獲得了極大的效能提升。

---

## 2. 🤝 團隊協作與版控 Sprint (Team Collaboration & VCS)

### 📌 痛點與挑戰
- 專案初期的 `git push` 極度依賴本機單一使用者的權限快取，且 GitHub 已廢棄密碼認證，導致在轉移或協作時頻繁出現 `403 Forbidden` 與認證失敗。

### 🔧 實作決策與重構
- **組織級遷移**：將專案正式從個人儲存庫遷移至官方指定的 `26ytph` 組織下 (`26ytph/aplan`)。
- **認證指南**：全面更新 `GITHUB_GUIDE.md`，詳列如何生成 Classic PAT (Personal Access Token) 並賦予 `repo` 權限，以徹底解決存取障礙。
- **建立交接標準**：確立了 `/handoff` 指令流程，讓未來不同的 AI Agent 或團隊開發者在接手開發時，能有一套標準程序瞬間同步上下文與決策脈絡。

---

## 3. 🧪 自動化驗證 Sprint (E2E Testing Best Practices)

### 📌 痛點與挑戰
- **字集對應錯誤**：在執行 Browser Subagent 自動化測試時，發現模擬鍵盤工具 (`browser_press_key`) 無法正確輸入繁體中文 Unicode（例如報錯 `Unknown key: "臺"`）。
- **錄影腐損問題**：測試腳本結束太快，導致瀏覽器錄影緩衝來不及完全寫入磁碟就中斷關閉，產出一堆僅 11KB 的毀損 `.webp` 影片。
- **環境未隔離**：測試過程一度誤用系統 Global Python 環境執行，未善加利用 `.venv` 虛擬環境，導致隱藏的套件缺失炸彈（如缺少 `chromadb`）。

### 🔧 實作決策與重構
- **最佳實務 (Best Practice) 落實**：
  1. **測試環境絕對隔離**：嚴格要求所有測試皆須在補齊 `requirements.txt` 後的 `.venv` 內啟動（`source .venv/bin/activate`）。
  2. **JS 注入繞過工具限制**：放棄不穩定的模擬打字，全面改用 JavaScript Injection (`document.getElementById(...).value = ...`) 將精確的中文測試語句送入 DOM，達成 100% 腳本精準度。
  3. **強制 I/O 留存緩衝 (Hard Wait)**：在生成測試結果後，強制指令工具在原地停留 60 秒（1分鐘），透過延長生命週期確保底層錄影引擎完美刷新緩衝。最終成功產出無殘缺、高畫質的 3.3MB `test_ai_intent_recording_20260319.webp` 檢驗證物。

---

*以上開發歷程與除錯經驗由 Antigravity 整理歸檔，為後續維護提供明確的技術脈絡。*
