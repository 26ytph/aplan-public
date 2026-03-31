import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Any

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PTTFetcher:
    """擷取 PTT 指定看板的文章清單與內容"""
    
    BASE_URL = "https://www.ptt.cc"

    def __init__(self):
        # 繞過年齡限制 (如 Gossiping 板)
        self.cookies = {"over18": "1"}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def fetch_articles(self, board: str = "Food", pages: int = 1) -> List[Dict[str, Any]]:
        """
        抓取指定看板最新文章
        """
        articles = []
        url = f"{self.BASE_URL}/bbs/{board}/index.html"
        
        for i in range(pages):
            logger.info(f"正在抓取 PTT [{board}] 看板: {url}")
            try:
                res = requests.get(url, headers=self.headers, cookies=self.cookies, timeout=10)
                if res.status_code != 200:
                    logger.error(f"PTT 抓取失敗 [{res.status_code}]")
                    break
                    
                soup = BeautifulSoup(res.text, "html.parser")
                
                # 取得該頁所有文章
                rents = soup.find_all("div", class_="r-ent")
                for rent in rents:
                    title_elem = rent.find("div", class_="title").find("a")
                    if not title_elem:
                        continue # 本文已被刪除
                        
                    title = title_elem.text.strip()
                    # 簡單過濾公告
                    if "[公告]" in title:
                        continue
                        
                    article_url = self.BASE_URL + title_elem["href"]
                    
                    articles.append({
                        "board": board,
                        "title": title,
                        "url": article_url
                    })
                    
                # 取得上一頁連結
                btn_group = soup.find("div", class_="btn-group-paging")
                if btn_group:
                    prev_btn = btn_group.find_all("a")[1] # 上一頁按鈕
                    if "href" in prev_btn.attrs:
                        url = self.BASE_URL + prev_btn["href"]
                    else:
                        break
                else:
                    break
                    
            except Exception as e:
                logger.error(f"PTT 擷取發生例外錯誤: {e}")
                break
                
        logger.info(f"成功取得 {len(articles)} 篇 PTT [{board}] 文章。")
        return articles

    def search_articles(self, board: str, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        搜尋指定看板的文章 (用於精準匹配景點)
        """
        articles = []
        # PTT 搜尋有時需要 URL 編碼，但 requests 預設會處理
        url = f"{self.BASE_URL}/bbs/{board}/search?q={query}"
        logger.info(f"正在搜尋 PTT [{board}] 關鍵字 '{query}'...")
        
        try:
            res = requests.get(url, headers=self.headers, cookies=self.cookies, timeout=10)
            if res.status_code != 200:
                logger.warning(f"PTT 搜尋失敗 [{res.status_code}]")
                return articles
                
            soup = BeautifulSoup(res.text, "html.parser")
            rents = soup.find_all("div", class_="r-ent")
            
            for rent in rents:
                if len(articles) >= limit:
                    break
                    
                title_elem = rent.find("div", class_="title").find("a")
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                article_url = self.BASE_URL + title_elem["href"]
                
                articles.append({
                    "board": board,
                    "title": title,
                    "url": article_url
                })
        except Exception as e:
            logger.error(f"PTT 搜尋發生錯誤: {e}")
            
        return articles

    def fetch_article_content(self, url: str) -> str:
        """
        進入文章內頁抓取主文
        """
        try:
            res = requests.get(url, headers=self.headers, cookies=self.cookies, timeout=10)
            if res.status_code != 200:
                return ""
                
            soup = BeautifulSoup(res.text, "html.parser")
            main_content = soup.find("div", id="main-content")
            
            if not main_content:
                return ""
                
            # 移除 span 和 div meta 資訊，只留下純文字
            for meta in main_content.find_all(["div", "span"]):
                meta.decompose()
                
            text = main_content.text.strip()
            # 限制長度避免過長
            return text[:500] if len(text) > 500 else text
            
        except Exception as e:
            logger.warning(f"擷取內文失敗 ({url}): {e}")
            return ""

    def normalize_data(self, article: Dict[str, Any]) -> str:
        """
        將 PTT 文章轉換為提供給 LLM 清洗的字串
        """
        content = self.fetch_article_content(article["url"])
        return f"來源：PTT {article['board']}板\n標題：{article['title']}\n內文節錄：{content}"

if __name__ == "__main__":
    fetcher = PTTFetcher()
    docs = fetcher.fetch_articles("Food", pages=1)
    if docs:
        print(fetcher.normalize_data(docs[-1]))
