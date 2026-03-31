# 🚀 AI-Native Productivity & Collaboration Handbook
> 臺北時光機 (Taipei Time Machine) - AI 協作與生產力全局手冊

本指南適用於所有使用 AI 輔助編程工具（如 Google Cursor、Antigravity、GitHub Copilot）參與本專案開發的團隊成員與智能體。本手冊匯總了專案在「生產力提升」、「AI 約束」以及「協作流程」上的所有最佳實務。

---

## 1. 🌟 總覽與核心哲學 (The AI-Native Philosophy)

在 AI-Native 的世代，我們不僅僅把 Python 程式碼推上 GitHub。我們意識到：**「對 AI 的指令 (Prompt)、自動化技能 (Skills) 與規則防護 (Rules)，與業務程式碼本身同等重要。」**

因此，這個專案將所有的「生產力工具」與原始碼放在同一個環境下進行**版本控制 (Version Control)**。這代表著：
*   **記憶傳承**：任何新的隊友（或他切換使用的任何新 AI 模型），只要拉取 (`git pull`) 最新的 Repo，就能瞬間擁有與原作者相同水準的防護牆與工作流。
*   **永續優化**：當你發現 AI 在開發某項功能時屢次犯下相同的架構錯誤，**請不要只在當前的對話視窗糾正它**；你應該把這個踩坑經歷寫成一條 Rule 存進 codebase，讓它成為專案永久的「肌肉記憶」。

---

## 2. 🧠 全局守則與約束 (System Rules & Prompts)

為了確保不同語言模型 (Claude, Gemini, GPT-4) 進入專案時不迷路、不擅自發明規則，我們設立了全域防護欄：

*   **`PROJECT_CONTEXT.md` (專案大腦)**：
    這是所有 AI 接手任務時**必須強制閱讀的第一份文件**。它定義了我們目前所在的開發階段 (Beta Release)、專案目標，以及最重要的「目錄結構約定」。
*   **`.gemini/rules/` (肌肉記憶引擎)**：
    這裡存放著針對特定技術棧的深層次防呆腳本。例如 `python-fastapi-rules.md` 強制約定了我們 FastAPI 的 Router 分層法與變數命名慣例。**這確保 AI 不會用隨性的風格污染我們 Enterprise-Grade 的架構**。

---

## 3. 🛠️ 擴充技能庫 (AI Agent Skills)

我們賦予了 AI 各式各樣的「超能力」，以應對瑣碎的開發日常。這些腳本放置於 **`.agents/skills/`** 下，AI 在評估任務時會自動尋找並引用它們：

| 技能名稱 (Skill) | 觸發情境與用途 |
| :--- | :--- |
| `agentic-e2e-testing` | 指導 AI 如何使用 Playwright 或 Browser Subagent 撰寫前端自動化 UI 驗證測試，確保不打破推薦卡片的渲染邏輯。 |
| `bulletproof-llm-fallback` | 專案御用模板：指導如何實作多模型容錯降級（例如 Gemini Quota 耗盡時如何切換其他模型）。 |
| `gemini-structured-output` | 說明如何正確驅動最新版 Google GenAI SDK 強制輸出 Pydantic JSON 結構，不會出現 Markdown 雜訊。 |
| `service-lifecycle-management` | **極端防死鎖**：指導 AI 正確利用 Bash 腳本 (`stop_server.sh`) 優雅關閉 Uvicorn，防止 ChromaDB 的 SQLite 遭到鎖死破壞。 |
| `github-repo-init` | 提供一份標準化劇本，包含 .gitignore 設定、README 瘦身與首次推播的標準流程。 |
| `sqlite-to-excel-export` | 營運小幫手：將嚴謹的 SQLite 觀光景點陣列，匯出成適合人類（如評審）審查的 Excel 多分頁報表。 |

---

## 4. 🔄 標準作業流 (Workflows & Handoff)

放置於 **`.agents/workflows/`** 中，這是人類直接下達給 AI 的「外掛快捷鍵」，用於規範複雜的連續任務。在對話視窗中輸入 `/指令` 即可啟動：

*   ▶️ **`/handoff` (零斷層交接)**：
    接手專案或重開對話的第一把交椅。AI 會自動掃描最近的 Git Commit、架構演進日誌與 Task，瞬間繼承前序開發者的邏輯與進度。
*   ▶️ **`/strict-planning` (嚴格煞車模式)**：
    當準備進行**重大架構重構 (Refactoring)** 時使用。強制啟動嚴格審核：AI 不能直接改 code，必須先產出 `implementation_plan.md`，讓人打勾核准後才能逐步執行。

---

## 5. 🐙 版本控制與協作策略 (GitHub Culture)

如何完美地與開發夥伴在版本庫中跳舞：

1.  **Semantic Commit Messages (語意視覺化版控)**：
    我們推崇 `GIT_COMMIT_EXAMPLES.md` 中約定的法則，每次 push 前必須標註 emoji 與動詞（如 `✨ Feat`, `🐛 Fix`, `🔖 Release`），讓專案的歷史長廊就像是一本優美的日記。
2.  **開發演進日誌 (Journey Logs)**：
    每完成一個重要里程碑（如接入 YouBike 或 OpenStreetMap），請要求 AI 在 **`docs/journeys/`** 下產出一份 `NN_phaseN_簡述.md`。記錄我們「為什麼選擇這個解法」、「捨棄了什麼方案」，這比程式碼註解還要珍貴。
3.  **禁止 AI "幻覺式覆蓋"**：
    在 Pull Request 或多人協作時，要求 AI 修改檔案前**絕對要先完整檢視 (View File)**，避免只聽信單方面指令而覆蓋掉隊友剛寫好的功能。

---

## 6. 📂 生產力目錄尋寶圖 (Productivity Directory Map)

如果你想尋找或擴充上述的神兵利器，請參考這張地圖：

```text
aplan/
├── .agents/
│   ├── skills/             # 🛠️ 各領域 AI 專屬自動化技能包 
│   └── workflows/          # 🔄 /handoff 等指令劇本
├── .gemini/
│   └── rules/              # 🧠 底層語言與框架防呆守則
├── docs/
│   ├── context/
│   │   └── AI_PRODUCTIVITY_HANDBOOK.md  # 📍 你現在在這裡
│   └── journeys/           # 🚀 每週期的里程碑歷史決策日誌
├── PROJECT_CONTEXT.md      # 📜 專案核心業務錨點
└── README.md               # 🏠 GitHub 首頁對外迎賓門面
```

> **終極精神**：當程式碼變為 Legacy 時，優良的防呆守則 (Rules) 與決策日誌 (Journeys) 將是你最堅實的後盾。
