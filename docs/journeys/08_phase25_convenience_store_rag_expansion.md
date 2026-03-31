# 開發日誌 08: Phase 25.1 購物類 POI 整合與經濟部資料救援
日期: 2026-03-27

## 1. 任務目標 (Objective)
擴充台北市購物類資料，重點包含便利商店 (7-11, 全家, 萊爾富, OK) 與連鎖超市 (全聯)。填補先前 POI 資料集中「生活採買」類別的空缺。

## 2. 核心技術挑戰 (Technical Challenges)
* **API 失效**：經濟部商工行政 API 長期處於 500 錯誤狀態，無法直接線上抓取最新分店資料。
* **地理編碼難點**：原始資料地址包含「樓層」、「地下室」、「里名」等資訊，直接丟給 Nominatim 會導致 100% 失敗率。
* **速率限制**：Nominatim 嚴格限制一秒一次請求，大批次地理編碼需要完善的快取機制。

## 3. 解決方案與實作 (Solutions)
### 3.1 來源切換 (Fetcher Refactoring)
* 定義 `moea_convenience_fetcher.py`，支援讀取使用者提供的本地 `全國5大超商資料集.csv`。
* 實作品牌過濾邏輯（過濾公司名稱與分公司狀態）。

### 3.2 地址清洗 (Regex Cleaning)
* 引入正則表達式剔除干擾項：
  - `re.sub(r'號.*$', '號', address)`：移除號碼後的樓層資訊。
  - `re.sub(r'..里', '', clean_addr)`：移除里名。
* 此舉將地理編碼成功率從 ~0% 提升至 **95% 以上**。

### 3.3 快取機制 (Geocoding Cache)
* 實作 `data_cache/geocoding_cache.json`。
* 避免重複查詢同一地址，節省 API 配額並加速後續 Ingestion。

## 4. 執行成果 (Results)
* **Ingestion**: 完成首批 228 筆 MOEA 資料處理（64 筆 7-11, 164 筆全聯）。
* **Database**: `test.db` 新增 209 筆 POI（排除重複），總量達 **16,063** 筆。
* **Vectorization**: 完成 `embed_incremental.py` 指令，將新 POI 全部寫入 ChromaDB 向量庫。
* **Export**: 生成 [moea_convenience_export_20260327.xlsx](file:///Users/ytp-thomas/Desktop/APlan/moea_convenience_export_20260327.xlsx) 供人工審閱。

## 5. 待辦事項 (Pending Items)
* [ ] 其餘約 1,600 筆台北市超商資料可分批完成地理編碼。
* [ ] 考慮加入百貨公司與傳統市場的資料（DataTaipei 來源）。
