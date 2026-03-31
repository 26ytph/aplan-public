import requests
import logging
from typing import List, Dict, Any

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DcardFetcher:
    """擷取 Dcard 指定看板的熱門文章"""
    
    BASE_URL = "https://www.dcard.tw/service/api/v2"

    def __init__(self):
        # 模擬瀏覽器 User-Agent 以防止被輕易阻擋
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

    def fetch_popular_posts(self, forum_alias: str = "travel", limit: int = 15) -> List[Dict[str, Any]]:
        """
        抓取指定看板 (例如 travel, food, taipei) 的熱門文章
        """
        url = f"{self.BASE_URL}/forums/{forum_alias}/posts?popular=true&limit={limit}"
        logger.info(f"正在抓取 Dcard [{forum_alias}] 看板前 {limit} 篇熱門文章: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                logger.error(f"Dcard 抓取失敗 [{response.status_code}]: {response.text}")
                return []
                
            data = response.json()
            logger.info(f"成功取得 {len(data)} 篇 Dcard 文章。")
            return data
        except Exception as e:
            logger.error(f"Dcard 擷取發生例外錯誤: {e}")
            return []

    def normalize_data(self, post: Dict[str, Any]) -> str:
        """
        將 Dcard 原始文章資料提取為純文字，供後續 LLM 洗理
        """
        title = post.get('title', '')
        excerpt = post.get('excerpt', '')
        tags = ", ".join(post.get('topics', []))
        
        # 組合成一段提供給 Gemini 洗理的原始內文
        # 在爬蟲階段不直接給定情緒，交由 LLM 判斷
        return f"標題：{title}\n摘要：{excerpt}\n關鍵字：{tags}"

if __name__ == "__main__":
    fetcher = DcardFetcher()
    posts = fetcher.fetch_popular_posts("travel", limit=3)
    for p in posts:
        print(fetcher.normalize_data(p))
        print("-" * 50)
