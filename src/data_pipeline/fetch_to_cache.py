"""
Stage 1: FETCH → JSON 快取
從 TDX 全國性 API 抓取資料，用 GPS Bounding Box 篩選大台北地區，存入本地 JSON。
此腳本只需執行一次，後續 Stage 2/3 可離線重複使用快取。
"""
import json, os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_pipeline.fetchers.tdx_api_fetcher import TDXFetcher

def main():
    print("🚀 Stage 1: FETCH → JSON 快取")
    tdx = TDXFetcher()
    all_pois = []

    # 1. 大台北景點 (台北 + 新北)
    print("📥 [1/4] 抓取大台北景點 (Taipei + NewTaipei)...")
    try:
        spots_tpe = tdx.fetch_scenic_spots(city="Taipei", top=2500)
        spots_ntpc = tdx.fetch_scenic_spots(city="NewTaipei", top=2500)
        for item in spots_tpe + spots_ntpc:
            all_pois.append(tdx.normalize_data(item, "ScenicSpot"))
        print(f"  └ ✅ 景點: {len(spots_tpe) + len(spots_ntpc)} 筆")
    except Exception as e:
        print(f"  └ ❌ 失敗: {e}")

    # 2. 大台北餐飲 (台北 + 新北)
    print("📥 [2/4] 抓取大台北餐飲 (Taipei + NewTaipei)...")
    try:
        foods_tpe = tdx.fetch_restaurants(city="Taipei", top=5000)
        foods_ntpc = tdx.fetch_restaurants(city="NewTaipei", top=5000)
        for item in foods_tpe + foods_ntpc:
            all_pois.append(tdx.normalize_data(item, "Restaurant"))
        print(f"  └ ✅ 餐飲: {len(foods_tpe) + len(foods_ntpc)} 筆")
    except Exception as e:
        print(f"  └ ❌ 失敗: {e}")

    # 3. 大台北活動 (台北 + 新北)
    print("📥 [3/4] 抓取大台北活動 (Taipei + NewTaipei)...")
    try:
        events_tpe = tdx.fetch_activities(city="Taipei", top=1000)
        events_ntpc = tdx.fetch_activities(city="NewTaipei", top=1000)
        for item in events_tpe + events_ntpc:
            all_pois.append(tdx.normalize_data(item, "Activity"))
        print(f"  └ ✅ 活動: {len(events_tpe) + len(events_ntpc)} 筆")
    except Exception as e:
        print(f"  └ ❌ 失敗: {e}")

    # 4. 大台北旅宿 (台北 + 新北)
    print("📥 [4/5] 抓取大台北旅宿 (Taipei + NewTaipei)...")
    try:
        hotels_tpe = tdx.fetch_hotels(city="Taipei", top=1000)
        hotels_ntpc = tdx.fetch_hotels(city="NewTaipei", top=1000)
        for item in hotels_tpe + hotels_ntpc:
            all_pois.append(tdx.normalize_data(item, "Hotel"))
        print(f"  └ ✅ 旅宿: {len(hotels_tpe) + len(hotels_ntpc)} 筆")
    except Exception as e:
        print(f"  └ ❌ 失敗: {e}")

    # 5. 台北捷運車站 (TRTC)
    print("📥 [5/5] 抓取台北捷運車站 (TRTC)...")
    try:
        mrt_stations = tdx.fetch_mrt_stations()
        for item in mrt_stations:
            all_pois.append(tdx.normalize_mrt_station(item, "TRTC"))
        print(f"  └ ✅ 捷運車站: {len(mrt_stations)} 筆")
    except Exception as e:
        print(f"  └ ❌ 失敗: {e}")

    # 6. 去重複 (Deduplication)
    seen = set()
    unique_pois = []
    for p in all_pois:
        if p["name"] not in seen:
            unique_pois.append(p)
            seen.add(p["name"])
    all_pois = unique_pois
    print(f"📥 去重後有效資料: {len(all_pois)} 筆")

    # 存入 JSON 快取
    os.makedirs("data_cache", exist_ok=True)
    cache_path = "data_cache/pois.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(all_pois, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Stage 1 完成！共 {len(all_pois)} 筆 POI 已存入 {cache_path}")
    
    # 分類統計
    from collections import Counter
    cats = Counter(p["category"] for p in all_pois)
    for cat, count in cats.most_common():
        print(f"  └ {cat}: {count} 筆")

if __name__ == "__main__":
    main()
