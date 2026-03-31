-- 1. 景點/消費場域資料表 (POIs: Points of Interest)
CREATE TABLE IF NOT EXISTS pois (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                   -- 景點名稱，例如：饒河街夜市、大稻埕碼頭
    category TEXT NOT NULL,               -- 類型，例如：夜間美食、市集展演、文青散策
    description TEXT,                     -- 簡述
    address TEXT,                         -- 新增：地址
    image_url TEXT,                       -- 新增：圖片網址
    source TEXT,                          -- 新增：資料來源 (MOCK, TDX_API, DATA_TAIPEI)
    lat REAL,                             -- 緯度
    lng REAL,                             -- 經度
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 模擬社群貼文表 (Social Trends)
-- 包含生成的假貼文，用於分析聲量與情境推薦
CREATE TABLE IF NOT EXISTS social_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poi_id INTEGER NOT NULL,              -- 關聯的景點 ID
    content TEXT NOT NULL,                -- 社群發文內容 (包含口語化描述與時間情境)
    sentiment TEXT,                       -- 情緒傾向，例如：positive, neutral, negative
    platform TEXT,                        -- 來源平台，例如：PTT, Dcard, IG, Threads
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 模擬貼文的發布時間
    FOREIGN KEY(poi_id) REFERENCES pois(id) ON DELETE CASCADE
);

-- 3. 使用者偏好表 (User Profiles)
-- 儲存使用者的動態旅遊標籤與歷史搜尋紀錄
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,         -- 外部識別 ID (例如 UUID 或 Session ID)
    preferences TEXT,                     -- JSON 格式儲存：動態旅遊標籤 (例如 {"keywords": ["夜市", "演唱會"], "time_pref": "night"})
    history TEXT,                         -- JSON 格式儲存：歷史點擊或查閱紀錄的清單
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
