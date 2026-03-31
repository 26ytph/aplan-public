# GitHub 操作指南 (YTP Hackathon 2026 Edition)

> 本文件涵蓋從**主辦方建立 Organization**到**各隊伍日常開發**的完整 GitHub 操作流程。
> 適用對象：黑客松主辦方、各隊伍代表（Admin）、隊伍成員、AI Agent。

---

## 0. 架構總覽

```text
GitHub Organization: 26ytph
├── aplan        ← 隊伍 A 的獨立 Repo（隊伍代表 = Admin）
├── bplan        ← 隊伍 B 的獨立 Repo（隊伍代表 = Admin）
├── cplan        ← 隊伍 C 的獨立 Repo（隊伍代表 = Admin）
└── ...
```

**核心設計原則：**

| 原則 | 說明 |
|------|------|
| 一隊一 Repo | 各隊程式碼完全隔離，互不可見 |
| 代表為 Admin | 隊伍代表可自行管理成員與設定 |
| 主辦方為 Owner | 主辦方保留最高管理權，可檢視所有 Repo |

---

## 1. 主辦方操作指南 (Organization Owner)

### 1.1 建立 GitHub Organization

1. 點擊 GitHub 右上角頭像 → **Your organizations**
2. 點擊 **New organization** → 選擇 **Free（免費版）**
3. 命名組織（例如：`26ytph`）

### 1.2 為各隊伍建立 Repository

1. 在組織頁面點擊 **New repository**
2. 填入：
   - **Owner**：`26ytph`（組織名稱）
   - **Repository name**：隊伍名（如 `aplan`）
   - **Visibility**：`Private`（保護競賽公平性）
   - ⚠️ **不要**勾選 Initialize with README（隊伍自帶）
3. 點擊 **Create repository**

### 1.3 將隊伍代表設為 Admin

> [!IMPORTANT]
> 這是最關鍵的一步。只有在 **Organization 的 Repo 下**，才能指派 Collaborator 為 Admin。個人帳號下的 Repo 無法做到這一點。

1. 進入該隊伍的 Repo（例如 `26ytph/aplan`）
2. 點選 **Settings → Collaborators and teams**
3. 點擊 **Add people**，輸入隊伍代表的 GitHub 帳號
4. 在 **Role** 下拉選單中選擇 **Admin**

被設為 Admin 之後，隊伍代表就可以：
- ✅ 自行邀請組員（不需再經過主辦方）
- ✅ 將 Repo 設為 Private / Public
- ✅ 設定 Branch Protection Rules
- ✅ 管理 GitHub Topics

---

## 2. 隊伍代表操作指南 (Repository Admin)

### 2.1 接受邀請

收到主辦方的邀請 email 後，點擊連結接受邀請。

### 2.2 邀請組員

1. 進入 Repo → **Settings → Collaborators and teams**
2. 點擊 **Add people**
3. 輸入組員的 GitHub 帳號，權限選擇 **Write**

### 2.3 設定 GitHub Topics

1. 在 Repo 首頁右側「About」區塊，點擊 **⚙️ 齒輪圖示**
2. 在 Topics 欄位輸入標籤（每個輸入後按 Enter）：
   - `ytp-2026-hackathon`、`python`、`fastapi`、`ai`、`hackathon`
3. 點擊 **Save changes**

### 2.4 設定 Branch Protection Rules

1. 進入 **Settings → Branches**
2. 點擊 **Add branch ruleset** 或 **Add rule**
3. 設定：
   - **Branch name pattern**：`main`
   - ✅ Require a pull request before merging（建議）
   - ✅ Do not allow force pushes（防止覆蓋歷史）
4. 點擊 **Create**

### 2.5 調整 Repo 能見度 (Public / Private)

> [!CAUTION]
> 比賽期間強烈建議設為 **Private**，以保護競賽智慧財產權。

1. **Settings** → 捲動至最底部 **Danger Zone**
2. **Change repository visibility** → **Change to private**
3. 按照提示輸入 Repo 名稱確認

---

## 3. GitHub 認證設定 (Authentication)

> [!WARNING]
> GitHub 自 2021 年起**不再接受密碼推送**。必須使用以下方式之一。

### 3.1 方法 A：Personal Access Token (PAT) — 推薦快速上手

1. 前往 👉 **https://github.com/settings/tokens**
2. 點擊 **Generate new token → Generate new token (classic)**
3. 設定：
   - **Note**：`YTP Hackathon 2026`
   - **Expiration**：`90 days`（或到黑客松結束）
   - **Scopes**：✅ 勾選 **`repo`**（整個 repo 區塊）
4. 點擊 **Generate token** → **複製 Token**

> [!CAUTION]
> Token **只會顯示一次**！請立即複製並安全保存。
> 
> **必須使用 Classic Token**。Fine-grained Token 對 Organization Repo 的權限設定較為複雜，容易出現 `403: Write access not granted` 錯誤。

5. 執行 `git push` 時：
   - **Username**：你的 GitHub **帳號名稱**（如 `tctarng`，不是 email）
   - **Password**：貼上 **Token**（不是密碼）

### 3.2 方法 B：SSH Key — 推薦長期使用

```bash
# 1. 檢查是否已有 SSH Key
ls ~/.ssh/id_*.pub

# 2. 若沒有，產生新的
ssh-keygen -t ed25519 -C "your-email@example.com"

# 3. 複製公鑰
cat ~/.ssh/id_ed25519.pub | pbcopy

# 4. 前往 GitHub → Settings → SSH and GPG keys → New SSH key
#    貼上公鑰並儲存

# 5. 將 remote 改為 SSH 格式
git remote set-url origin git@github.com:26ytph/aplan.git
```

### 3.3 儲存認證（避免每次輸入）

```bash
# macOS：使用 Keychain 儲存
git config --global credential.helper osxkeychain

# 下次 push 時輸入的帳號與 Token 會被自動記住
```

---

## 4. 首次推送程式碼

### 4.1 連結本地專案至 GitHub

```bash
# 設定遠端（以 APlan 為例）
git remote add origin https://github.com/26ytph/aplan.git

# 推送 main 分支並設定上游追蹤
git push -u origin main
```

### 4.2 驗證

```bash
git remote -v
# 應顯示：
# origin  https://github.com/26ytph/aplan.git (fetch)
# origin  https://github.com/26ytph/aplan.git (push)
```

### 4.3 若需切換至新的 Remote

```bash
# 檢視目前的 remote
git remote -v

# 更改 remote URL（不需刪除再新增）
git remote set-url origin https://github.com/26ytph/aplan.git

# 重新推送
git push -u origin main
```

---

## 5. 日常開發流程

### 5.1 分支策略（精簡雙軌）

```text
main ─────────────────────────────────── (穩定版，Demo 用)
  └── feat/xxx ──── PR ──── merge ──┘   (功能開發)
  └── fix/xxx  ──── PR ──── merge ──┘   (緊急修復)
```

| 分支類型 | 命名規則 | 範例 |
|----------|----------|------|
| `main` | — | 永遠保持可 Demo 的穩定狀態 |
| `feat/*` | `feat/功能簡述` | `feat/voice-input` |
| `fix/*` | `fix/問題簡述` | `fix/toast-dismiss` |
| `docs/*` | `docs/文件簡述` | `docs/github-guide` |

> [!TIP]
> 黑客松期間若只有 1-2 人開發，可直接在 `main` 上 commit。多人協作時請開分支走 PR。

### 5.2 標準開發循環

```bash
# 1. 拉取最新程式碼
git pull origin main

# 2. 建立功能分支
git checkout -b feat/your-feature-name

# 3. 開發、測試、提交（遵循 Commit 規範）
git add .
git commit -m "feat(api): 實作某某功能"

# 4. 推送分支至 GitHub
git push -u origin feat/your-feature-name

# 5. 在 GitHub 建立 Pull Request → 請隊友 Review → Merge
```

### 5.3 合併後清理

```bash
git checkout main
git pull origin main
git branch -d feat/your-feature-name
```

---

## 6. Pull Request (PR) 指南

### 6.1 PR 標題格式

與 Commit 規範一致：`<type>(<scope>): <簡短描述>`

### 6.2 PR 描述模板

本 Repo 已內建 PR 模板（`.github/pull_request_template.md`），建立 PR 時會自動帶出。

### 6.3 Code Review 要點

| 面向 | 檢查項目 |
|------|----------|
| 功能 | 是否正確實現需求？邊界情況是否處理？ |
| 規範 | Commit 訊息格式、檔案位置是否符合 `PROJECT_CONTEXT.md`？ |
| 安全 | `.env` 或 API Key 是否不小心被提交？ |
| 文件 | 若變更了 API 或架構，相關文件是否同步更新？ |

---

## 7. 常用 Git 操作速查

```bash
# 查看狀態與歷史
git status
git log --oneline -10

# 暫存工作
git stash              # 暫存
git stash pop          # 取回

# 修改最後一次 commit 訊息（尚未 push 時）
git commit --amend -m "新的訊息"

# 處理衝突
git pull origin main   # 拉取 → 若有衝突，手動解決 → git add → git commit
```

---

## 8. 機敏資訊保護

> [!CAUTION]
> 每次提交前請額外確認：`git diff --cached --name-only | grep -E '\.env|secret'`

| 排除項目 | 原因 |
|---|---|
| `.env` | 包含 API Key |
| `test.db` / `*.sqlite` | 開發用暫存資料庫 |
| `.gemini/` | AI Agent 快取 |
| `.venv/` | 虛擬環境 |

| 應追蹤的特例 | 原因 |
|---|---|
| `.agents/skills/` | AI Skill 知識資產 |
| `.agents/workflows/` | 開發工作流程資產 |

---

## 9. AI 協作最佳實務

### 9.1 Phase 結束時務必提交

```bash
git add .
git commit -m "refactor: 完成 Phase II 重構，修復 3 項審計發現"
git push origin main
```

### 9.2 切換 AI 模型前（`/handoff`）

確保：所有變更已推送、`docs/journeys/` 有最新日誌、`PROJECT_CONTEXT.md` 已更新。

### 9.3 `.agents/` 目錄的版控

AI Skill 和 Workflow 是團隊知識資產，必須提交。

---

## 📚 延伸閱讀

| 文件 | 說明 |
|------|------|
| [GIT_COMMIT_GUIDE.md](GIT_COMMIT_GUIDE.md) | Commit 訊息撰寫標準 |
| [GIT_COMMIT_EXAMPLES.md](GIT_COMMIT_EXAMPLES.md) | 10+ 個情境式 Commit 範例 |
| [AI_PRODUCTIVITY_HANDBOOK.md](AI_PRODUCTIVITY_HANDBOOK.md) | AI 生產力、自動化技能庫與合作協定 |
| [PROJECT_CONTEXT.md](../../PROJECT_CONTEXT.md) | 專案全局上下文同步檔 |
