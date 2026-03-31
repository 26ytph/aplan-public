import sqlite3
import os

DB_PATH = "/Users/ytp-thomas/Desktop/APlan/test.db"

def elevate_neihu():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    neihu_pois = [
        # (name, category, description, address, lat, lng, source, tier)
        ("教父牛排 Danny's Steakhouse", "food", "米其林一星頂級牛排館，大直/內湖地區頂尖餐飲地標。", "104台北市中山區樂群三路58號", 25.0831, 121.5583, "MICHELIN_ENRICH", 1),
        ("Miacucina (內湖店)", "food", "指標性義式蔬食料理，工業風設計與開放式廚房為內科熱門聚會地。", "114台北市內湖區瑞光路601號", 25.0818, 121.5705, "ENRICHED_NEIHU", 2),
        ("覺旅咖啡 Journey Kaffe (陽光店)", "food", "內科最具代表性的工作咖啡廳，提供DIY手作與豐富木碗沙拉。", "114台北市內湖區陽光街321巷42號", 25.0748, 121.5815, "ENRICHED_NEIHU", 2),
        ("大湖公園 (Dahu Park)", "spot", "以錦帶橋與山水美景聞名，曾登上法國世界報。適合野餐、釣魚與散步。", "114台北市內湖區成功路五段31號", 25.0841, 121.6115, "GOV_TAIPEI", 1),
        ("碧山巖開漳聖王廟", "spot", "俯瞰台北市盆地與台北101的最佳夜景觀測點，周邊有白石湖吊橋。", "114台北市內湖區碧山路24號", 25.0975, 121.5875, "GOV_TAIPEI", 1),
        ("金面山親山步道 (剪刀石)", "nature", "內湖熱門攀岩步道，山頂剪刀石可環視內科與內湖區全景。", "114台北市內湖區環山路一段136巷底", 25.0888, 121.5725, "GOV_TAIPEI", 1),
        ("初心菓寮", "food", "位於文德捷運站附近的日式甜點名店，代表內湖的雅緻生活步調。", "114台北市內湖區文德路86號", 25.0785, 121.5855, "ENRICHED_NEIHU", 2),
        ("龍船岩步道", "nature", "白石湖地區的奇岩地標，巨石矗立於山脊，極具視覺衝擊力。", "114台北市內湖區碧山路62號", 25.1015, 121.5995, "GOV_TAIPEI", 2),
    ]

    for poi in neihu_pois:
        name, category, desc, addr, lat, lng, source, tier = poi
        
        # 檢查是否已存在
        cursor.execute("SELECT id FROM pois WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            print(f"🔄 更新現有 POI: {name}")
            cursor.execute("""
                UPDATE pois 
                SET category = ?, description = ?, address = ?, lat = ?, lng = ?, source = ?, tier = ?, is_embedded = 0
                WHERE id = ?
            """, (category, desc, addr, lat, lng, source, tier, row[0]))
        else:
            print(f"➕ 注入新 POI: {name}")
            cursor.execute("""
                INSERT INTO pois (name, category, description, address, lat, lng, source, tier, is_embedded)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (name, category, desc, addr, lat, lng, source, tier))

    conn.commit()
    conn.close()
    print("✅ 內湖區菁英提拔計畫注入完成！")

if __name__ == "__main__":
    elevate_neihu()
