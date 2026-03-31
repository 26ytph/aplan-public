---
description: 專門處理優雅的啟動與關閉系統後端服務 (Uvicorn)，以防止 ChromaDB 資料庫死鎖與 Port 佔用
---

# 服務生命週期管理 (Service Lifecycle Management)

當需要重啟伺服器、解決 API 報錯 (例如 `500 Failed to apply logs to the hnsw segment writer`)、或需要在背景執行資料庫大規模匯入任務 (`reindex_all.py` 等) 時，你**必須**使用此技能來管理伺服器程序的啟動與關閉。

## ⚠️ 核心原則：為何需要「優雅關閉」？
因為專案底層使用的本地端 ChromaDB (`PersistentClient`) **不支援多進程併發讀寫 (Multi-process write)**。
如果 Uvicorn 仍在運行中（抓住了 ChromaDB 目錄的手），此時再利用外部的 Python 腳本進行大數據匯入，將導致檔案系統發生嚴重的 Lock 衝突，引發災難性的索引壞軌 (Corrupted Index)。

因此，在執行任何影響向量資料庫的背景批次作業「**之前**」，請一律先優雅關閉主伺服器。

---

## 🛑 如何「優雅關閉」服務 (Graceful Stop)
請直接呼叫封裝好的關閉腳本：
```bash
./scripts/stop_server.sh
```

**內部動作：**
1. 找出並關閉執行 `uvicorn src.main:app` 的進程 (`pkill -f`)。
2. 釋放被佔用的 Port 8000。
3. 安全解除 ChromaDB 檔案系統目錄鎖 (Directory Lock)。

---

## 🚀 如何「優雅啟動」服務 (Graceful Start)
當資料庫處理任務完成，或者系統重新上線時，請呼叫：
```bash
./scripts/start_server.sh
```

**內部動作：**
1. 雙重確認舊的伺服器已徹底關閉避免 Port 衝突。
2. 在背景安全啟動 Uvicorn (`nohup`) 並切換為 `reload` 模式。
3. 將標準日誌重導向至專案根目錄的 `uvicorn.log`。

---

## 🩺 偵錯與急救手段 (Troubleshooting)
1. **確認是否啟動成功**：
   執行 `tail -n 20 uvicorn.log`，確認看到 `Application startup complete.` 字樣。
2. **Port 8000 頑固卡死**：
   有時遇到 Zombie Thread，上述腳本可能無法成功擊殺伺服器。請使用以下方式暴力釋放：
   ```bash
   lsof -i :8000 | grep LISTEN
   # 然後將對應的 PID 強制關閉：
   kill -9 <PID>
   ```
