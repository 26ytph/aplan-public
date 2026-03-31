import time
import math
import httpx
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class UBikeService:
    _cache: List[Dict] = []
    _last_fetch_time: float = 0
    _cache_ttl: int = 60  # 60s TTL
    
    UBIKE_API_URL = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
    
    @classmethod
    async def fetch_stations(cls) -> List[Dict]:
        """抓取 YouBike 2.0 即時站點資料，包含 60 秒快取機制"""
        now = time.time()
        if cls._cache and (now - cls._last_fetch_time < cls._cache_ttl):
            return cls._cache
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(cls.UBIKE_API_URL, timeout=10.0)
                if response.status_code == 200:
                    cls._cache = response.json()
                    cls._last_fetch_time = now
                    logger.info(f"✅ UBike Cache Refreshed! Load {len(cls._cache)} stations.")
                else:
                    logger.warning(f"⚠️ UBike API failed with status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ UBike fetch error: {str(e)}")
            
        return cls._cache

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance in meters"""
        R = 6371000  # Radius of earth in meters
        phi_1 = math.radians(lat1)
        phi_2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2.0) ** 2 + \
            math.cos(phi_1) * math.cos(phi_2) * \
            math.sin(delta_lambda / 2.0) ** 2
            
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @classmethod
    async def find_nearest_station(cls, lat: float, lng: float, require_bikes: bool = False, require_docks: bool = False, max_distance_m: float = 1000) -> Optional[Dict]:
        """
        尋找距離指定座標最近且符合條件的站點。
        require_bikes=True: 必須有車可借 (sbi > 0)
        require_docks=True: 必須有位可還 (bemp > 0)
        max_distance_m: 最大搜尋半徑 (公尺)，預設 1000m (超過就不建議走了)
        """
        stations = await cls.fetch_stations()
        if not stations: return None
        
        nearest_station = None
        min_dist = float('inf')
        
        for st in stations:
            # 確保資料完整且為營業中 (act == "1")
            if 'latitude' not in st or 'longitude' not in st or str(st.get('act')) != "1":
                continue
                
            dist_m = cls.haversine(lat, lng, float(st['latitude']), float(st['longitude']))
            if dist_m > max_distance_m:
                continue
                
            bikes = int(st.get('available_rent_bikes', 0))
            docks = int(st.get('available_return_bikes', 0))
            
            if require_bikes and bikes < 1:
                continue
            if require_docks and docks < 1:
                continue
                
            if dist_m < min_dist:
                min_dist = dist_m
                nearest_station = dict(st) # 防止污染全域快取
                nearest_station['calculated_distance_m'] = int(dist_m)
                
        return nearest_station
