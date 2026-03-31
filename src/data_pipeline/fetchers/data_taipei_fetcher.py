import requests
import json
import logging
from typing import List, Dict, Any

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import time

class DataTaipeiFetcher:
    """擷取臺北旅遊網 Open API 的景點資料"""
    
    BASE_URL = "https://www.travel.taipei/open-api/zh-tw"

    def __init__(self):
        self.headers = {
            "Accept": "application/json"
        }

    def fetch_attractions(self, pages: int = 5) -> List[Dict[str, Any]]:
        """抓取臺北市景點 (支援多頁抓取並過濾有圖景點)"""
        all_data = []
        for page in range(1, pages + 1):
            url = f"{self.BASE_URL}/Attractions/All?page={page}"
            logger.info(f"正在抓取臺北市旅遊網景點資料 (Page {page}): {url}")
            
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"抓取臺北景點失敗 (Page {page}): {response.text}")
                continue
                
            json_data = response.json()
            data = json_data.get("data", [])
            if not data:
                break
                
            # 不再強迫過濾無圖片的景點，確保資料量最大化
            for item in data:
                all_data.append(item)
                
            time.sleep(1.5) # 友善請求，避免產生 429 Rate Limit Exceeded
            
        logger.info(f"成功取得共 {len(all_data)} 筆的臺北市在地景點資料。")
        return all_data

    def normalize_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """將臺北旅遊網資料正規化為我們要的 POI 格式"""
        
        # 處理圖片
        images = item.get("images", [])
        image_url = ""
        if images and hasattr(images, "__iter__") and len(images) > 0:
            image_url = images[0].get("src", "")
            
        if not image_url:
            image_url = "/static/images/fallback_poi.jpg"
            
        description = item.get("introduction", "")
        if not description:
            description = item.get("description", "")
            
        lat = 25.033
        lng = 121.565
        nlat = item.get("nlat")
        elong = item.get("elong")
        if nlat and elong:
            try:
                lat = float(nlat)
                lng = float(elong)
            except ValueError:
                pass
            
        return {
            "id": f"taipei_{item.get('id', '')}",
            "name": item.get("name", ""),
            "description": description[:200] + "..." if len(description) > 200 else description,
            "address": item.get("address", "台北市"),
            "image_url": image_url,
            "source": "DATA_TAIPEI",
            "category": "spot",
            "lat": lat,
            "lng": lng
        }

    def fetch_markets(self) -> List[Dict[str, Any]]:
        """[Phase 25] 抓取臺北市公有市場資料"""
        # 已知的 data.taipei 公有市場 rid
        market_rids = [
            "6a5246ec-ed0f-4886-ac9f-d31e97669d04",  # 公有零售市場行情
        ]
        
        # 備用方案：直接用臺北旅遊網 API 搜尋市場相關景點
        logger.info("正在抓取臺北市市場/商圈資料...")
        
        all_markets = []
        
        # 方案 A: 從旅遊網景點中過濾市場和商圈
        try:
            attractions = self.fetch_attractions(pages=10)
            for item in attractions:
                name = item.get('name', '')
                cat_str = ' '.join(item.get('category', []) if isinstance(item.get('category'), list) else [str(item.get('category', ''))])
                
                # 過濾市場和商圈相關
                is_market = any(k in name for k in ['市場', '商圈', '百貨', '購物', '商場', '名品', '廣場'])
                is_market = is_market or any(k in cat_str for k in ['購物', '市場', '商圈'])
                
                if is_market:
                    normalized = self.normalize_data(item)
                    normalized['category'] = 'shopping'
                    normalized['source'] = 'DataTaipei_Market'
                    all_markets.append(normalized)
        except Exception as e:
            logger.warning(f"從旅遊網過濾市場資料失敗: {e}")
        
        logger.info(f"成功取得 {len(all_markets)} 筆市場/商圈資料")
        return all_markets

if __name__ == "__main__":
    fetcher = DataTaipeiFetcher()
    # 測試連線與取得少量資料
    spots = fetcher.fetch_attractions(pages=1)
    if spots:
        print(json.dumps(fetcher.normalize_data(spots[0]), ensure_ascii=False, indent=2))
