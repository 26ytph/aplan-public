import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.api.v1.services.ubike import UBikeService

async def debug():
    stations = await UBikeService.fetch_stations()
    print("Stations count:", len(stations))
    if len(stations) > 0:
        print("First station:", stations[0])

if __name__ == '__main__':
    asyncio.run(debug())
