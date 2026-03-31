"""
Phase 25: 購物類 POI 資料攝取總控腳本
整合 3 個來源 (OSM, 經濟部, data.taipei) → 去重 → 寫入 SQLite
"""
import os
import sys
import asyncio
import json
import math
import logging

# 加入專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.repository import DatabaseRepository

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2):
    """計算兩個 GPS 座標之間的距離 (公尺)"""
    R = 6371000  # 地球半徑 (公尺)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def deduplicate_pois(pois, distance_threshold=50):
    """去重：名稱相同且距離 < threshold 公尺的視為同一 POI"""
    unique = []
    for poi in pois:
        is_dup = False
        for existing in unique:
            if poi['name'] == existing['name']:
                if poi['lat'] > 0 and existing['lat'] > 0:
                    dist = haversine_distance(poi['lat'], poi['lng'], existing['lat'], existing['lng'])
                    if dist < distance_threshold:
                        is_dup = True
                        break
                elif poi['address'] == existing['address']:
                    is_dup = True
                    break
        if not is_dup:
            unique.append(poi)
    return unique


async def ingest_shopping(skip_moea_geocoding=False, local_csv_path=None, moea_limit=None):
    """主流程：抓取 → 去重 → 寫入 SQLite"""
    
    all_pois = []
    
    # 來源 1: OSM Shopping (省略日後執行)
    # 來源 2: DataTaipei (省略日後執行)
    
    # ===== 來源 3: 經濟部商工 5大超商 =====
    logger.info("=" * 60)
    logger.info("📦 來源: 經濟部商工 (五大超商 CSV)")
    logger.info("=" * 60)
    try:
        from src.data_pipeline.fetchers.moea_convenience_fetcher import fetch_moea_convenience
        moea_pois = fetch_moea_convenience(
            geocode=not skip_moea_geocoding, 
            local_csv_path=local_csv_path,
            limit=moea_limit
        )
        all_pois.extend(moea_pois)
        logger.info(f"  ✅ 經濟部: {len(moea_pois)} 筆")
    except Exception as e:
        logger.error(f"  ❌ 經濟部 失敗: {e}")
        import traceback
        traceback.print_exc()
    
    # ===== 去重 =====
    logger.info("=" * 60)
    logger.info(f"🔄 去重處理 (原始: {len(all_pois)} 筆)")
    unique_pois = deduplicate_pois(all_pois)
    logger.info(f"  └ 去重後: {len(unique_pois)} 筆 (移除 {len(all_pois) - len(unique_pois)} 筆重複)")
    
    # ===== 寫入 SQLite =====
    logger.info("=" * 60)
    logger.info("💾 寫入 SQLite...")
    
    repo = DatabaseRepository()
    await repo.init_db()
    
    inserted = 0
    skipped = 0
    for poi in unique_pois:
        try:
            await repo.insert_poi(
                name=poi['name'],
                category=poi['category'],
                description=poi.get('description', ''),
                lat=poi['lat'],
                lng=poi['lng'],
                address=poi.get('address', '台北市'),
                image_url=poi.get('image_url', ''),
                source=poi['source']
            )
            inserted += 1
        except Exception:
            skipped += 1  # 重複名稱
    
    # ===== 報告 =====
    logger.info("=" * 60)
    logger.info(f"🎉 經濟部資料攝取完成！")
    logger.info(f"  └ 新增: {inserted} 筆")
    logger.info(f"  └ 跳過 (已存在): {skipped} 筆")
    logger.info(f"  └ 接下來請執行: python -m src.data_pipeline.embed_incremental")
    
    return inserted


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Phase 25.1: 經濟部超商資料攝取')
    parser.add_argument('--skip-geocoding', action='store_true', help='跳過地理編碼')
    parser.add_argument('--csv', type=str, default='全國5大超商資料集.csv', help='本地 CSV 路徑')
    parser.add_argument('--limit', type=int, default=200, help='地理編碼筆數上限 (預設 200)')
    args = parser.parse_args()
    
    asyncio.run(ingest_shopping(
        skip_moea_geocoding=args.skip_geocoding,
        local_csv_path=args.csv,
        moea_limit=args.limit
    ))
