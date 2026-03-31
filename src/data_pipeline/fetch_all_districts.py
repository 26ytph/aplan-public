import requests
import json
import os
import time

def fetch_district_data(district_name):
    print(f"🔍 正在抓取 {district_name} 的餐廳與咖啡廳資料...")
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:60];
    area["name"="臺北市"]->.city;
    area["name"="{district_name}"](area.city)->.district;
    (
      node["amenity"~"restaurant|cafe"](area.district);
      way["amenity"~"restaurant|cafe"](area.district);
    );
    out center;
    """
    
    response = requests.post(overpass_url, data={'data': overpass_query})
    if response.status_code != 200:
        print(f"❌ 抓取 {district_name} 失敗: {response.status_code}")
        return []
    
    data = response.json()
    elements = data.get('elements', [])
    
    pois = []
    for el in elements:
        tags = el.get('tags', {})
        name = tags.get('name')
        if not name: continue
        
        lat = el.get('lat') or el.get('center', {}).get('lat')
        lon = el.get('lon') or el.get('center', {}).get('lon')
        
        pois.append({
            "id": f"osm_{el['id']}",
            "name": name,
            "category": "food",
            "description": f"位於{district_name}的{tags.get('amenity', '餐廳/咖啡廳')}。OSM 標籤: {tags.get('cuisine', '特色美食')}",
            "address": f"台北市{district_name}{tags.get('addr:street', '')}{tags.get('addr:housenumber', '')}",
            "lat": lat,
            "lng": lon,
            "source": f"OSM_{district_name}"
        })
    
    print(f"  └ ✅ 成功取得 {len(pois)} 筆資料")
    return pois

def main():
    districts = [
        "中正區", "大同區", "中山區", "松山區", "大安區", 
        "萬華區", "信義區", "士林區", "北投區", "內湖區", 
        "南港區", "文山區"
    ]
    
    output_dir = "data_cache/districts"
    os.makedirs(output_dir, exist_ok=True)
    
    all_count = 0
    for dist in districts:
        filename = f"{output_dir}/osm_{dist}.json"
        
        # 抓取資料
        dist_pois = fetch_district_data(dist)
        if dist_pois:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(dist_pois, f, ensure_ascii=False, indent=2)
            all_count += len(dist_pois)
        
        # 禮貌性延遲，避免 Overpass API 封鎖
        time.sleep(2)
    
    print(f"\n✨ 任務完成！共抓取 {len(districts)} 個行政區，總計 {all_count} 筆 POI。")
    print(f"📂 資料夾: {output_dir}")

if __name__ == "__main__":
    main()
