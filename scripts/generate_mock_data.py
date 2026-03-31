import asyncio
import os
import sys
import json
import random

# 確保能從專案根目錄匯入 src 模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.repository import DatabaseRepository
from src.utils.llm_adapter import get_llm_adapter

# 預先定義 15 筆符合 YTP 賽題情境的虛擬 POI
MOCK_POIS = [
    # 夜間美食 (Night Food)
    {"name": "饒河街觀光夜市", "category": "夜間美食", "description": "米其林必比登推薦胡椒餅的發源地", "lat": 25.0505, "lng": 121.5775},
    {"name": "寧夏夜市", "category": "夜間美食", "description": "以千歲宴聞名，蚵仔煎與地瓜球必吃", "lat": 25.0560, "lng": 121.5154},
    {"name": "阿宗麵線 (西門町)", "category": "夜間美食", "description": "站著吃也要排隊的老字號大腸麵線", "lat": 25.0435, "lng": 121.5076},
    
    # 商圈購物 (Shopping)
    {"name": "信義商圈", "category": "商圈購物", "description": "百貨林立，街頭藝人表演熱點", "lat": 25.0359, "lng": 121.5670},
    {"name": "大稻埕迪化街", "category": "商圈購物", "description": "傳統南北貨與現代文創商店交錯的老街", "lat": 25.0573, "lng": 121.5095},
    {"name": "中山心中山線形公園", "category": "商圈購物", "description": "文青聚集地，充滿特色服飾與甜點店", "lat": 25.0530, "lng": 121.5204},
    
    # 文青散策 (Culture & Walk)
    {"name": "華山1914文化創意產業園區", "category": "文青散策", "description": "舊酒廠改建，展覽與特色選物店", "lat": 25.0441, "lng": 121.5294},
    {"name": "松山文創園區", "category": "文青散策", "description": "結合菸廠古蹟與誠品生活的文教休閒區", "lat": 25.0438, "lng": 121.5604},
    {"name": "公館寶藏巖", "category": "文青散策", "description": "藝術村駐村，地形獨特的山城聚落", "lat": 25.0105, "lng": 121.5323},
    {"name": "榕錦時光生活園區", "category": "文青散策", "description": "日式老屋翻新，和服體驗與咖啡館", "lat": 25.0312, "lng": 121.5265},
    
    # 演唱會活動 (Concerts & Events)
    {"name": "台北小巨蛋", "category": "演唱會活動", "description": "國內外巨星演唱會首選場地", "lat": 25.0519, "lng": 121.5533},
    {"name": "台北流行音樂中心", "category": "演唱會活動", "description": "以流行音樂為主題的新興表演場館", "lat": 25.0535, "lng": 121.6033},
    
    # 市集展演 (Markets & Exhibitions)
    {"name": "建國假日花市", "category": "市集展演", "description": "週末限定的大型花草植物市集", "lat": 25.0336, "lng": 121.5381},
    {"name": "四四南村", "category": "市集展演", "description": "原眷村改建，假日好丘市集與市區遠眺101", "lat": 25.0315, "lng": 121.5615},
    {"name": "MAJI 集食行樂 (圓山)", "category": "市集展演", "description": "結合異國美食與創意市集的複合空間", "lat": 25.0716, "lng": 121.5218},
]

async def seed_static_pois(repo: DatabaseRepository):
    """階段 1: 初始化資料庫並寫入靜態 POI"""
    print("🚀 正在初始化資料表 schema...")
    await repo.init_db()
    
    print(f"📥 正在寫入 {len(MOCK_POIS)} 筆基礎景點 (POIs)...")
    poi_configs = []
    for poi in MOCK_POIS:
        poi_id = await repo.insert_poi(
            name=poi["name"],
            category=poi["category"],
            description=poi["description"],
            lat=poi["lat"],
            lng=poi["lng"]
        )
        poi_configs.append((poi_id, poi["name"], poi["category"]))
        
    print("✅ 基礎景點寫入完成！\n")
    return poi_configs

async def generate_mock_trends_for_poi(repo: DatabaseRepository, llm, poi_id: int, name: str, category: str):
    """階段 2: 使用 LLM 產生特定 POI 的隨機虛擬社群討論"""
    prompt = f"""
    # 任務設定
    你現在是一個社群輿情產生器，要替「{name}」這個台北市景點產生 4 篇虛擬的社群相關貼文。
    
    # 景點資訊
    - 名稱：{name}
    - 類別：{category}
    
    # 產生要求
    請模擬網路上 Dcard、PTT或 IG 的鄉民發言語氣。包含抱怨人多、稱讚美食、詢問交通、或是情境打卡。
    請確保 4 篇貼文中包含不同情緒 (positive, negative, neutral)。
    
    # 輸出格式
    你必須嚴格輸出合法的 JSON 陣列 (Array)，不能有一絲一毫其他文字或 Markdown。格式如下：
    [
      {{"content": "超愛這裡的氣氛，昨天下午去逛好悠閒✨", "sentiment": "positive", "platform": "IG"}},
      {{"content": "人多到滿出來，排隊排了半小時真的會氣瘋😡", "sentiment": "negative", "platform": "Dcard"}}
    ]
    """
    
    try:
        response_text = await llm.generate_content(prompt)
        # 清理可能夾帶的 Markdown 符號
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        data_list = json.loads(clean_text)
        
        # 寫入資料庫
        for data in data_list:
            await repo.insert_social_trend(
                poi_id=poi_id,
                content=data["content"][:200], # 防止過長
                sentiment=data["sentiment"],
                platform=data["platform"]
            )
        print(f"  └ 成功生成 {name} 的 4 筆虛擬動態")
        
    except Exception as e:
        print(f"  └ ❌ {name} 生成失敗: {str(e)}")


async def main():
    repo = DatabaseRepository()
    llm = get_llm_adapter()
    
    # 執行階段 1
    poi_configs = await seed_static_pois(repo)
    
    # 執行階段 2
    print("🤖 正在呼叫 Gemini API 產生模擬虛擬社群資料 (這會花一點時間)...")
    
    # 為避免 API Rate Limit (429)，我們批次處理並加入延遲
    for poi_id, name, category in poi_configs:
        await generate_mock_trends_for_poi(repo, llm, poi_id, name, category)
        await asyncio.sleep(2) # 暫停 2 秒避免超過每分鐘請求限制限制
        
    print("\n🎉 Sprint 2: 資料庫初始化與情境模擬資料生成全部完成！")

if __name__ == "__main__":
    asyncio.run(main())
