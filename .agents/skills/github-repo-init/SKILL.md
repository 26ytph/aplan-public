---
name: github-repo-init
description: 專案首次推上 GitHub 時的標準化初始流程：.gitignore、README 精簡化、docs/ 目錄結構規劃與首次 commit
---

# GitHub Repo Init (專案發布準備) Skill

## 適用場景
當一個專案開發到一個階段，需要首次推上 GitHub 時。目標是在**完整保留開發歷程與文件**的同時，讓主專案看起來**極致簡潔優雅**。

## 核心原則：分離關注點

```text
根目錄 = 「5 秒讀懂怎麼跑」（極簡）
docs/   = 「想深入就進來看」（豐沛）
```

---

## Step 1: 建立 `.gitignore`

以下是 Python 專案的標準排除清單，請依實際技術棧調整：

```gitignore
# Environment variables (機敏資訊永不上傳)
.env

# Virtual environments
.venv/
venv/
__pycache__/
*.pyc

# System files
.DS_Store

# Databases (開發用暫存資料庫)
*.db
*.sqlite

# AI Agent raw cache (龐大的暫存對話紀錄)
.gemini/

# IDE
.idea/
.vscode/
```

### ⚠️ 注意：`.agents/` 應該被提交
`.agents/skills/` 和 `.agents/workflows/` 裡存放的是**團隊與 AI 共同淬鍊出來的方法論資產**，它們本身就是專案知識的一部分，**不應被忽略**。

---

## Step 2: 規劃 `docs/` 目錄結構

推薦的標準子目錄結構：

```text
docs/
├── context/      # 背景脈絡文件（競賽指引、外部規格書、原始需求）
├── journeys/     # AI 協同開發日誌與實作歷程（每個 Phase 一份 .md）
├── adr/          # Architecture Decision Records（重大技術決策紀錄）
├── architecture.md   # 系統架構圖（推薦用 Mermaid 嵌入）
├── flow_diagrams.md  # 核心流程循序圖
└── test_strategy.md  # 測試策略與計畫
```

**命名慣例：**
- `journeys/` 內的日誌檔以 `NN_phaseN_描述.md` 命名（例如 `01_phase1_implementation_log.md`）
- `context/` 放置不修改的「原始參考文件」
- `adr/` 以 `ADR-NNN-標題.md` 命名

---

## Step 3: 精簡化 `README.md`（五秒原則）

README 只保留三大區塊：

### 區塊 1: Hero（一句話介紹 + 專案簡述）
```markdown
# 專案名稱
**一句話 tagline**
兩到三行的精簡介紹。
```

### 區塊 2: Quick Start（複製貼上就能跑）
```markdown
## 🚀 快速上手
### 環境需求
### 安裝與啟動（一個 code block 搞定）
```

### 區塊 3: 文件導航（用表格連結至 docs/）
```markdown
## 📚 深入專案文件
| 分類 | 文件 | 說明 |
|------|------|------|
| 📐 架構 | [architecture.md](docs/architecture.md) | ... |
| 🚀 日誌 | [docs/journeys/](docs/journeys/) | ... |
```

**禁止出現在 README 的內容：**
- 冗長的功能細節描述（移至 `docs/`）
- 評審展示說明（移至 `docs/` 或獨立的 `DEMO.md`）
- 完整的技術棧清單（移至 `PROJECT_CONTEXT.md`）

---

## Step 4: 處理 `PROJECT_CONTEXT.md`

`PROJECT_CONTEXT.md` 是給 AI 智能體的「大腦同步檔」，**應保留在根目錄**。這讓任何 AI Agent 進入專案時能第一時間讀取全局狀態。

---

## Step 5: Git 初始化與首次 Commit

```bash
git init
git add .
git commit -m "docs: initialize project structure for GitHub"
```

**Commit message 慣例：**
- 結構性調整用 `docs:` 或 `chore:` prefix
- 功能實作用 `feat:` prefix
- 修復用 `fix:` prefix

---

## 驗證 Checklist

完成後逐項確認：

- [ ] `git status` 顯示 `working tree clean`
- [ ] 根目錄只有：`README.md`, `PROJECT_CONTEXT.md`, `requirements.txt`/`package.json`, `src/`, `tests/`, `scripts/`, `docs/`, `.agents/`
- [ ] `docs/` 根目錄沒有散落的「背景類」文件
- [ ] `.env`, `.venv/`, `.gemini/`, `.DS_Store` 皆未被追蹤
- [ ] `.agents/` 的 skills 和 workflows **有**被追蹤
