import asyncio
import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any

class VectorDBRepository:
    """
    ChromaDB 向量資料庫存取層。
    負責管理景點與社群貼文的 Embedding，以支援語意檢索 (Semantic Search)。
    """
    def __init__(self):
        # 初始化 Persistent Client，將資料儲存於本地專案目錄下
        self.db_path = "./.gemini/chroma_db"
        
        # 確保路徑存在
        os.makedirs(self.db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 取得或建立 Collections
        # 使用 cosine distance 作為相似度計算標準
        self.poi_collection = self.client.get_or_create_collection(
            name="poi_collection",
            metadata={"hnsw:space": "cosine"}
        )
        self.social_trends_collection = self.client.get_or_create_collection(
            name="social_trends_collection",
            metadata={"hnsw:space": "cosine"}
        )

    # === POI (Points of Interest) 操作 ===

    async def upsert_pois(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict[str, Any]]):
        """
        批次寫入或更新 POI 的向量資料。
        使用 asyncio.to_thread 避免同步磁碟 I/O 阻塞事件循環。
        """
        await asyncio.to_thread(
            self.poi_collection.upsert,
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    async def count_pois(self) -> int:
        """回傳 POI collection 中的向量數量"""
        return await asyncio.to_thread(self.poi_collection.count)

    async def query_pois(self, query_embedding: List[float], n_results: int = 5, where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        根據輸入的向量，找出最相似的 POI。可選用 where 進行 Metadata 過濾。
        使用 asyncio.to_thread 避免同步磁碟 I/O 阻塞事件循環。
        """
        results = await asyncio.to_thread(
            self.poi_collection.query,
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        # 將 ChromaDB 回傳的複雜結構轉為 List of Dict 方便後續使用
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                doc = {
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else None
                }
                formatted_results.append(doc)
                
        return formatted_results

    # === Social Trends (社群動態) 操作 ===

    async def upsert_social_trends(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict[str, Any]]):
        """
        批次寫入或更新社群貼文的向量資料。
        使用 asyncio.to_thread 避免同步磁碟 I/O 阻塞事件循環。
        """
        await asyncio.to_thread(
            self.social_trends_collection.upsert,
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    async def query_social_trends(self, query_embedding: List[float], n_results: int = 5, where: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        根據輸入的向量，找出最相似的社群貼文。
        使用 asyncio.to_thread 避免同步磁碟 I/O 阻塞事件循環。
        """
        results = await asyncio.to_thread(
            self.social_trends_collection.query,
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                doc = {
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else None
                }
                formatted_results.append(doc)
                
        return formatted_results
