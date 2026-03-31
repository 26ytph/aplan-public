# ChromaDB 災難回顧與解決架構 (Lessons Learned)

## 🚨 事件背景 (Context)
在 Phase 32 執行「全球美食菁英資料 RAG 全量重建」階段時，`Fast-Track` 推薦 API 突發伺服器級崩潰 (HTTP 500 Error)。
日誌顯示：`chromadb.errors.InternalError: Error sending backfill request to compactor: Failed to apply logs to the hnsw segment writer`。
這導致原先建立的高品質向量索引完全毀損，推薦系統徹底失效。

---

## 🔍 根本原因分析 (Root Cause)
此次災難的核心癥結在於：**違反了 ChromaDB `PersistentClient` 嚴格的單一進程 (Single-process) 限制。**
1. **底層架構限制**：專案採用的 `PersistentClient` 是將資料存在本地資料夾 (`./.gemini/chroma_db`)。它底層依賴 SQLite/DuckDB 的檔案鎖 (File Lock) 來保護 HNSW 語意搜尋網格。它**天生不支援**多重 Python 進程同時對該目錄進行併發讀寫 (Multi-process Concurrent Write)。
2. **觸發災難的併行操作**：
   - 當時背景負責處理 API 的 **Uvicorn 主伺服器 (Process A)** 正與資料夾維持持續開啟的連線讀取狀態。
   - 開發者同時在 Terminal 中執行了資料大批次匯入腳本 **`reindex_all.py` (Process B)**。
   - 兩個進程爭奪同一個檔案的寫入權，導致 WAL (Write-Ahead Log) 預寫式日誌無法套用於 HNSW Segment，檔案毀損並爆發上述 Fatal Error。

---

## 🛠️ 短期改進方案 (Short-Term Mitigation)
**核心精神：離線批次寫入 (Offline Batch Write) 與嚴格的生命週期管理**

我們立刻中止了手動隨意關閉進程的做法，改用自動化的 **服務生命週期管理 (Service Lifecycle Management)** 技能來杜絕此類人為風險：
1. **強制關閉再寫入**：在執行任何 `scripts/` 背景匯入工作前，嚴格規定必須呼叫 `./scripts/stop_server.sh`。該腳本會安全釋放 Port 並解除專案裡所有的資料庫檔案鎖。
2. **優雅重啟**：當匯入作業結束後，再透過 `./scripts/start_server.sh` 於背景將服務安全重啟。
3. **優點**：無需修改任何程式邏輯，系統維護成本極低。
4. **缺點**：伺服器在大規模資料匯入的 2~3 分鐘內會產生服務中斷 (Downtime)。

---

## 🏗️ 長期解決方案 (Long-Term Architectural Solution)
**核心精神：升級為 Client-Server 微服務架構 (Real-time Concurrent Write)**

若未來專案規模進一步擴大，要求「不允許停機 (Zero Downtime)」，且需要「爬蟲即時匯入資料」，則必須將 ChromaDB 的架構升級：
1. **自立門戶的獨立服務**：將向量資料庫抽離，讓它成為一個持續在背景執行的獨立守護進程，例如透過指令 `chroma run --path .gemini/chroma_db --port 8000` 來運行原生的 Chroma Server。
2. **重構後端連線程式碼**：將 `src/db/vector_store.py` 中所有的 `chromadb.PersistentClient(...)`，全面修改為基於網路通訊的 `chromadb.HttpClient(...)`。
3. **效益**：所有來自 Uvicorn API 與背景 `reindex_all.py` 的讀寫需求，都會轉換成 HTTP 封包，交由獨立的 Chroma Server 統一管理排隊與寫入鎖，100% 根絕檔案死鎖與毀損風險。
