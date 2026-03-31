import asyncio
from src.db.vector_store import VectorDBRepository

async def debug():
    vdb = VectorDBRepository()
    # 查詢 "頤宮"
    results = vdb.poi_collection.get(where={"name": "頤宮 Le Palais (君品酒店)"})
    print(f"Results for 頤宮: {results}")
    
    # 查詢近期的推薦結果
    query_text = "必吃的餐廳"
    from src.utils.llm_adapter import get_llm_adapter
    adapter = get_llm_adapter("gemini")
    emb = await adapter.get_embedding(query_text)
    
    results = await vdb.query_pois(query_embedding=emb, n_results=10)
    print("\nTop 10 raw Chroma results for '必吃的餐廳':")
    for res in results:
        print(f"- {res['metadata'].get('name')} (ID: {res['metadata'].get('poi_id')})")

if __name__ == "__main__":
    asyncio.run(debug())
