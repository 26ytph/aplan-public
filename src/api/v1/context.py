from fastapi import APIRouter, Query
from src.core.weather_service import WeatherService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(
    prefix="/context",
    tags=["Context"],
)

class WeatherResponse(BaseModel):
    temperature: Optional[float]
    condition: str
    code: Optional[int]
    precipitation_prob: Optional[int]
    display_text: str

weather_service = WeatherService()

@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
    lat: float = Query(..., description="緯度"),
    lng: float = Query(..., description="經度"),
    target_time: str = Query("現在", description="目標時間")
):
    """取得特定座標下的即時天氣預報 (Open-Meteo)"""
    data = await weather_service.get_weather(lat=lat, lng=lng, target_time=target_time)
    return WeatherResponse(**data)
