# 臺北時光機 · Taipei Time Machine

> 用一句自然語言，探索臺北的日與夜。

臺北時光機是一套 AI 驅動的台北旅遊推薦系統。拋棄死板的下拉選單，用語音或文字告訴它你現在的心情與需求，它會結合你的 GPS 位置、即時天氣和時間，推薦最適合的下一站，並自動附上最近的 YouBike 借還點。

**核心資料已隨 repo 提供**（2,367 筆精選台北景點的向量庫 + SQLite 資料庫），clone 後不需要跑資料爬蟲，幾分鐘內即可啟動。

---

## 功能特色

- **語音 / 文字輸入**：「下雨天想找室內小吃」→ 自動解析意圖並推薦
- **即時情境感知**：GPS 定位 + 即時天氣 + 24 小時時間輪盤，自動帶入當下背景
- **語意向量檢索**：2,367 筆台北精選景點（米其林餐廳、國家景點、百貨商圈、捷運站周邊）
- **YouBike 微交通**：即時顯示最近可借 / 可還站點
- **多語言輸出**：繁中 / English / 日本語 / 한국어 / ภาษาไทย

---

## 系統需求

- **Python 3.10+**
- **[Google Gemini API Key](https://aistudio.google.com/app/apikey)**（免費方案即可）

---

## 快速開始

### 1. Clone 專案

```bash
git clone https://github.com/26ytph/aplan-public.git
cd aplan-public
```

### 2. 安裝依賴套件

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows：.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 設定 API Key

```bash
cp .env.example .env
```

用任何文字編輯器開啟 `.env`，將 `your_gemini_api_key_here` 替換為你的 Gemini API Key：

```
GEMINI_API_KEY=AIza...（你的 Key）
```

### 4. 啟動伺服器

```bash
./scripts/start_server.sh
```

> **Windows 使用者：** 改執行 `python -m uvicorn src.main:app --host 0.0.0.0 --port 8000`

### 5. 開啟瀏覽器

前往 **http://127.0.0.1:8000**，開始探索台北！

### 停止伺服器

```bash
./scripts/stop_server.sh
```

> 請務必使用此腳本停止伺服器，以正確釋放 ChromaDB 資料庫鎖定。

---

## 使用說明

1. **選擇時間**：調整右側時間輪盤，或讓系統自動偵測現在時刻
2. **開啟定位**：點選 GPS 按鈕，授權後系統會取得你的所在位置與即時天氣
3. **描述需求**：在輸入框打字，或點選麥克風圖示用語音輸入
   - 例：「晚上想找安靜的咖啡廳坐一下」
   - 例：「現在下雨，找個室內景點」
   - 例：「帶朋友吃台式小吃」
4. **查看推薦**：系統回傳 2–3 個景點卡片，含推薦理由與 YouBike 站點資訊

---

## 專案結構

```
aplan-public/
├── src/
│   ├── api/v1/            # FastAPI 路由端點
│   ├── core/              # 推薦引擎、向量檢索器、天氣服務
│   ├── data_pipeline/     # ETL 資料管道（選用，資料已預建）
│   ├── templates/         # 前端 HTML（Jinja2）
│   └── utils/             # LLM Adapter（支援多模型切換）
├── scripts/               # 啟動 / 停止腳本
├── .gemini/chroma_db/     # 預建向量庫（ChromaDB，2,367 筆景點）
├── test.db                # 預建關聯資料庫（SQLite）
├── .env.example           # 環境變數範本
└── docs/                  # 架構設計文件、開發日誌
```

---

## 技術架構

| 層次 | 技術 |
|------|------|
| 前端 | HTML5 + Vanilla JavaScript + Tailwind CSS |
| 後端 | Python 3.10 / FastAPI / Uvicorn |
| 向量庫 | ChromaDB（768 維 Gemini Text Embedding） |
| 關聯庫 | SQLite（非同步 aiosqlite） |
| LLM | Google Gemini API（gemini-3.1-flash-lite-preview） |
| 天氣 | Open-Meteo（免費，無需認證） |
| 微交通 | YouBike 2.0 即時 Azure Blob 端點 |

---

## 常見問題

**Q：啟動時出現 `GEMINI_API_KEY` 相關錯誤？**
請確認 `.env` 檔案中已填入有效的 Gemini API Key，且不含多餘的空白或引號。

**Q：Port 8000 已被佔用？**
修改 `.env` 中的 `PORT=8000` 為其他埠號（例如 `8080`），重新啟動即可。

**Q：想要更新景點資料？**
可以選擇性執行資料管道腳本重新抓取最新資料：
```bash
PYTHONPATH=. python3 src/data_pipeline/fetch_to_cache.py   # 從 TDX API 抓取
PYTHONPATH=. python3 src/data_pipeline/load_to_sqlite.py   # 載入 SQLite
PYTHONPATH=. python3 src/data_pipeline/embed_incremental.py # 重建向量庫
```

---

*Built by Team Antigravity · 2026 YTP Hackathon*
