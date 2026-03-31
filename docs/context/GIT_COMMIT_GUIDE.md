# Git Commit 規範指南 (AI-Native Hackathon Edition)

> [!NOTE]
> 為了確保「AI 與人類」以及「不同 AI 模型」之間能高效協作，我們採用 **Conventional Commits** 規範，並針對 AI 世代增加了微幅調整。

---

## 1. 核心格式

```text
<type>(<scope>): <subject>
                                  ← 空行
<body>                            ← 選填，說明 Why / What
```

### 1.1 Type（類型）

| Type | 說明 | 何時使用 |
|------|------|----------|
| `feat` | 新增功能 | 新增 API 端點、新 UI 元件、新演算法 |
| `fix` | 修復 Bug | 修正已知錯誤行為或例外 |
| `docs` | 修改文件 | README、ADR、開發日誌、指南等 |
| `refactor` | 重構程式碼 | 不改變外部行為，只改善內部結構 |
| `chore` | 瑣事 | 目錄清理、依賴升級、CI 設定 |
| `test` | 測試相關 | 新增或修改測試案例與報告 |
| `style` | 格式調整 | 縮排、空白、分號等不影響邏輯的變更 |
| `skill` | **[AI-Native]** | 建立或更新 `.agents/skills/` 中的 AI Skill |

### 1.2 Scope（範圍）— 選填但建議標註

Scope 用來標示**受影響的模組**，幫助團隊在 `git log` 中快速定位變更區域。

| Scope | 對應目錄 | 範例 |
|-------|----------|------|
| `api` | `src/api/` | `feat(api): 新增意圖解析端點` |
| `core` | `src/core/` | `refactor(core): 簡化推薦引擎 Prompt` |
| `db` | `src/db/` | `feat(db): 新增向量資料庫遷移腳本` |
| `ui` | `src/templates/`, `src/static/` | `fix(ui): 修正 Toast 無法手動關閉` |
| `llm` | `src/utils/llm_adapter.py` | `feat(llm): 實作多模型 Fallback` |
| `config` | `src/core/config.py`, `.env` | `chore(config): 新增 ANTHROPIC_API_KEY` |
| `docs` | `docs/` | `docs(adr): 記錄 ChromaDB 選型決策` |

> [!TIP]
> 如果一次 Commit 橫跨多個模組，可省略 Scope，改在 body 中逐條列出。

### 1.3 Subject（標題）

| 規則 | ✅ 正確 | ❌ 錯誤 |
|------|---------|---------|
| 使用祈使句 | `實作語意檢索端點` | `實作了語意檢索端點` |
| 控制在 50 字元內 | `移除 llm_adapter.py 死碼` | `移除 llm_adapter.py 中殘留的舊版 IntentResponse 和 parse_user_intent 函式` |
| 不加句號 | `新增 ChromaDB 遷移腳本` | `新增 ChromaDB 遷移腳本。` |
| 說明「做了什麼」而非「改了哪個檔案」| `統一 Pydantic Models 至單一來源` | `修改 schemas.py 和 options.py` |

---

## 2. Body 撰寫指引

Body 是選填的，但以下情境**強烈建議**加上：

| 情境 | 應寫什麼 |
|------|----------|
| 重構 | **為什麼**要重構？改善了什麼問題？ |
| Bug 修復 | Bug 的**根本原因**是什麼？如何復現？ |
| 破壞性變更 | 加上 `BREAKING CHANGE:` 標記，說明影響範圍 |
| Phase 總結 | 條列本 Phase 完成的所有子任務 |

**Body 格式**：每行不超過 72 字元，使用 `-` 條列。

---

## 3. AI 協作特別建議

### 3.1 `/handoff` 前的 Phase 總結 Commit

在一個開發 Phase 結束時，請確保最後一個 Commit 能讓接手的 AI 模型透過 `git log -1` 快速重建脈絡：

```text
refactor: 完成 Phase II 重構並固化 3 個開發 Skill

- 移除 llm_adapter.py 的 30 行死碼
- 補齊 src/ 子目錄的 __init__.py
- 將 Pydantic Models 統一遷移至 schemas.py
- 建立 gemini-structured-output 等 3 個 Skill
```

### 3.2 AI 自動產生的 Commit

當 AI 模型代替開發者產生 Commit 時，建議在 body 末尾標註模型資訊：

```text
Co-authored-by: Antigravity (Gemini) <noreply@google.com>
```

---

## 4. 提交前檢查清單

- [ ] 是否使用了正確的 `type` 前綴？
- [ ] 標題是否一眼就能看出變更的核心價值？
- [ ] 若為 Breaking Change，是否在 body 加上 `BREAKING CHANGE:` 說明？
- [ ] Commit 是否保持原子性？（一個 Commit 只做一件事）

---

## 📚 延伸閱讀

想看更多貼合本專案的**完整情境範例**，請參考：
- 👉 [GIT_COMMIT_EXAMPLES.md](GIT_COMMIT_EXAMPLES.md) — 以本專案 Sprint 1~6 的真實開發歷程為素材，提供 10+ 個情境式範例。
