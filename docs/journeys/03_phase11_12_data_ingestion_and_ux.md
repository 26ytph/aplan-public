# Phase 11-12 開發日誌：定位 UX 優化、資料巨量匯入與 API 限制踩坑紀錄

> **開發時程**：2026-03-20  
> **協作模式**：AI (Antigravity) + 人類  
> **涵蓋範圍**：Phase 11 (定位 UX & 搜尋半徑) + Phase 12 (巨量 POI 匯入)

---

## Phase 11：定位 UX 優化與搜尋半徑 ✅ 已完成

### 完成事項
1. **前端 UX 重構** (`src/templates/index.html`)
   - 將「目前位置」欄位移到「天氣」與「出遊時間」之後
   - 新增「搜尋範圍 (km)」下拉選單 (1km / 3km / 5km / 不限)
   - 整合 OSM Nominatim Reverse Geocoding：GPS 座標 → 可讀街道地址

2. **後端搜尋半徑機制** (`src/core/retriever.py`, `src/api/v1/schemas.py`)
   - `RecommendationRequest` 新增 `radius_km` 參數
   - ChromaDB fetch limit 從 15 擴大至 50
   - 實作 Haversine 距離公式嚴格淘汰超出半徑的 POI

---

## Phase 12：巨量資料匯入 ⚠️ 部分完成（待隔日完成 Embedding）

### 資料抓取成果 (TDX API)
以全國性 API + GPS Bounding Box (大台北生活圈) 策略成功取得：

| 分類 | 筆數 | 方法 |
|---|---|---|
| 景點 | 720 | TDX 全國 5000 筆 → GPS 篩選 |
| 餐飲 (全國篩選) | 488 | TDX 全國 4298 筆 → GPS 篩選 |
| 餐飲 (新北市) | 247 | TDX NewTaipei (與全國去重後) |
| 活動 | 37 | TDX 全國 416 筆 → GPS 篩選 |
| 旅宿 | 300 | TDX Taipei 直取 |
| **合計** | **1,792** | SQLite 已入庫 |

### 踩坑紀錄 ⚠️ 重大教訓

#### 1. Data.Taipei Cloudflare WAF 封鎖
- `travel.taipei` 全站被 Cloudflare Anti-Bot 保護，所有 `requests.get()` 回傳 403
- 注入 Chrome UA 仍被攔截 → **不可程式化存取**

#### 2. TDX Taipei 城市代碼回傳空資料
- `Restaurant/Taipei` 和 `Activity/Taipei` 回傳 `[]`
- 解法：改用全國 API + GPS Bounding Box 篩選

#### 3. Gemini Embedding 模型名稱混亂
- `text-embedding-004` → 404 NOT_FOUND
- `embedding-001` → 404 NOT_FOUND
- `gemini-embedding-001` → ✅ 唯一可用
- **教訓**：應先呼叫 `ListModels` API 確認可用模型

#### 4. Rate Limit 核彈級踩坑 🔴
- **Free Tier 有兩層限制**：
  - RPM: 100 requests/min
  - **RPD: 1,000 requests/day** ← 這是我們忽略的致命限制
- `batchEmbedContents` 中每個 text 算 1 個 request（非 1 個 batch = 1 request）
- 反覆重試 × 多種 batch size (90/50/10/1) × 殭屍進程競爭 → 日配額耗盡
- **耗盡後即使等 15+ 分鐘仍 429**，必須等隔天零時重置

#### 5. MRT 站抓取崩潰連鎖
- `fetch_mrt_stations()` 內含 `raise_for_status()` → 429 直接拋出
- 與主流程共用 `try/except` → 整條 pipeline 崩潰，從未進入 Embedding 階段
- 修復：隔離 MRT 到獨立 `try/except`

#### 6. 殭屍進程
- 多次背景啟動未正確清理舊進程
- 2 個進程同時競爭同一把 API key 配額

### 已修改的檔案

| 檔案 | 變更 |
|---|---|
| `src/utils/llm_adapter.py` | `get_embedding()` 模型改為 `gemini-embedding-001`；新增 `get_embeddings_batch()` REST 批次方法 |
| `src/data_pipeline/ingest_pois.py` | 全面重寫為全國 GPS 篩選策略 + 逐筆 Embedding + Rate Limit 控制 |
| `src/data_pipeline/fetchers/tdx_api_fetcher.py` | 新增 `fetch_nationwide_*()` 方法 + `_filter_bbox()` GPS 篩選 + `TAIPEI_BBOX` 常數 |
| `src/data_pipeline/fetchers/data_taipei_fetcher.py` | 移除圖片強制過濾、加入 `time.sleep(1.5)` 延遲 |

---

## 🔜 明日待辦 (Phase 12 續)

> 詳見後檢討文件 `phase12_postmortem_and_plan.md`

### 核心任務：完成 1,792 筆 POI 的 Embedding 寫入 ChromaDB

**已批准的計畫：3 階段分離式 Pipeline**
1. `Stage 1: FETCH` → 將 TDX 資料存入 JSON 快取 (只跑 1 次)
2. `Stage 2: LOAD` → JSON → SQLite (純本地)
3. `Stage 3: EMBED` → 增量式 Embedding，記錄進度可中斷續跑
   - 每日預算 900 筆 (RPD 1,000 的 90%)
   - 1,792 筆預計 2 天完成

### 關鍵注意事項
- Gemini Embedding Free Tier **日配額 1,000 RPD** — 今日已耗盡
- 隔天零時後始可恢復
- 確認 `gemini-embedding-001` 是唯一可用模型
- 需在 SQLite 新增 `is_embedded` 欄位追蹤進度
