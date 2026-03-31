import asyncio
import os
import sys
import json
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.repository import DatabaseRepository
from src.db.vector_store import VectorDBRepository
from src.utils.llm_adapter import get_llm_adapter
from src.data_pipeline.fetchers.ptt_fetcher import PTTFetcher

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def clean_and_extract_trend(llm, article_text: str, poi_name: str) -> dict:
    """使用 Gemini 將生肉 PTT 文章洗理成結構化的社群趨勢摘要"""
    
    prompt = f"""
    # 任務設定
    你現在是一個社群輿情分析師，要替我們萃取 PTT 文章中關於「{poi_name}」的討論精華。
    
    # PTT 文章原文
    {article_text}
    
    # 產生要求
    請總結這篇文章中網友對「{poi_name}」的看法。如果文章並非在討論此景點，請根據內文推敲出一個最接近的在地體驗趨勢。
    1. content 必須是一句繁體中文摘要 (不超過 50 字)，必須生動口語，例如：「假日人太多了要排隊一小時，但風景真的很美✨」。
    2. sentiment 必須是 "positive", "neutral", 或 "negative" 其中之一。
    
    # 輸出格式
    嚴格輸出合法的 JSON，不要其他文字。格式如下：
    {{
      "content": "摘要內容",
      "sentiment": "positive"
    }}
    """
    
    try:
        response_text = await llm.generate_content(prompt)
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        logger.warning(f"Gemini 萃取失敗: {e}")
        return None

async def ingest_real_social_trends():
    """主程序：針對資料庫中的 POI，去 PTT 爬取對應文章並用 Gemini 清洗後寫入資料庫"""
    print("🚀 開始執行 [真實社群趨勢] 萃取與導入作業...")
    
    sqlite_repo = DatabaseRepository()
    chroma_repo = VectorDBRepository()
    llm = get_llm_adapter("gemini")
    ptt = PTTFetcher()
    
    print("⏳ 從 SQLite 讀取 POIs...")
    all_pois = await sqlite_repo.get_all_pois()
    if not all_pois:
        print("沒有找到景點資料，請先執行 load_to_sqlite.py (Phase 12 Pipeline)")
        return
        
    # 為了避免 API Limit 與時間過久，我們只取部分 POI 來示範火力展示
    # 抽取有代表性的 10 筆
    target_pois = all_pois[:10]
    
    ids = []
    documents = []
    embeddings = []
    metadatas = []
    
    for count, poi in enumerate(target_pois):
        print(f"\n[{count+1}/{len(target_pois)}] 正在處理: {poi['name']}")
        
        # 決定針對哪個看板搜尋
        board = "Food" if poi["category"] in ["夜間美食", "food", "Restaurant"] else "Taipei"
        
        # 使用第一段短名稱作為關鍵字 (避免過長的官方名稱搜不到)
        query_keyword = poi['name'].split("_")[0].split("(")[0].strip()
        
        articles = ptt.search_articles(board=board, query=query_keyword, limit=2)
        
        # 如果找不到，就隨機找當前看板最新文章當成「周邊新聞」
        if not articles:
            logger.info(f"未搜到 {query_keyword} 的精準文章，改爬最新熱門文章...")
            articles = ptt.fetch_articles(board=board, pages=1)[:2]
            
        for art in articles:
            raw_text = ptt.normalize_data(art)
            print(f"  └ 正在讓 Gemini 閱讀並清洗文章: {art['title'][:15]}...")
            
            trend_data = await clean_and_extract_trend(llm, raw_text, poi['name'])
            if not trend_data:
                continue
                
            try:
                # 寫入 SQLite
                sql_id = await sqlite_repo.insert_social_trend(
                    poi_id=poi['id'],
                    content=trend_data["content"],
                    sentiment=trend_data["sentiment"],
                    platform="PTT"
                )
                
                # 準備寫入 ChromaDB
                doc_text = f"在 {board} 板上關於「{poi['name']}」的討論：{trend_data['content']}"
                emb = await llm.get_embedding(doc_text)
                
                ids.append(f"trend_{sql_id}")
                documents.append(doc_text)
                embeddings.append(emb)
                metadatas.append({
                    "trend_id": sql_id,
                    "poi_id": poi['id'],
                    "sentiment": trend_data["sentiment"],
                    "platform": "PTT"
                })
                print(f"    └ ✅ 成功寫入: [{trend_data['sentiment']}] {trend_data['content']}")
                
            except Exception as e:
                print(f"    └ ❌ 寫入資料庫失敗: {e}")
                
            await asyncio.sleep(2) # 延遲避免 API 限流

    # 批次寫入 ChromaDB Vector Store
    if ids:
        print(f"\n🧠 正在將 {len(ids)} 筆清洗後的社群趨勢寫入 ChromaDB...")
        await chroma_repo.upsert_social_trends(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        print("🎉 真實 PTT 社群趨勢資料導入完成！")
    else:
        print("\n⚠️ 沒有成功清洗任何文章資料。")

if __name__ == "__main__":
    asyncio.run(ingest_real_social_trends())
