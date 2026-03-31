import aiosqlite
import json
from typing import List, Dict, Any, Optional
from src.core.config import get_settings

class DatabaseRepository:
    """
    非同步資料庫存取層 (Database Access Object - DAO)
    負責封裝所有對 SQLite 的讀寫操作。
    """
    def __init__(self):
        settings = get_settings()
        self.db_path = settings.db_path

    async def init_db(self):
        """讀取 schema.sql 並初始化資料表"""
        try:
            with open("src/db/schema.sql", "r", encoding="utf-8") as f:
                schema_script = f.read()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.executescript(schema_script)
                await db.commit()
                # print("✅ 資料庫初始化完成")
        except Exception as e:
            raise RuntimeError(f"Database Initialization Failed: {e}")

    # === POI (Points of Interest) 操作 ===
    
    async def insert_poi(self, name: str, category: str, description: str, lat: float, lng: float, address: str = "", image_url: str = "", source: str = "MOCK") -> int:
        """新增一個景點"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO pois (name, category, description, address, image_url, source, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, category, description, address, image_url, source, lat, lng)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_all_pois(self) -> List[Dict[str, Any]]:
        """取得所有景點資料"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM pois")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_poi_categories(self) -> List[str]:
        """取得所有不重複的景點分類標籤"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT DISTINCT category FROM pois WHERE category IS NOT NULL AND category != ''")
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
            
    async def get_sample_locations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """隨機抽選幾個景點作為模擬位置選項"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # 使用 ORDER BY RANDOM() 在 SQLite 中進行隨機排序
            cursor = await db.execute("SELECT id, name, lat, lng FROM pois ORDER BY RANDOM() LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # === Social Trends (社群動態) 操作 ===
    
    async def insert_social_trend(self, poi_id: int, content: str, sentiment: str, platform: str) -> int:
        """新增一筆模擬社群貼文"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO social_trends (poi_id, content, sentiment, platform) VALUES (?, ?, ?, ?)",
                (poi_id, content, sentiment, platform)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_trends_by_poi(self, poi_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """取得特定景點的近期社群聲量"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM social_trends WHERE poi_id = ? ORDER BY created_at DESC LIMIT ?",
                (poi_id, limit)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # === User Profiles (使用者偏好) 操作 ===
    
    async def upsert_user_profile(self, user_id: str, preferences: dict, history: list) -> None:
        """更新或新增使用者偏好 (Upsert)"""
        async with aiosqlite.connect(self.db_path) as db:
            # 先檢查是否存在
            cursor = await db.execute("SELECT id FROM user_profiles WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            
            if row:
                # Update
                await db.execute(
                    "UPDATE user_profiles SET preferences = ?, history = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (json.dumps(preferences, ensure_ascii=False), json.dumps(history, ensure_ascii=False), user_id)
                )
            else:
                # Insert
                await db.execute(
                    "INSERT INTO user_profiles (user_id, preferences, history) VALUES (?, ?, ?)",
                    (user_id, json.dumps(preferences, ensure_ascii=False), json.dumps(history, ensure_ascii=False))
                )
            await db.commit()
