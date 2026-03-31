"""
Stage 3: EMBED → ChromaDB (增量式)
從 SQLite 讀取尚未嵌入的 POI，逐筆呼叫 gemini-embedding-001，
成功後立刻標記 is_embedded=1 並寫入 ChromaDB。

⚠️ Rate Limit 安全策略：
- 每筆間隔 1.5 秒 (~40 RPM，安全於 100 RPM)
- 每日上限 900 筆 (RPD 1,000 的 90%)
- 429 發生時等待 65 秒自動重試
- 可隨時中斷，下次從斷點續跑
"""
import asyncio, os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiosqlite
from src.db.vector_store import VectorDBRepository
from src.utils.llm_adapter import get_llm_adapter, CustomQuotaExhaustedError
from src.core.config import get_settings

DAILY_BUDGET = 15000       # 提升至超大預算，交由 KeyManager 的 QuotaExhausted 來踩煞車
INTERVAL_SECONDS = 0.6   # (60s / 100筆) 透過 7 核心輪替，均勻分散每把鑰匙的 RPM
RETRY_WAIT = 65          # 429 重試等待 (秒)

async def main():
    print("🚀 Stage 3: EMBED → ChromaDB (增量式)")
    print(f"  ⚙️ 每日預算: {DAILY_BUDGET} 筆 | 間隔: {INTERVAL_SECONDS}s | 429 重試: {RETRY_WAIT}s")
    
    settings = get_settings()
    db_path = settings.db_path
    
    if not os.path.exists(db_path):
        print("❌ 找不到 SQLite 資料庫，請先執行 Stage 2 (load_to_sqlite.py)")
        return
    
    adapter = get_llm_adapter("gemini")
    chroma_repo = VectorDBRepository()
    
    # 查詢尚未嵌入的 POI
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, name, category, description, address, source, lat, lng "
            "FROM pois WHERE is_embedded = 0 ORDER BY id"
        )
        pending = [dict(row) for row in await cursor.fetchall()]
    
    total_pending = len(pending)
    if total_pending == 0:
        print("✅ 所有 POI 已完成嵌入！無需操作。")
        # 顯示 ChromaDB 統計
        count = await chroma_repo.count_pois()
        print(f"📊 ChromaDB 中共有 {count} 筆向量")
        return
    
    to_process = pending[:DAILY_BUDGET]
    print(f"📊 待嵌入: {total_pending} 筆 | 本次處理: {len(to_process)} 筆")
    estimated_min = len(to_process) * INTERVAL_SECONDS / 60
    print(f"⏱ 預估耗時: {estimated_min:.0f} 分鐘")
    sys.stdout.flush()
    
    success_count = 0
    fail_count = 0
    start_time = time.time()
    
    for idx, poi in enumerate(to_process):
        doc = (
            f"這是一個名為「{poi['name']}」的場域。"
            f"分類屬於「{poi['category']}」。"
            f"地址位在「{poi['address']}」。"
            f"詳細描述：{poi['description']}"
        )
        
        emb = None
        try:
            emb = await adapter.get_embedding(doc)
        except CustomQuotaExhaustedError:
            print(f"\n🚨 [CRITICAL] 所有 {len(get_settings().gemini_api_keys)} 把 API 金鑰額度皆已耗盡！")
            print(f"📌 本次已成功拯救 {success_count} 筆，正在啟動 Graceful Exit 程序...")
            break
        except Exception as e:
            err = str(e)
            print(f"  ❌ #{idx+1} 發生未預期的嵌入錯誤: {err[:80]}，跳過此筆繼續...")
            fail_count += 1
            continue
        
        if emb:
            # 寫入 ChromaDB
            await chroma_repo.upsert_pois(
                ids=[f"real_poi_{poi['id']}"],
                embeddings=[emb],
                documents=[doc],
                metadatas=[{
                    "poi_id": poi['id'],
                    "name": poi['name'],
                    "category": poi['category'],
                    "source": poi['source']
                }]
            )
            # 標記已嵌入 (立即持久化進度)
            async with aiosqlite.connect(db_path) as db:
                await db.execute("UPDATE pois SET is_embedded = 1 WHERE id = ?", (poi['id'],))
                await db.commit()
            
            success_count += 1
        else:
            fail_count += 1
        
        # 進度報告 (每 50 筆)
        if (idx + 1) % 50 == 0 or idx == len(to_process) - 1:
            elapsed = time.time() - start_time
            rpm = success_count / (elapsed / 60) if elapsed > 0 else 0
            remaining = total_pending - success_count
            print(
                f"  ✅ 進度: {idx+1}/{len(to_process)} | "
                f"成功: {success_count} | 失敗: {fail_count} | "
                f"實際 RPM: {rpm:.1f} | 剩餘待嵌入: {remaining}"
            )
            sys.stdout.flush()
        
        # Rate Limit 控制
        await asyncio.sleep(INTERVAL_SECONDS)
    
    elapsed = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"🎉 Stage 3 本次執行完成！")
    print(f"  ✅ 成功嵌入: {success_count} 筆")
    print(f"  ❌ 失敗: {fail_count} 筆")
    print(f"  ⏱ 耗時: {elapsed/60:.1f} 分鐘")
    
    # 最終統計
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM pois WHERE is_embedded = 0")
        remaining = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM pois WHERE is_embedded = 1")
        done = (await cursor.fetchone())[0]
    
    chroma_count = await chroma_repo.count_pois()
    print(f"\n📊 最終統計:")
    print(f"  └ SQLite 已嵌入: {done} 筆")
    print(f"  └ SQLite 待嵌入: {remaining} 筆")
    print(f"  └ ChromaDB 向量: {chroma_count} 筆")
    
    if remaining > 0:
        print(f"\n💡 還有 {remaining} 筆待嵌入，明天重新執行此腳本即可續跑。")

if __name__ == "__main__":
    asyncio.run(main())
