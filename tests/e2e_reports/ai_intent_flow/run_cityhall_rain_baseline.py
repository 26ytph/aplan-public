import time
import sys
import os
import shutil
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SCENARIO_NAME = "e2e_cityhall_rain_20260330"
VIDEO_DIR = "tests/e2e_videos"
SCREENSHOT_FILE = f"tests/e2e_views/{SCENARIO_NAME}.png"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs("tests/e2e_views", exist_ok=True)

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            record_video_dir=VIDEO_DIR,
            record_video_size={"width": 1280, "height": 750}
        )
        page = context.new_page()

        print("🌐 1. 前往應用程式首頁...")
        page.goto("http://localhost:8000", timeout=15000)
        page.wait_for_load_state("networkidle")
        time.sleep(2) # 讓畫面穩定

        print("💬 2. 模擬使用者透過魔法搜尋框輸入意圖...")
        user_intent = "下著暴雨，我在台北市政府，我想找個不會淋濕的地方看展覽喝咖啡"
        page.fill("#ai-search-input", user_intent)
        time.sleep(1)

        print("🖱️ 3. 點擊送出讓 AI 解析並檢索...")
        page.click("#btn-ai-submit")

        print("⏳ 4. 等待 Hybrid RAG 完成運算與推薦生成...")
        page.wait_for_selector("#result-summary", timeout=15000)
        
        # [修改] 先在畫面上方停留，讓錄影清楚拍下天氣、時間與 AI 總結
        print("👀 4.5. 確認上方情境儀表板 (天氣與位置) 已更新...")
        page.wait_for_timeout(3500)

        print("⏳ 4.6. 等待推薦景點卡片產生...")
        try:
            page.wait_for_selector("#result-cards-container > div", timeout=15000)
            print("✅ 已發現推薦卡片。")
        except:
            print("⚠️ 未發現卡片，嘗試繼續執行...")

        print("⏬ 4.7. 強制捲動到頁面底部以捕捉所有卡片...")
        # 多次嘗試捲動以確保動態內容載入後視角正確
        for _ in range(3):
            page.evaluate("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })")
            page.wait_for_timeout(1000)
        
        print("📸 5. 擷取最終結果畫面 (關閉 full_page 避免錄影跳動)...")
        page.screenshot(path=SCREENSHOT_FILE, full_page=False)
        print("⏳ 5.5. 在結果畫面停留 7 秒，確保錄影完整捕捉最終狀態...")
        time.sleep(7) # 使用系統級 sleep 確保錄影 context 穩定錄入影像

        # ✅ 結尾錄影收尾流程
        raw_video_path = page.video.path()
        final_video_path = os.path.join(VIDEO_DIR, f"{SCENARIO_NAME}.webm")
        
        context.close()
        if os.path.exists(raw_video_path):
            shutil.move(raw_video_path, final_video_path)
            
        print("✅ 自動化測試劇本已走完！錄影已存檔。")
        print(f"   📸 截圖: {SCREENSHOT_FILE}")
        print(f"   🎬 錄影: {final_video_path}")

        # 如果是從自動端執行 (帶有腳本參數)，則不進入 input 阻塞
        if len(sys.argv) > 1 and sys.argv[1] == "--auto":
            print("🚀 自動化模式：跳過手動確認並關閉瀏覽器。")
            browser.close()
            return

        print("👉 您可以在 Terminal 按下 [Enter] 關閉下方自動開啟的瀏覽器畫面。")
        # 開新頁面保留畫面給使用者看
        manual_page = browser.new_page()
        manual_page.goto("http://localhost:8000")
        input(">>> 測試結束。按下 [Enter] 關閉瀏覽器...")
        browser.close()

if __name__ == "__main__":
    run_test()
