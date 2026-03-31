# 系統流程圖 (Process Flows)

本文件展示了「臺北時光機」最核心的 **魔法連動 (Agentic UI) 與 Semantic RAG 推薦流程**。

## 核心互動循序圖 (Sequence Diagram)

這個流程展示了使用者對著手機說出一句話後，系統如何在幾秒鐘內完成「意圖理解、介面自動填寫、語意融合檢索、LLM 創意生成」的完整迴圈。

```mermaid
sequenceDiagram
    autonumber
    
    actor User as 使用者
    participant Browser as 前端介面 (Browser)
    participant API as FastAPI Server
    participant Gemini as Gemini API (Flash-Lite / Embed)
    participant Chroma as ChromaDB (向量庫)
    participant SQLite as SQLite (關聯庫)

    User->>Browser: "語音/文字：『明早九點，天氣晴朗時，郊外踏青的地方』"
    
    Browser->>API: "POST /api/v1/parse-intent"
    
    API->>Gemini: "萃取【天氣】【時間】與對應【探索標籤(如: nature)】"
    Gemini-->>API: "回傳 Structured JSON (Intent)"
    
    API-->>Browser: "回傳已解析的 Intent"
    Note over Browser: 自動在畫面上勾選『自然探索』標籤與『明早』時間
    
    Browser->>API: "POST /api/v1/fast-recommend/ (傳送座標、半徑、原始語意與標籤)"
    
    Note over API, SQLite: 雙軌混合檢索與排序 (Hybrid Retrieval)
    
    API->>Gemini: "將 raw_intent (郊外踏青) 送去 Embeddings"
    Gemini-->>API: "回傳 768 維度語意向量"
    
    API->>Chroma: "Cosine Similarity 語意相似度搜尋"
    Chroma-->>API: "回傳初步候選名單與語意距離"
    
    API->>SQLite: "地理 Bounding Box & 分類過濾 (如: park, nature)"
    SQLite-->>API: "回傳實體景點 (包含 Tier 星級與經緯度)"
    
    Note over API: 執行 LBS 關鍵字補償 (如: "踏青" -> 語意加分)<br/>計算最終權重: 語意 * 1.0 + 距離處罰 * 0.2 + (Tier 加分)
    
    API->>Gemini: "推薦引擎：融合景點資訊 + 使用者情境，生成專屬導覽文案"
    Gemini-->>API: "回傳 RecommendationResponse (JSON)"
    
    API-->>Browser: "回傳最終推薦結果"
    Browser-->>User: "呈現專屬客製化行程與地圖連結"
```

## 流程設計亮點說明
1. **自動化 UI 更新 (Step 4-7)**：捨棄傳統「使用者填完表單才按下搜尋」的模式。系統會主動理解語意，幫使用者「畫面上」勾選好選項後，才交給後端處理，提供極佳的視覺反饋。
2. **混合檢索與權重 (Hybrid Retrieval)**：雖然前端幫忙勾選了「自然探索」，但後端真正在搜尋資料庫時，會直接拿使用者的原始語句（例如：郊外踏青）做 ChromaDB 的向量對比，並且在 SQLite 回傳資料後施加「Tier 菁英優待」以及「0.2公里的距離處罰折扣」，確保優質的遠方景點能擊敗普通的近身景點。
