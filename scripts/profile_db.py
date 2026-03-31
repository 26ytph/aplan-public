import asyncio
import os
import time
from src.core.config import get_settings
from src.db.vector_store import VectorDBRepository
from src.utils.llm_adapter import get_llm_adapter

async def profile_query():
    print("--- DB Sizing ---")
    settings = get_settings()
    sqlite_size = os.path.getsize(settings.db_path) / (1024 * 1024)
    chroma_size = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                     for dirpath, _, filenames in os.walk("./.gemini/chroma_db") 
                     for filename in filenames) / (1024 * 1024)
    print(f"SQLite Size: {sqlite_size:.2f} MB")
    print(f"ChromaDB Size: {chroma_size:.2f} MB")

    print("\n--- ChromaDB Query Profiling (100 runs) ---")
    adapter = get_llm_adapter("gemini")
    query_text = "台北車站附近的平價美食"
    try:
        emb = await adapter.get_embedding(query_text)
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return

    repo = VectorDBRepository()
    latencies = []
    
    # warmup
    _ = await repo.query_pois(emb, n_results=5)
    
    for _ in range(100):
        start = time.perf_counter()
        _ = await repo.query_pois(emb, n_results=5)
        latencies.append((time.perf_counter() - start) * 1000)
    
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)
    print(f"Average: {avg_latency:.2f} ms")
    print(f"Min: {min_latency:.2f} ms")
    print(f"Max: {max_latency:.2f} ms")
    
if __name__ == "__main__":
    asyncio.run(profile_query())
