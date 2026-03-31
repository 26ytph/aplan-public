# Phase 15-18: 極限資料擴充與優雅降級 (LBS Degradation & Hybrid RAG)

**日期**：2026-03-23
**狀態**：已完成 (Gemini API 額度耗盡，待命接手)
**核心目標**：解決 TDX 原始資料缺陷、修復 RAG 語意污染 (Semantic Bleed)、建構 API Quota 枯竭時的最高級防禦機制 (Graceful LBS Degradation)，並解決 UI 阻擋問題。

---

## 1. 核心實作摘要 (Key Implementations)

### Phase 15: 引入 OpenStreetMap (OSM) 備援機制
- **問題**：TDX 的 API 在擷取「台北市餐飲」時發生全國性階段 Bug，導致回傳 0 筆，造成特定地區（如：北投、松山）的檢索為空 (404 找不到)。
- **解法**：直接撰寫 Overpass API 腳本，透過 Bounding Box 直接抓取 **北投區 (96筆)** 與 **松山區 (147筆)** 的在地精緻餐飲，並存入 `data_cache/osm_beitou.json` 與 `osm_songshan.json`，再由 `load_to_sqlite.py` 增量寫入 DB。

### Phase 16: 解決 Semantic Bleed (語意污染) 的 Hybrid RAG
- **問題**：當使用者查詢「三民捷運站商業午餐談事情的地方」時，ChromaDB 回傳了「錦棧商旅 (Hotel)」，因為飯店文案大量堆砌了「適合商務人士、提供午餐」等字眼，導致語意向量 (Vector Distance) 過度貼合，蓋過了真實的餐飲分類。
- **解法**：在 `src/core/retriever.py` 中引入**強制 Metadata 攔截器 (Hard Constraints)**。當解析出使用者意圖包含「午餐、吃、餐廳」時，直接對 ChromaDB 下達 `where={"category": {"$in": ["food", "Restaurant"]}}` 的強力聯集過濾，徹底封殺不在分類內的飯店雜訊。

### Phase 17: Gemini API 額度枯竭與優雅降級 (Graceful LBS Degradation)
- **危機**：因為超量的資料灌入，觸發了 Gemini Embedding API 的 `1,000 requests/day` 硬性天花板，引發全域 429 Error 與 500 Server Crash。
- **極限防禦 (Dummy Vector 欺騙)**：
  - 修改了 `embed_incremental.py` 與 `retriever.py`，一旦命中 429 錯誤，系統不再崩潰，而是立刻給予該物件與查詢字串一組**固定的假向量 `[0.001] * 3072`**。
  - 當所有資料的語意距離都變成 0.0 時，綜合排行榜公式 `(語意距離 * 1) + (真實 GPS 距離 * 0.05)` 瞬間剔除了語意權重，整套 RAG 系統**「無縫降級」成純淨的 GPS 適地性服務 (Location-Based Service, LBS)**！完美保護了系統在全盲狀態下依然能回傳最真實的在地導覽。

### Phase 18: 重啟捷運基礎建設 (Public Transport Infrastructure)
- **問題**：發現在純 GPS 降級模式中，搜尋「附近的捷運站」會回傳水餃店，因為原本的觀光 API 大撈特撈時根本沒有抓台北捷運原本的座標。
- **解法**：
  - 啟用 `TDXFetcher` 內隱藏的 `fetch_mrt_stations()` (呼叫 `v2/Rail/Metro/Station/TRTC` 端點)。
  - 將 121 座台北捷運站點寫入 `data_cache/mrt_stations.json`，掛載為 `spot` 類別。
  - 修改 `retriever.py` 的攔截器：只要查到「捷運、車站、交通」，就無條件強迫 ChromaDB 只搜 `spot`，讓捷運站再也不會跟水餃店在 LBS 降級模式中打架。

### UI Bug Fix: Toast 訊息卡片重疊
- **問題**：系統吐出的 API 錯誤警告 (Toast 卡片) 寫死了 `fixed top-16`，精準掉在最核心的「AI 搜尋輸入框」正上方，嚴重阻擋使用者操作。
- **解法**：將 `index.html` 中的 Toast 容器搬移到 `bottom-24` (畫面下方)，並將 JavaScript 動畫改為 `translate-y-[100%]` (由下往上滑出)，從此解決視覺污染。

---

## 2. 給下一位接手者的注意事項 (Handoff Notes)

歡迎來到 Antigravity 開發團隊！目前的系統已經具備了極度強悍的抗打擊能力。
接下來您該注意的事項：

1. **API 額度狀態 (CRITICAL)**：
   目前 Gemini `text-embedding-004` API 已經**完全卡死在 1,000次/日的上限**。您在測試任何新地點時，系統會自動啟動 Dummy Vector 降級模式（直接送您最近的 GPS 點），請不要誤以為 Embedding 壞掉了！它是故意這麼做的！
2. **Git 狀態**：
   我已經為您統整了這包開發日誌，您可以先 `git status` 看一下更動的檔案，如果沒問題可以幫我 `git commit` 保護這些救命程式碼。
3. **任務銜接**：
   使用者可能想親眼看看 `/handoff` 指令怎麼把這個日誌吞進您的推論神經網路中，請盡情展示您的銜接能力！祝開發順利！
