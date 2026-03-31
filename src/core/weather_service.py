import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WeatherService:
    """提供基於經緯度的天氣查詢 (使用免授權的 Open-Meteo API 備案)"""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Open-Meteo WMO Weather interpretation codes
    WEATHER_CODE_MAP = {
        0: "晴朗無雲",
        1: "晴時多雲", 2: "多雲", 3: "陰天",
        45: "有霧", 48: "有霧",
        51: "毛毛雨", 53: "小雨", 55: "中雨",
        56: "凍雨", 57: "凍雨",
        61: "微雨", 63: "中雨", 65: "大雨",
        66: "凍雨", 67: "大凍雨",
        71: "小雪", 73: "中雪", 75: "大雪",
        77: "雪粒",
        80: "微陣雨", 81: "中陣雨", 82: "大雷陣雨",
        85: "小陣雪", 86: "大陣雪",
        95: "雷雨",
        96: "雷陣雨夾冰雹", 99: "大雷陣雨夾冰雹"
    }

    async def get_weather(self, lat: float, lng: float, target_time: Optional[str] = "現在") -> Dict[str, Any]:
        """
        取得天氣。
        target_time 可為 "現在"，或是 "今日 15:00"、"明日 10:00" 等格式。
        """
        try:
            # 為了拿到未來 24 小時的預報，我們請求 hourly data
            params = {
                "latitude": lat,
                "longitude": lng,
                "current_weather": "true",
                "hourly": "temperature_2m,precipitation_probability,weathercode",
                "timezone": "Asia/Taipei",
                "forecast_days": 2
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.BASE_URL, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
            
            # 若為「現在」，直接回傳 current_weather
            if not target_time or target_time == "現在" or target_time.lower() == "now":
                cw = data.get("current_weather", {})
                code = cw.get("weathercode", 0)
                temp = cw.get("temperature", 20)
                desc = self.WEATHER_CODE_MAP.get(code, "未知天氣")
                
                return {
                    "temperature": temp,
                    "condition": desc,
                    "code": code,
                    "precipitation_prob": None,
                    "display_text": f"{desc} ({temp}°C)"
                }
                
            # 解析 target_time (格式例如: "今日 15:00")
            # 由於 Open-Meteo 的 hourly.time 是 ISO 格式 ("2023-10-25T15:00")
            # 我們需要把中文時間對應到陣列索引
            now = datetime.now()
            hours_offset = 0
            
            try:
                # 簡單的時數差計算
                parts = target_time.split(" ")
                if len(parts) == 2:
                    day_str = parts[0]
                    time_str = parts[1]
                    target_hour = int(time_str.split(":")[0])
                    
                    if day_str == "今日":
                        hours_offset = target_hour - now.hour
                    elif day_str == "明日":
                        hours_offset = (24 - now.hour) + target_hour
                        
                    # 確保在合理範圍內 (0 ~ 47)
                    if hours_offset < 0:
                        hours_offset = 0
                    elif hours_offset >= len(data["hourly"]["time"]):
                        hours_offset = len(data["hourly"]["time"]) - 1
            except Exception as parse_e:
                logger.warning(f"解析時間 '{target_time}' 失敗，回退至目前天氣: {parse_e}")
                hours_offset = 0

            # 提取對應的小時預報
            hourly = data.get("hourly", {})
            
            # Open-Meteo index 0 剛好是今天的 00:00，所以不能直接用 hours_offset 當 index
            # 取出 current hour 在陣列中的確切 index
            current_time_str = data["current_weather"]["time"] # e.g. "2023-10-25T11:00"
            try:
                current_idx = hourly["time"].index(current_time_str)
            except ValueError:
                current_idx = 0
                
            target_idx = current_idx + hours_offset
            if target_idx >= len(hourly["time"]):
                target_idx = len(hourly["time"]) - 1
                
            code = hourly["weathercode"][target_idx]
            temp = hourly["temperature_2m"][target_idx]
            precip = hourly["precipitation_probability"][target_idx]
            desc = self.WEATHER_CODE_MAP.get(code, "未知天氣")
            
            # 組裝友善字串
            display_text = f"{desc} ({temp}°C)"
            if precip and precip > 20:
                display_text += f" 💧降雨率{precip}%"
                
            return {
                "temperature": temp,
                "condition": desc,
                "code": code,
                "precipitation_prob": precip,
                "display_text": display_text
            }
                
        except Exception as e:
            logger.error(f"取得天氣預報失敗: {e}")
            return {
                "temperature": None,
                "condition": "無法取得天氣",
                "code": None,
                "precipitation_prob": None,
                "display_text": "無法取得天氣"
            }

