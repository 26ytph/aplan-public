import asyncio
from src.api.v1.services.ubike import UBikeService

async def debug():
    stations = await UBikeService.fetch_stations()
    print("Stations count:", len(stations))
    if len(stations) > 0:
        print("First station:", stations[0])

asyncio.run(debug())
