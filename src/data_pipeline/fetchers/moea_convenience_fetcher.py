"""
Phase 25: 經濟部商工行政 — 五大超商 CSV Fetcher
下載全國五大超商分公司登記 CSV，篩選台北市，並用 Nominatim 批次地理編碼。
來源: https://data.gcis.nat.gov.tw (經濟部商業發展署)
"""
import csv
import io
import logging
import time
import requests
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
import json

# 五大超商的公司統編 (用於 CSV 過濾)
CONVENIENCE_BRANDS = {
    "統一超商": "7-ELEVEN",
    "全家便利商店": "全家 FamilyMart",
    "萊爾富": "萊爾富 Hi-Life",
    "來來超商": "OK超商",  # OK mart 的公司名
    "全聯實業": "全聯福利中心",
}

# 經濟部商工 5大超商 CSV 直接下載 URL
CSV_URL = "https://data.gcis.nat.gov.tw/od/file?oid=9D17AE56-B8A4-4F51-9D93-A8C5B5A557E5"
CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data_cache", "geocoding_cache.json")


def _load_cache() -> Dict[str, List[float]]:
    """載入地理編碼快取"""
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"⚠️ 快取載入失敗: {e}")
    return {}


def _save_cache(cache: Dict[str, List[float]]):
    """儲存地理編碼快取"""
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    try:
        with open(CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"⚠️ 快取儲存失敗: {e}")


def fetch_moea_convenience(geocode: bool = True, local_csv_path: str = None, limit: int = None) -> List[Dict[str, Any]]:
    """讀取經濟部五大超商資料，篩選台北市，並地理編碼"""
    
    taipei_stores = []
    total_rows = 0
    
    if local_csv_path and os.path.exists(local_csv_path):
        logger.info(f"📂 正在讀取本地 CSV: {local_csv_path}...")
        try:
            with open(local_csv_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"❌ 本地 CSV 讀取失敗: {e}")
            return []
    else:
        logger.info("🔍 正在下載經濟部商工五大超商 CSV...")
        try:
            response = requests.get(CSV_URL, timeout=60)
            response.raise_for_status()
            content = response.content.decode('utf-8-sig')
        except Exception as e:
            logger.error(f"❌ CSV 下載失敗: {e}")
            return []
    
    # 解析 CSV
    reader = csv.DictReader(io.StringIO(content))
    
    for row in reader:
        total_rows += 1
        address = row.get('分公司地址', '') or row.get('地址', '') or ''
        company_name = row.get('公司名稱', '') or ''
        branch_name = row.get('分公司名稱', '') or row.get('名稱', '') or ''
        status = row.get('分公司狀態', '') or row.get('狀態', '') or ''
        
        # 篩選邏輯：台北市 + 核准設立 (01)
        if '台北市' not in address and '臺北市' not in address:
            continue
        if status and status != '01' and '核准設立' not in status:
            continue
        if not branch_name or branch_name.strip() == "":
            continue
        
        # 判斷品牌
        brand = None
        for key, display_name in CONVENIENCE_BRANDS.items():
            if key in company_name:
                brand = display_name
                break
        
        if not brand:
            continue
        
        taipei_stores.append({
            "name": branch_name.strip(),
            "brand": brand,
            "address": address.strip(),
        })
    
    logger.info(f"  └ 共 {total_rows} 筆，篩選台北市有效門市: {len(taipei_stores)} 筆")
    
    # 地理編碼
    pois = []
    cache = _load_cache()
    
    if geocode:
        process_count = limit if limit else len(taipei_stores)
        logger.info(f"📍 開始地理編碼 (預計處理 {process_count} 筆)...")
        
        geocoded = 0
        from_cache = 0
        failed = 0
        
        for i, store in enumerate(taipei_stores):
            if limit and i >= limit:
                break
                
            addr = store['address']
            lat, lng = None, None
            
            # 先查快取
            if addr in cache:
                lat, lng = cache[addr]
                from_cache += 1
            else:
                lat, lng = _geocode_address(addr)
                if lat and lng:
                    cache[addr] = [lat, lng]
                    geocoded += 1
                    # 每 10 筆存一次快取
                    if geocoded % 10 == 0:
                        _save_cache(cache)
                    # Nominatim 限速
                    time.sleep(1.1)
                else:
                    failed += 1
            
            if lat and lng:
                pois.append({
                    "name": store['name'],
                    "category": "convenience" if "全聯" not in store['brand'] else "shopping",
                    "description": f"🏪 {store['brand']}。地址：{store['address']}",
                    "address": store['address'],
                    "lat": lat,
                    "lng": lng,
                    "image_url": "",
                    "source": f"MOEA_{store['brand'].split()[0]}",
                })
            
            if (i + 1) % 50 == 0:
                logger.info(f"  └ 進度 {i+1}/{process_count} (快取: {from_cache}, 新編碼: {geocoded}, 失敗: {failed})")
        
        _save_cache(cache)
    else:
        # 不做地理編碼
        for store in taipei_stores[:limit] if limit else taipei_stores:
            pois.append({
                "name": store['name'],
                "category": "convenience" if "全聯" not in store['brand'] else "shopping",
                "description": f"🏪 {store['brand']}。地址：{store['address']}",
                "address": store['address'],
                "lat": 0,
                "lng": 0,
                "image_url": "",
                "source": f"MOEA_{store['brand'].split()[0]}",
            })
    
    logger.info(f"✅ 完成: 產出 {len(pois)} 筆 POI")
    return pois


import re

def _geocode_address(address: str) -> tuple:
    """用 Nominatim 地理編碼單一地址，包含地址清洗邏輯"""
    
    # 清洗邏輯 1: 移除「號」之後的所有內容 (樓層、地下室等)
    clean_addr = re.sub(r'號.*$', '號', address)
    
    # 清洗邏輯 2: 移除「里」 (Nominatim 有時不認得社區/里名)
    clean_addr = re.sub(r'..里', '', clean_addr)
    
    try:
        # 嘗試 1: 清洗後的地址
        lat, lng = _query_nominatim(clean_addr)
        if lat: return lat, lng
        
        # 嘗試 2: 如果失敗，嘗試原始地址
        lat, lng = _query_nominatim(address)
        if lat: return lat, lng
        
        # 嘗試 3: 再更簡略，移除「路/街」之後的所有內容 (保險方案)
        brief_addr = re.sub(r'(路|街|大道).*$', r'\1', clean_addr)
        if brief_addr != clean_addr:
             lat, lng = _query_nominatim(brief_addr)
             if lat: return lat, lng

    except Exception as e:
        logger.error(f"⚠️ Geocoding 發生異常: {e}")
        
    return None, None


def _query_nominatim(q: str) -> tuple:
    """實際發送 Nominatim 請求"""
    try:
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': q, 'format': 'json', 'limit': 1, 'countrycodes': 'tw'},
            headers={'User-Agent': 'TaipeiTimeMachine/1.1'},
            timeout=10
        )
        if response.ok:
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception:
        pass
    return None, None


if __name__ == "__main__":
    import json
    # 先不做 geocoding，只看篩選結果
    results = fetch_moea_convenience(geocode=False)
    print(f"\n共 {len(results)} 筆")
    if results:
        print(json.dumps(results[:5], ensure_ascii=False, indent=2))
