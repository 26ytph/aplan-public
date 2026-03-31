import time
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def log_step(step_name: str):
    """印出步驟名稱，並記錄開始時間"""
    print(f"\n▶️ [STEP] {step_name}")
    return time.time()

def log_done(start_time: float):
    """印出完成訊息與花費時間"""
    elapsed = time.time() - start_time
    print(f"   ✔️ 成功 (耗時: {elapsed:.2f}s)")

def log_wait(ms: int, reason: str):
    """模擬原定劇本的強制睡眠，並計時"""
    print(f"   ⏳ [WAIT] {reason} (強制等待 {ms}ms)...")
    start = time.time()
    time.sleep(ms / 1000.0)
    elapsed = time.time() - start
    print(f"   ✔️ 等待完畢 (耗時: {elapsed:.2f}s)")

def run_test():
    print("==================================================")
    print("🚀 [START] E2E 測試啟動: 晚餐時間，附近義式餐廳推薦")
    print("==================================================")

    total_start = time.time()

    VIDEO_DIR = "tests/e2e_videos"
    
    with sync_playwright() as p:
        try:
            # 1. 開啟瀏覽器 (可視化模式方便除錯)，並啟用錄影功能
            st = log_step("啟動 Chromium 瀏覽器 (含錄影模式)")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                record_video_dir=VIDEO_DIR,       # 錄影存放目錄
                record_video_size={"width": 1280, "height": 750}  # 錄影解析度
            )
            page = context.new_page()
            print(f"   🎬 錄影已啟動！影片將暫存至: {VIDEO_DIR}/")
            log_done(st)

            # 2. 前往 localhost:8000
            st = log_step("導航至 http://localhost:8000")
            page.goto("http://localhost:8000", timeout=15000)
            log_done(st)

            log_wait(3500, "等待 UI 介面與地圖資源完全載入")

            # 3. 填寫 AI 探索意圖
            query_text = "晚餐時間，附近的義式餐廳推薦"
            st = log_step(f"尋找輸入框並填入咒語: '{query_text}'")
            input_box = page.locator("#ai-search-input")
            input_box.wait_for(state="visible", timeout=10000)
            input_box.fill(query_text)
            log_done(st)

            log_wait(1000, "等待字串輸入完畢的渲染緩衝")

            # 4. 點擊送出按鈕
            st = log_step("尋找並點擊『送出 / AI 分析』按鈕")
            submit_btn = page.locator("#btn-ai-submit")
            submit_btn.wait_for(state="visible", timeout=10000)
            submit_btn.click()
            log_done(st)

            # 5. 等待後端檢索那 1.5 萬筆向量庫並回傳 AI 結果
            log_wait(2000, "給予後端初步檢索時間 (預先緩衝)")
            
            st = log_step("等待後端推薦結果卡片渲染完出現 (最多忍受 60 秒)")
            # 不等 #results-section！那個區塊在「計算中」時也會 visible。
            # 我們等第一張真實的 POI 推薦卡片 (bg-white rounded-2xl) 出現才算完成！
            first_card = page.locator("div.bg-white.rounded-2xl").first
            first_card.wait_for(state="visible", timeout=60000)
            log_done(st)
            
            result_area = page.locator("#results-section")

            log_wait(4000, "確保推薦結果清單與地圖標記(Markers)完全渲染")

            # 6. 分段捲動：先捲到結果區，再繼續往下拉看到卡片
            st = log_step("捲動到 AI 推薦結果區塊 (確保卡片完整入鏡)")
            # Step 6a: 先讓結果區塊滾進視野
            result_area.scroll_into_view_if_needed()
            log_wait(800, "等待初步捲動完成")
            # Step 6b: 再向下多拉 600px，確保推薦卡片出現在畫面中段
            page.mouse.wheel(0, 600)
            log_wait(800, "等待卡片入鏡")
            # Step 6c: 再拉 400px 讓第一張卡片完整呈現
            page.mouse.wheel(0, 400)
            log_done(st)

            log_wait(2000, "等待滾動動畫完成")

            # 7a. 捲回到第一張最高優先推薦卡片 (讓錄影結束在最佳位置)
            st = log_step("捲回第一張推薦卡片 (最高優先選項)")
            first_card.scroll_into_view_if_needed()
            log_done(st)

            log_wait(1500, "停在最高優先推薦卡片上")

            # 8. 截圖
            st = log_step("擷取結果畫面 Screenshot")
            screenshot_path = "e2e_italian_dinner_result.png"
            page.screenshot(path=screenshot_path, full_page=False)
            print(f"   ✔️ 截圖已儲存至: {screenshot_path}")
            log_done(st)

            # 9. 結束前緩衝 (讓錄影確保最後畫面寫入磁碟)
            log_wait(5000, "停留畫面，確保影片編碼器寫入最後畫面")

            # ✋ 暫停！讓使用者直接看看結果，不需要找錄影檔
            print("\n" + "="*50)
            print("✅ 測試完成！瀏覽器保持開啟供您直接觀看結果。")
            print("👉 檢查完畢後，請回到 Terminal 按下 [Enter] 以關閉瀏覽器並存下錄影。")
            print("="*50)
            input(">>> 按下 [Enter] 關閉瀏覽器並完成錄影...")

            # 10. 關閉 context (此時 Playwright 才會把影片 flush 到磁碟)
            st = log_step("關閉 Browser Context 並完成錄影存檔")
            video_path = page.video.path()
            context.close()
            browser.close()
            print(f"   🎬 影片已儲存至: {video_path}")
            log_done(st)

            print("==================================================")
            print("🏆 [SUCCESS] E2E 自動化測試完美通關！")
            total_elapsed = time.time() - total_start
            print(f"⏱  總耗時: {total_elapsed:.2f}s")
            print(f"📸 截圖: {screenshot_path}")
            print(f"🎬 影片: {video_path}")
            print("==================================================")
            sys.exit(0)

        except PlaywrightTimeoutError as e:
            print("\n==================================================")
            print("💥 [ERROR] 測試超時卡關 (Timeout)！")
            print(f"   詳細原因: 網頁元素在規定時間內未出現或無回應。")
            print(f"   Exception: {str(e)[:200]}")
            print("==================================================")
            page.screenshot(path="e2e_timeout_error.png")
            print("📸 已截取卡關畫面的截圖 (e2e_timeout_error.png)")
            sys.exit(1)
            
        except Exception as e:
            print("\n==================================================")
            print(f"💥 [CRITICAL] 發生未預期錯誤！")
            print(f"   Exception: {str(e)}")
            print("==================================================")
            sys.exit(1)

if __name__ == "__main__":
    run_test()
