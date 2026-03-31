"""
Phase 25: OSM Shopping Fetcher
抓取台北市 OpenStreetMap 的購物類 POI (百貨/商場/超市/生活百貨/傳統市場)
不含便利商店(由經濟部 CSV 負責)和服飾店(暫不收)。
"""
import requests
import json
import logging
import time
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# 要抓的購物類別 (排除 convenience 和 clothes)
SHOPPING_TAGS = {
    "department_store": {"label": "百貨公司", "emoji": "🏬"},
    "mall":             {"label": "購物中心", "emoji": "🛒"},
    "supermarket":      {"label": "超市",     "emoji": "🥬"},
    "variety_store":    {"label": "生活百貨", "emoji": "🎁"},
}

MARKETPLACE_TAG = {"label": "傳統市場", "emoji": "🏪"}


def fetch_osm_shopping() -> List[Dict[str, Any]]:
    """一次性抓取台北市所有購物 POI (Overpass API)"""
    
    # 組合 shop tags
    shop_filters = "|".join(SHOPPING_TAGS.keys())
    
    query = f"""
    [out:json][timeout:120];
    area["name"="臺北市"]->.taipei;
    (
      nwr["shop"~"^({shop_filters})$"](area.taipei);
      nwr["amenity"="marketplace"](area.taipei);
    );
    out center;
    """
    
    logger.info(f"🔍 正在從 OSM 抓取台北市購物類 POI...")
    logger.info(f"  查詢標籤: shop={shop_filters} + amenity=marketplace")
    
    try:
        response = requests.post(OVERPASS_URL, data={'data': query}, timeout=180)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"❌ Overpass API 請求失敗: {e}")
        return []
    
    data = response.json()
    elements = data.get('elements', [])
    logger.info(f"  └ 取得 {len(elements)} 筆原始元素")
    
    pois = []
    for el in elements:
        tags = el.get('tags', {})
        name = tags.get('name')
        if not name:
            continue  # 排除無名店面
        
        lat = el.get('lat') or el.get('center', {}).get('lat')
        lon = el.get('lon') or el.get('center', {}).get('lon')
        if not lat or not lon:
            continue
        
        # 判斷是 shop 還是 marketplace
        shop_type = tags.get('shop', '')
        is_marketplace = tags.get('amenity') == 'marketplace'
        
        if is_marketplace:
            meta = MARKETPLACE_TAG
            sub_category = "marketplace"
        elif shop_type in SHOPPING_TAGS:
            meta = SHOPPING_TAGS[shop_type]
            sub_category = shop_type
        else:
            continue
        
        # 組裝地址
        addr_parts = [
            tags.get('addr:city', '台北市'),
            tags.get('addr:district', ''),
            tags.get('addr:street', ''),
            tags.get('addr:housenumber', ''),
        ]
        address = ''.join(p for p in addr_parts if p)
        if not address or address == '台北市':
            address = f"台北市 (OSM ID: {el['id']})"
        
        # 品牌/連鎖名稱
        brand = tags.get('brand', '')
        name_display = f"{brand} {name}" if brand and brand not in name else name
        
        pois.append({
            "name": name_display.strip(),
            "category": "shopping",
            "description": f"{meta['emoji']} {meta['label']}。{tags.get('description', '')}".strip(),
            "address": address,
            "lat": lat,
            "lng": lon,
            "image_url": "",
            "source": f"OSM_Shopping_{sub_category}",
        })
    
    logger.info(f"✅ 正規化後取得 {len(pois)} 筆購物 POI (已排除無名店面)")
    
    # 統計
    by_source = {}
    for p in pois:
        src = p['source']
        by_source[src] = by_source.get(src, 0) + 1
    for src, cnt in sorted(by_source.items()):
        logger.info(f"  └ {src}: {cnt} 筆")
    
    return pois


if __name__ == "__main__":
    results = fetch_osm_shopping()
    print(f"\n共 {len(results)} 筆")
    if results:
        print(json.dumps(results[:3], ensure_ascii=False, indent=2))
