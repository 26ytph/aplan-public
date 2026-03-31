import asyncio
import sys
import os

# Add the project root to sys.path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.v1.services.ubike import UBikeService

async def main():
    print("Fetching YouBike stations...")
    stations = await UBikeService.fetch_stations()
    print(f"Total stations in cache: {len(stations)}")
    
    # 測試台北101附近 (25.033964, 121.564468)
    lat, lng = 25.033964, 121.564468
    print(f"\nTesting near Taipei 101 ({lat}, {lng}):")
    
    nearest_bikes = await UBikeService.find_nearest_station(lat, lng, require_bikes=True)
    if nearest_bikes:
        print(f"Nearest with bikes: {nearest_bikes.get('sna', '')} (Dist: {nearest_bikes['calculated_distance_m']}m, Bikes: {nearest_bikes.get('available_rent_bikes', 0)})")
    
    nearest_docks = await UBikeService.find_nearest_station(lat, lng, require_docks=True)
    if nearest_docks:
        print(f"Nearest with docks: {nearest_docks.get('sna', '')} (Dist: {nearest_docks['calculated_distance_m']}m, Empty Docks: {nearest_docks.get('available_return_bikes', 0)})")

if __name__ == "__main__":
    asyncio.run(main())
