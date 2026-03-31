import time
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def log_step(step_name: str):
    print(f"\n▶️ [STEP] {step_name}")
    return time.time()

def log_done(start_time: float):
    elapsed = time.time() - start_time
    print(f"   ✔️ 成功 (耗時: {elapsed:.2f}s)")

def log_wait(ms: int, reason: str):
    print(f"   ⏳ [WAIT] {reason} (強制等待 {ms}ms)...")
    start = time.time()
    time.sleep(ms / 1000.0)
    elapsed = time.time() - start
    print(f"   ✔️ 等待完畢 (耗時: {elapsed:.2f}s)")

def run_test():
    print("==================================================")
    print("🚀 [START] E2E 測試啟動: 多語系 (i18n) 動態切換與日文搜尋")
    print("==================================================")

    total_start = time.time()
    VIDEO_DIR = "tests/e2e_videos"
    
    with sync_playwright() as p:
        try:
            # 1. 開啟瀏覽器 (可視化模式方便除錯)，並啟用錄影功能
            st = log_step("啟動 Chromium 瀏覽器")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                record_video_dir=VIDEO_DIR,
                record_video_size={"width": 1280, "height": 750}
            )
            page = context.new_page()
            print(f"   🎬 錄影已啟動！")
            log_done(st)

            # 2. 前往 localhost:8000
            st = log_step("導航至 http://localhost:8000")
            page.goto("http://localhost:8000", timeout=15000)
            log_done(st)

            log_wait(3500, "等待 UI 介面載入 Metadata (標籤與地點)")

            # 3. 切換語系至日文
            st = log_step("點擊切換語系為【日本語】")
            lang_btn_ja = page.locator('button[data-lang="ja"]')
            lang_btn_ja.wait_for(state="visible", timeout=5000)
            lang_btn_ja.click()
            log_done(st)

            log_wait(1000, "等待 i18n UI 替換完成")

            # 驗證 UI 是否切換
            st = log_step("驗證 UI 上的靜態文字是否轉為日文")
            app_title = page.locator('[data-i18n="app_title"]').inner_text()
            print(f"   目前 App Title = {app_title}")
            if app_title != "台北タイムマシン":
                raise Exception("App Title 沒有切換為日文！")
            log_done(st)

            # 4. 填寫日文探索意圖
            query_text = "台北駅近くで雨宿りして夜食を食べたい"
            st = log_step(f"尋找輸入框並填入日文咒語: '{query_text}'")
            input_box = page.locator("#ai-search-input")
            input_box.fill(query_text)
            log_done(st)

            log_wait(1000, "等待字串輸入")

            # 5. 點擊送出按鈕
            st = log_step("點擊『送出 / AI 分析』按鈕")
            submit_btn = page.locator("#btn-ai-submit")
            submit_btn.click()
            log_done(st)
            
            # 6. 等待推薦結果
            st = log_step("等待後端多語系推薦結果卡片渲染 (最多 60 秒)")
            first_card = page.locator("div.bg-white.rounded-2xl").first
            first_card.wait_for(state="visible", timeout=60000)
            log_done(st)
            
            result_area = page.locator("#results-section")

            log_wait(4000, "確保推薦結果清單完全渲染")

            # 7. 捲動與截圖
            st = log_step("捲動到 AI 推薦結果區塊並截圖")
            result_area.scroll_into_view_if_needed()
            page.mouse.wheel(0, 600)
            log_wait(1000, "等待卡片入鏡")

            screenshot_path = "tests/e2e_i18n_japanese_switch_20260327.png"
            page.screenshot(path=screenshot_path, full_page=False)
            print(f"   📸 截圖已儲存至: {screenshot_path}")
            log_done(st)

            # 8. 結束前暫停 — 按新 Skill 規範給出明確指引
            print("\n" + "="*50)
            print("✅ [PASS] 多語系 E2E 自動化測試劇本已走完！")
            print(f"   📸 截圖: {screenshot_path}")
            print(f"   🎬 錄影: tests/e2e_videos/ (關閉後自動存檔)")
            print("-"*50)
            print("👉 選項 A: 您可以在瀏覽器上「手動繼續測試」其他語言切換 (EN/KO/TH)")
            print("👉 選項 B: 回到 Terminal 按下 [Enter] 關閉瀏覽器，結束本次測試")
            print("="*50)
            input(">>> 按下 [Enter] 關閉瀏覽器並完成錄影...")

            context.close()
            browser.close()

            print("🏆 [SUCCESS] 多語系生圖 E2E 測試通關！")
            sys.exit(0)

        except PlaywrightTimeoutError as e:
            print("\n==================================================")
            print("💥 [ERROR] 測試超時卡關 (Timeout)！")
            page.screenshot(path="tests/e2e_i18n_timeout.png")
            print("📸 已截取卡關畫面的截圖 (tests/e2e_i18n_timeout.png)")
            sys.exit(1)
            
        except Exception as e:
            print("\n==================================================")
            print(f"💥 [CRITICAL] 發生未預期錯誤！\n{e}")
            sys.exit(1)

if __name__ == "__main__":
    run_test()
