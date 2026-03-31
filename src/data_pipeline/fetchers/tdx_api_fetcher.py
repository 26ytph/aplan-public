import os
import requests
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

class TDXFetcher:
    """擷取交通部 TDX 平台的觀光景點與餐飲資料"""
    
    AUTH_URL = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    BASE_URL = "https://tdx.transportdata.tw/api/basic"
    
    # 大台北 Bounding Box (含基隆、新北近郊)
    TAIPEI_BBOX = {"lat_min": 24.9, "lat_max": 25.22, "lon_min": 121.4, "lon_max": 121.7}

    def __init__(self):
        self.client_id = os.getenv("TDX_CLIENT_ID")
        self.client_secret = os.getenv("TDX_CLIENT_SECRET")
        self.token = None
        
        if not self.client_id or not self.client_secret:
            logger.warning("未設定 TDX_CLIENT_ID 或 TDX_CLIENT_SECRET，請確認 .env 檔案")

    def _get_token(self) -> str:
        """取得 TDX Bearer Token"""
        if self.token:
            return self.token
            
        logger.info("正在向 TDX 請求 Access Token...")
        data = {
            "content-type": "application/x-www-form-urlencoded",
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(self.AUTH_URL, data=data)
        if response.status_code != 200:
            logger.error(f"取得 Token 失敗: {response.text}")
            response.raise_for_status()
            
        self.token = response.json().get("access_token")
        logger.info("成功取得 TDX Access Token。")
        return self.token

    def _get_headers(self) -> Dict[str, str]:
        """產生 API 請求的 Headers"""
        token = self._get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

    def fetch_scenic_spots(self, city: str = "Taipei", top: int = 150) -> List[Dict[str, Any]]:
        """抓取指定縣市的景點資料 (包含無圖者)"""
        url = f"{self.BASE_URL}/v2/Tourism/ScenicSpot/{city}?$top={top}&$format=JSON"
        logger.info(f"正在抓取 {city} 景點資料: {url}")
        
        response = requests.get(url, headers=self._get_headers())
        if response.status_code != 200:
            logger.error(f"抓取景點失敗: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        logger.info(f"成功取得 {len(data)} 筆 {city} 景點資料。")
        return data

    def fetch_restaurants(self, city: str = "Taipei", top: int = 100) -> List[Dict[str, Any]]:
        """抓取指定縣市的餐飲資料 (包含無圖者)"""
        url = f"{self.BASE_URL}/v2/Tourism/Restaurant/{city}?$top={top}&$format=JSON"
        logger.info(f"正在抓取 {city} 餐飲資料: {url}")
        
        response = requests.get(url, headers=self._get_headers())
        if response.status_code != 200:
            logger.error(f"抓取餐飲失敗: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        logger.info(f"成功取得 {len(data)} 筆 {city} 餐飲資料。")
        return data

    def fetch_activities(self, city: str = "Taipei", top: int = 50) -> List[Dict[str, Any]]:
        """抓取指定縣市的活動資料 (包含無圖者)"""
        url = f"{self.BASE_URL}/v2/Tourism/Activity/{city}?$top={top}&$format=JSON"
        logger.info(f"正在抓取 {city} 活動資料: {url}")
        
        response = requests.get(url, headers=self._get_headers())
        if response.status_code != 200:
            logger.error(f"抓取活動失敗: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        logger.info(f"成功取得 {len(data)} 筆 {city} 活動資料。")
        return data

    def fetch_nationwide_restaurants(self, top: int = 5000) -> List[Dict[str, Any]]:
        """抓取全國餐飲資料，並用 GPS 過濾出大台北地區"""
        url = f"{self.BASE_URL}/v2/Tourism/Restaurant?$top={top}&$format=JSON"
        logger.info(f"正在抓取全國性餐飲資料 (top={top}): {url}")
        
        response = requests.get(url, headers=self._get_headers())
        if response.status_code != 200:
            logger.error(f"抓取全國餐飲失敗: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        taipei_data = self._filter_bbox(data)
        logger.info(f"全國餐飲 {len(data)} 筆，大台北篩選後: {len(taipei_data)} 筆")
        return taipei_data

    def fetch_nationwide_scenic_spots(self, top: int = 5000) -> List[Dict[str, Any]]:
        """抓取全國景點資料，並用 GPS 過濾出大台北地區"""
        url = f"{self.BASE_URL}/v2/Tourism/ScenicSpot?$top={top}&$format=JSON"
        logger.info(f"正在抓取全國性景點資料 (top={top}): {url}")
        
        response = requests.get(url, headers=self._get_headers())
        if response.status_code != 200:
            logger.error(f"抓取全國景點失敗: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        taipei_data = self._filter_bbox(data)
        logger.info(f"全國景點 {len(data)} 筆，大台北篩選後: {len(taipei_data)} 筆")
        return taipei_data

    def fetch_nationwide_activities(self, top: int = 5000) -> List[Dict[str, Any]]:
        """抓取全國活動資料，並用 GPS 過濾出大台北地區"""
        url = f"{self.BASE_URL}/v2/Tourism/Activity?$top={top}&$format=JSON"
        logger.info(f"正在抓取全國性活動資料 (top={top}): {url}")
        
        response = requests.get(url, headers=self._get_headers())
        if response.status_code != 200:
            logger.error(f"抓取全國活動失敗: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        taipei_data = self._filter_bbox(data)
        logger.info(f"全國活動 {len(data)} 筆，大台北篩選後: {len(taipei_data)} 筆")
        return taipei_data

    def _filter_bbox(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """用 Bounding Box 過濾出大台北地區的資料"""
        bb = self.TAIPEI_BBOX
        result = []
        for item in data:
            pos = item.get("Position", {})
            lat = pos.get("PositionLat", 0)
            lon = pos.get("PositionLon", 0)
            if bb["lat_min"] <= lat <= bb["lat_max"] and bb["lon_min"] <= lon <= bb["lon_max"]:
                result.append(item)
        return result

    def fetch_mrt_stations(self) -> List[Dict[str, Any]]:
        """抓取台北捷運所有車站資料"""
        url = f"{self.BASE_URL}/v2/Rail/Metro/Station/TRTC?$format=JSON"
        logger.info(f"正在抓取台北捷運車站資料: {url}")
        
        response = requests.get(url, headers=self._get_headers())
        if response.status_code != 200:
            logger.error(f"抓取捷運車站失敗: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        logger.info(f"成功取得 {len(data)} 筆台北捷運車站資料。")
        return data

    def fetch_hotels(self, city: str = "Taipei", top: int = 100) -> List[Dict[str, Any]]:
        """抓取指定縣市的旅宿資料 (包含無圖者)"""
        url = f"{self.BASE_URL}/v2/Tourism/Hotel/{city}?$top={top}&$format=JSON"
        logger.info(f"正在抓取 {city} 旅宿資料: {url}")
        
        response = requests.get(url, headers=self._get_headers())
        if response.status_code != 200:
            logger.error(f"抓取旅宿失敗: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        logger.info(f"成功取得 {len(data)} 筆 {city} 旅宿資料。")
        return data

    def fetch_mrt_stations(self, operator: str = "TRTC") -> List[Dict[str, Any]]:
        """抓取捷運站資料 (TRTC=台北捷運, KRTC=高雄捷運, TYMC=桃園捷運, TMRT=台中捷運)"""
        url = f"{self.BASE_URL}/v2/Rail/Metro/Station/{operator}?$format=JSON"
        logger.info(f"正在抓取 {operator} 捷運站資料: {url}")
        
        response = requests.get(url, headers=self._get_headers())
        if response.status_code != 200:
            logger.error(f"抓取 {operator} 捷運站失敗: {response.text}")
            response.raise_for_status()
            
        data = response.json()
        logger.info(f"成功取得 {len(data)} 筆 {operator} 捷運站資料。")
        return data

    def normalize_data(self, item: Dict[str, Any], category: str) -> Dict[str, Any]:
        """將 TDX 原始資料正規化為我們先前定義的 POI 格式"""
        
        position = item.get("Position", {})
        lat = position.get("PositionLat", 25.033)
        lng = position.get("PositionLon", 121.565)
        
        # 嘗試提取圖片與敘述
        picture = item.get("Picture", {})
        image_url = picture.get("PictureUrl1", "")
        if not image_url:
            # Fallback 圖片：優先使用 Google Static Maps, 否則 OpenStreetMap
            google_key = os.getenv("GOOGLE_MAPS_API_KEY")
            if google_key:
                image_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=16&size=600x400&markers=color:red%7C{lat},{lng}&key={google_key}"
            else:
                image_url = f"https://staticmap.openstreetmap.de/staticmap.php?center={lat},{lng}&zoom=15&size=600x400&markers={lat},{lng},red-pushpin"
            
        description = item.get("DescriptionDetail") or item.get("Description") or item.get("City", "")
        
        return {
            "id": f"tdx_{item.get(f'{category}ID', item.get('ID', ''))}",
            "name": item.get(f"{category}Name", item.get("Name", "")),
            "description": description[:200] + "..." if len(description) > 200 else description,
            "address": item.get("Address", "台北市"),
            "image_url": image_url,
            "source": "TDX_API",
            "category": "spot" if category == "ScenicSpot" else "food" if category == "Restaurant" else "hotel" if category == "Hotel" else "event",
            "lat": lat,
            "lng": lng
        }

    def normalize_mrt_station(self, item: Dict[str, Any], operator: str = "TRTC") -> Dict[str, Any]:
        """將捷運站資料正規化為 POI 格式"""
        station_id = item.get("StationID", "")
        station_name_zh = item.get("StationName", {}).get("Zh_tw", "")
        
        # 建立前綴
        prefix_map = {
            "TRTC": "台北捷運",
            "KRTC": "高雄捷運",
            "TYMC": "桃園捷運",
            "TMRT": "台中捷運"
        }
        prefix = prefix_map.get(operator, "捷運")
        
        position = item.get("StationPosition", {})
        lat = position.get("PositionLat", 25.033)
        lng = position.get("PositionLon", 121.565)
        
        # 使用捷運/火車意象的圖作為佔位符
        mrt_placeholder = "https://images.unsplash.com/photo-1548681531-97b7cb780826?auto=format&fit=crop&q=80&w=800"
        
        return {
            "id": f"tdx_mrt_{operator.lower()}_{station_id}",
            "name": f"捷運{station_name_zh}站",
            "description": f"{prefix} {station_id} 站",
            "address": item.get("StationAddress", "地址未提供"),
            "image_url": mrt_placeholder,
            "source": "TDX_API",
            "category": "spot", # 將其視為一個景點以利被導航或被推薦
            "lat": lat,
            "lng": lng
        }

if __name__ == "__main__":
    fetcher = TDXFetcher()
    # 測試連線與取得少量資料
    spots = fetcher.fetch_scenic_spots(top=1)
    if spots:
        print(json.dumps(fetcher.normalize_data(spots[0], "ScenicSpot"), ensure_ascii=False, indent=2))
