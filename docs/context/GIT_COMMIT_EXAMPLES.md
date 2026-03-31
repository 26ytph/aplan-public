# Git Commit 情境範例冊 (Based on Real Project History)

> 本文件以「臺北時光機」Sprint 1 ~ 6 的真實開發歷程為素材，提供團隊成員可直接參考的 Commit 範例。每個範例都附有**正確**與**錯誤**的對比，幫助你快速上手。

---

## 🟢 情境 1：新增 API 端點

**場景**：Sprint 4 實作意圖解析 API。

✅ **正確**
```text
feat(api): 實作 /parse-intent 語意解析端點

利用 Gemini Structured Output 將自然語言轉換為
IntentResponse JSON，支援地點、天氣、時間、標籤四維度。
```

❌ **錯誤**
```text
新增了 intent.py
```
> 💡 **問題**：缺少 type 前綴、缺少 scope、標題描述的是「改了哪個檔案」而非「做了什麼」。

---

## 🟢 情境 2：修復 UI Bug

**場景**：Sprint 6 發現 Toast 錯誤通知無法手動關閉。

✅ **正確**
```text
fix(ui): 錯誤級 Toast 改為手動關閉，不自動消失

Bug：error/warning Toast 與 success Toast 共用 4 秒自動
消失邏輯，導致使用者來不及閱讀錯誤訊息。
修復：僅 success/info 類型自動消失，error/warning 強制
使用者手動點擊 × 關閉。
```

❌ **錯誤**
```text
fix: 修了 bug
```
> 💡 **問題**：完全看不出修了什麼 Bug、在哪裡修的。

---

## 🟢 情境 3：重構 / 移除死碼

**場景**：Phase II 審計後移除 `llm_adapter.py` 中的重複模型。

✅ **正確**
```text
refactor(llm): 移除 IntentResponse 副本與孤立的 parse_user_intent

Phase I 審計發現 llm_adapter.py 底部殘留 30 行死碼：
- IntentResponse 副本缺少 selected_time 欄位，與
  schemas.py 正式版本不同步
- parse_user_intent() 已被 intent.py 的 API 端點取代
```

❌ **錯誤**
```text
清理程式碼
```
> 💡 **問題**：缺少 type、沒有解釋為什麼要清理。

---

## 🟢 情境 4：補齊基礎設施

**場景**：所有 `src/` 子目錄缺少 `__init__.py`。

✅ **正確**
```text
chore: 為 src/ 全部 6 個子目錄補齊 __init__.py

確保 Python 正確將各子目錄視為合法 Package，修復未來
pytest 與 import 可能的 ModuleNotFoundError。
```

❌ **錯誤**
```text
加了一堆 __init__.py
```

---

## 🟢 情境 5：文件更新

**場景**：競賽準備階段更新 README 執行步驟。

✅ **正確**
```text
docs(readme): 更新快速啟動步驟，補充 ChromaDB 遷移指令

新增 Step 3: 執行 python scripts/migrate_to_chroma.py
以確保首次啟動前向量資料庫已就緒。
```

❌ **錯誤**
```text
docs: 更新文件
```
> 💡 **問題**：太籠統。一個專案有幾十份文件，「更新文件」等於沒說。

---

## 🟢 情境 6：新增測試報告

**場景**：使用 Browser Subagent 完成手動 UI 流程測試。

✅ **正確**
```text
test(e2e): 新增手動 UI 操作流程測試報告與錄影

測試場景：手動選取華山1914 + 夜間美食/文青散策標籤
結果：PASS — 推薦引擎正確產出榕錦時光與寧夏夜市
歸檔：tests/e2e_reports/manual_ui_flow/
```

❌ **錯誤**
```text
測試通過了
```

---

## 🟢 情境 7：建立 AI Skill

**場景**：將 Gemini Structured Output 的用法固化為可重複使用的 Skill。

✅ **正確**
```text
skill: 建立 gemini-structured-output 技能模板

記錄如何正確搭配 google-genai SDK 的 response_schema
參數與 Pydantic Model 實現強制 JSON 結構化輸出。
路徑：.agents/skills/gemini-structured-output/SKILL.md
```

---

## 🟢 情境 8：資料庫遷移

**場景**：Sprint 5 從 SQL 關鍵字比對升級為 ChromaDB 向量檢索。

✅ **正確**
```text
feat(db): 實作 ChromaDB 語意向量遷移腳本

新增 scripts/migrate_to_chroma.py：
- 從 SQLite 讀取景點與貼文資料
- 使用 gemini-embedding-001 進行向量化
- 寫入 .gemini/chroma_db PersistentClient
```

---

## 🟢 情境 9：Phase 結束總結 Commit

**場景**：Phase II 重構全部完成，準備交棒給下一個 AI 模型。

✅ **正確**
```text
refactor: 完成 Phase II 精準重構 (3 項修復 + 鷹架合規)

HIGH:
- 移除 llm_adapter.py 30 行死碼
- 補齊 src/ 全部 __init__.py
- 統一 Pydantic Models 至 schemas.py

MEDIUM:
- 清除空目錄 src/components/
- 遷移 print() 至 logging 模組

Co-authored-by: Antigravity (Gemini) <noreply@google.com>
```

---

## 🟢 情境 10：破壞性變更

**場景**：假設未來將 API 路徑從 `/api/v1/` 改為 `/api/v2/`。

✅ **正確**
```text
feat(api): 升級至 API v2，調整路由前綴

BREAKING CHANGE: 所有 /api/v1/* 端點更名為 /api/v2/*。
前端需同步更新 fetch URL。受影響端點：
- /api/v1/recommendations/ → /api/v2/recommendations/
- /api/v1/parse-intent → /api/v2/parse-intent
- /api/v1/metadata/* → /api/v2/metadata/*
```

---

## 📌 速查對照表

| 你想做的事 | Type | Scope 建議 |
|-----------|------|-----------|
| 新增 API 路由 | `feat` | `api` |
| 修正前端顯示錯誤 | `fix` | `ui` |
| 移除無用程式碼 | `refactor` | 受影響模組 |
| 補齊 `__init__.py` | `chore` | 省略 |
| 更新 README | `docs` | `readme` |
| 寫測試報告 | `test` | `e2e` 或 `unit` |
| 固化開發技巧為 Skill | `skill` | 省略 |
| 升級套件版本 | `chore` | `deps` |
| 調整 CSS 縮排 | `style` | `ui` |
| 記錄架構決策 | `docs` | `adr` |
