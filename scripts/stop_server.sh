#!/bin/bash
# stop_server.sh
# 優雅關閉系統主伺服器 (Service Lifecycle Management)

echo "🛑 [Service Lifecycle] 尋找並關閉 Uvicorn 執行緒..."

# 1. 尋找 Uvicorn 的行程並關閉
if pgrep -f "uvicorn src.main:app" > /dev/null; then
    pkill -f "uvicorn src.main:app"
    echo "✅ [Service Lifecycle] 已發送優雅關閉訊號給 Uvicorn (等待關機作業)..."
    # 等待 1.5 秒讓 Uvicorn 處理 Shutdown 事件，釋放 ChromaDB 的檔案鎖
    sleep 1.5
else
    echo "ℹ️ [Service Lifecycle] 目標伺服器原本就處於離線狀態，沒有背景進程。"
fi

# 2. 雙重防呆: 確認 Port 8000 是否徹底釋放
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ [Service Lifecycle] 警告: Port 8000 仍被佔用，執行最終級強制擊殺 (kill -9)..."
    lsof -Pi :8000 -sTCP:LISTEN -t | xargs kill -9
    echo "✅ [Service Lifecycle] 幽靈進程已終結，Port 8000 現已釋出。"
else
    echo "✅ [Service Lifecycle] 伺服器已徹底關閉，所有被鎖定的資料庫檔案已釋放！"
fi
