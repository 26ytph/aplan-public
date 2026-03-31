#!/bin/bash
# start_server.sh
# 優雅啟動系統主伺服器 (Service Lifecycle Management)

echo "🔄 [Service Lifecycle] 準備啟動 Uvicorn 伺服器..."

# 1. 為了防範 Port 被重複佔用，一率先嘗試執行關閉程序
cd "$(dirname "$0")/.." || exit
./scripts/stop_server.sh > /dev/null 2>&1

# 2. 啟動 Uvicorn in the background
nohup .venv/bin/python -m uvicorn src.main:app --reload --port 8000 > uvicorn.log 2>&1 &
PID=$!

echo "✅ [Service Lifecycle] 伺服器已在背景啟動 (PID: $PID)！"
echo "👉 預計 3 秒後完成初始化。您可以透過 'cat uvicorn.log' 查看啟動狀態與日誌。"

# 3. 給予 2 秒的啟動緩衝，再秀出最後幾行 log 供確認
sleep 2
tail -n 5 uvicorn.log
