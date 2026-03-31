---
name: agentic-e2e-testing
description: 前端 E2E 自動化測試的兩種模式（Playwright 腳本 vs. Browser Subagent），含命名規範與呼叫語法
---

# E2E 自動化測試 Skill

本技能涵蓋兩種前端 E2E 測試流派，各有適用場景。**AI 必須根據情境選擇正確的模式**。

---

## 🔀 模式選擇指南

| | **Mode A: Playwright 腳本** | **Mode B: Browser Subagent** |
|---|---|---|
| **適用場景** | 需要精確控制、穩定重現、使用者想在自己的 Terminal 看到完整 Log | 快速探索性驗證、UI 視覺巡檢、不值得寫腳本的一次性操作 |
| **執行者** | 使用者在自己的 Terminal 執行 | AI 在 Agent Shell 內背景執行 |
| **可靠度** | ⭐⭐⭐⭐⭐（確定性高，可重現） | ⭐⭐⭐（依賴視覺推理與網路，偶爾卡住） |
| **中文輸入** | ✅ `.fill()` 原生支援 | ⚠️ 需透過 JS 注入 |
| **產出** | `.png` 截圖 + `.webm` 錄影 + Terminal Log | `.webp` 錄影 + `.png` 截圖 + 文字報告 |

---

## Mode A: Playwright 腳本（推薦）

### 呼叫語法

使用者或 AI 在對話中以 `[playwright]` 標記明確指定：

> "請用 **Playwright** 幫我測試 i18n 語言切換功能，切到日文後搜尋日文查詢。"

AI 收到後必須：
1. 在 `tests/` 目錄下建立 `run_e2e_{scenario_name}.py`
2. 提供一行可直接貼上 Terminal 的指令

### 腳本模板規範

```python
import time, sys, os, shutil
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SCENARIO_NAME = "e2e_{scenario}_{date}"  # 例: e2e_i18n_english_switch_20260327
VIDEO_DIR = "tests/e2e_videos"

def run_test():
    # 🎬 必開錄影
    context = browser.new_context(
        record_video_dir=VIDEO_DIR,
        record_video_size={"width": 1280, "height": 750}
    )
    page = context.new_page()
    # ... 測試步驟 ...
    
    # ✅ 結尾：關閉錄影 context → 重新命名 → 開新頁面供手動測試
    raw_video_path = page.video.path()
    final_video_path = os.path.join(VIDEO_DIR, f"{SCENARIO_NAME}.webm")
    
    context.close()  # Flush 錄影到磁碟
    if os.path.exists(raw_video_path):
        shutil.move(raw_video_path, final_video_path)
    
    # 開新頁面（無錄影）供使用者手動繼續測試
    manual_page = browser.new_page()
    manual_page.goto("http://localhost:8000", timeout=15000)
    
    print("✅ 自動化測試劇本已走完！錄影已存檔。")
    print(f"   🎬 錄影: {final_video_path}")
    print("👉 選項 A: 您可以在瀏覽器上「手動繼續測試」其他功能")
    print("👉 選項 B: 回到 Terminal 按下 [Enter] 關閉瀏覽器，結束本次測試")
    input(">>> 按下 [Enter] 關閉瀏覽器...")
    browser.close()
```

> [!CAUTION]
> **禁止在背景 Thread 中呼叫 Playwright sync API！** Playwright 使用 greenlet 執行模型，跨線程呼叫 `context.close()` 會觸發 `greenlet.error: cannot switch to a different thread`。所有 Playwright API 呼叫必須在主線程完成。

### 交付方式

AI 建立好腳本後，必須交付：
```
👉 請在 Terminal 執行：
.venv/bin/python tests/run_e2e_{scenario_name}.py
```

---

## Mode B: Browser Subagent

### 呼叫語法

使用者在對話中以 `[subagent]` 標記、或使用自然語言描述即席檢查：

> "請用 **Browser Subagent** 幫我快速截圖看看首頁長什麼樣子。"
> "請前往 localhost:8000，截圖回報目前 UI 狀態。"

### 必要的 Prompt 指令

**錄影防掛滅守則**（必須在 Task 中附帶）：
> **[強制限制 1]** 每點擊一次按鈕，必須強制執行 `Sleep(3000ms)` 讓畫面完全渲染。
> **[強制限制 2]** 操作結束後，絕對不可以立刻回傳！你必須在該畫面上再待滿 `Sleep(5000ms)`。

### ⚠️ 注意事項

- 中文輸入需透過 `document.getElementById(...).value = "..."` 的 JS 注入
- 後端觸發的 API 會消耗 Gemini Free Tier 額度
- 若 Subagent 連續卡住，**立即降級為 Mode A**

---

## 📁 命名規範（兩種模式共用）

### 截圖命名

```
e2e_{scenario}_{date}.png
```

### 錄影命名

Playwright 錄影引擎會自動產生 hash 檔名。**測試腳本結束時必須重新命名**為：
```
tests/e2e_videos/e2e_{scenario}_{date}.webm
```
透過 `shutil.move(raw_video_path, final_video_path)` 完成。

### 測試腳本命名

```
tests/run_e2e_{scenario_name}.py
```

---

## 🏁 結尾訊息規範

不論哪種模式，測試結束時**必須**提供以下資訊：

1. ✅ / ❌ 明確的 Pass/Fail 判定
2. 📸 截圖檔案路徑
3. 🎬 錄影檔案路徑
4. 👉 **下一步操作指引**：告知使用者可以「繼續手動測試」或「按 Enter 關閉」

## 🎬 錄影收尾機制（Two-Context 策略）

測試劇本走完後：
1. 立即 `context.close()` — flush 錄影到磁碟
2. `shutil.move()` — 將 hash 檔名改為可讀名稱
3. `browser.new_page()` — 開新頁面（無錄影），供使用者手動繼續操作
4. `input()` — 等待使用者按 Enter 關閉瀏覽器
