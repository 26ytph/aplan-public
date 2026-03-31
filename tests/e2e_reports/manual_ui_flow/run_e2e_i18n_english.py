import time
import sys
import os
import shutil
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def log_step(step_name: str):
    print(f"\n▶️ [STEP] {step_name}")
    return time.time()

def log_done(start_time: float):
    elapsed = time.time() - start_time
    print(f"   ✔️ 成功 (耗時: {elapsed:.2f}s)")

def log_wait(ms: int, reason: str):
    print(f"   ⏳ [WAIT] {reason} (強制等待 {ms}ms)...")
    time.sleep(ms / 1000.0)
    print(f"   ✔️ 等待完畢")

# 錄影命名常數
SCENARIO_NAME = "e2e_i18n_english_switch_20260327"
VIDEO_DIR = "tests/e2e_videos"

def run_test():
    print("==================================================")
    print("🚀 [START] E2E 測試: i18n 英文切換 + 英文搜尋")
    print("==================================================")

    total_start = time.time()

    with sync_playwright() as p:
        try:
            st = log_step("啟動 Chromium 瀏覽器")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                record_video_dir=VIDEO_DIR,
                record_video_size={"width": 1280, "height": 750}
            )
            page = context.new_page()
            log_done(st)

            st = log_step("導航至 http://localhost:8000")
            page.goto("http://localhost:8000", timeout=15000)
            log_done(st)

            log_wait(3500, "等待 Metadata 載入")

            # --- 切換為英文 ---
            st = log_step("點擊切換語系為【EN】")
            lang_btn_en = page.locator('button[data-lang="en"]')
            lang_btn_en.wait_for(state="visible", timeout=5000)
            lang_btn_en.click()
            log_done(st)

            log_wait(1000, "等待 i18n UI 替換")

            # --- 驗證 UI 靜態文字 ---
            st = log_step("驗證 UI 靜態文字是否全部轉為英文")
            checks = {
                "app_title": "Taipei Time Machine",
                "context_title": "REAL-TIME CONTEXT",  # Tailwind `uppercase` CSS 轉換
                "weather_label": "Weather",
                "time_label": "Departure Time",
                "location_label": "Current Location",
                "search_range_label": "Search Radius",
                "explore_title": "What do you want to explore?",
                "ai_recommend_title": "✨ AI Picks for You",
                "generate_btn": "Generate My Time Machine Tour",
            }
            all_passed = True
            for key, expected in checks.items():
                actual = page.locator(f'[data-i18n="{key}"]').inner_text()
                status = "✅" if actual == expected else "❌"
                if actual != expected:
                    all_passed = False
                print(f"   {status} {key}: 「{actual}」(期望: 「{expected}」)")

            placeholder = page.locator("#ai-search-input").get_attribute("placeholder")
            ph_ok = "Late night food" in placeholder
            print(f"   {'✅' if ph_ok else '❌'} placeholder: 「{placeholder}」")
            if not ph_ok:
                all_passed = False
            log_done(st)

            if not all_passed:
                raise Exception("部份 UI 文字未正確切換為英文！")

            # --- 英文搜尋 ---
            query_text = "I want to find a cozy cafe near Taipei 101 for afternoon tea"
            st = log_step(f"填入英文搜尋: '{query_text}'")
            input_box = page.locator("#ai-search-input")
            input_box.fill(query_text)
            log_done(st)

            log_wait(1000, "等待輸入完成")

            st = log_step("點擊送出按鈕")
            page.locator("#btn-ai-submit").click()
            log_done(st)

            st = log_step("等待後端英文推薦結果 (最多 60 秒)")
            first_card = page.locator("div.bg-white.rounded-2xl").first
            first_card.wait_for(state="visible", timeout=60000)
            log_done(st)

            log_wait(4000, "確保推薦結果完全渲染")

            # --- 捲動 + 截圖 ---
            st = log_step("捲動到結果區並截圖")
            page.locator("#results-section").scroll_into_view_if_needed()
            page.mouse.wheel(0, 600)
            log_wait(1000, "等待卡片入鏡")

            screenshot_path = f"tests/{SCENARIO_NAME}.png"
            page.screenshot(path=screenshot_path, full_page=False)
            log_done(st)

            # --- 切回繁中驗證 ---
            st = log_step("切回【繁中】並驗證恢復")
            page.locator('button[data-lang="zh-TW"]').click()
            log_wait(500, "等待切換")
            title_zhtw = page.locator('[data-i18n="app_title"]').inner_text()
            print(f"   App Title = 「{title_zhtw}」")
            if title_zhtw != "臺北時光機":
                raise Exception("切回繁中失敗！")
            log_done(st)

            # === 錄影存檔：先關 context (flush 錄影)，再開新頁面供手動測試 ===
            st = log_step("存檔錄影並開啟手動測試頁面")
            raw_video_path = page.video.path()
            final_video_path = os.path.join(VIDEO_DIR, f"{SCENARIO_NAME}.webm")

            # 關閉錄影用的 context（這會 flush 影片到磁碟）
            context.close()

            # 重新命名錄影檔
            if os.path.exists(raw_video_path):
                shutil.move(raw_video_path, final_video_path)

            # 開一個全新的頁面（無錄影），供使用者手動繼續操作
            manual_page = browser.new_page()
            manual_page.goto("http://localhost:8000", timeout=15000)
            log_done(st)

            print("\n" + "="*50)
            print("✅ [PASS] 英文 i18n E2E 自動化測試劇本全數通過！")
            print(f"   📸 截圖: {screenshot_path}")
            print(f"   🎬 錄影: {final_video_path}")
            print("-"*50)
            print("👉 瀏覽器已開啟新頁面，您可以手動繼續測試其他語言 (JA/KO/TH)")
            print("👉 測試完畢後，回到 Terminal 按下 [Enter] 關閉瀏覽器")
            print("="*50)
            input(">>> 按下 [Enter] 關閉瀏覽器...")

            browser.close()

            print(f"\n🏆 [SUCCESS] 總耗時: {time.time() - total_start:.2f}s")
            print(f"📸 截圖: {screenshot_path}")
            print(f"🎬 影片: {final_video_path}")
            sys.exit(0)

        except PlaywrightTimeoutError as e:
            print(f"\n💥 [TIMEOUT] {str(e)[:200]}")
            page.screenshot(path="tests/e2e_i18n_en_timeout.png")
            print("📸 卡關截圖: tests/e2e_i18n_en_timeout.png")
            sys.exit(1)

        except Exception as e:
            print(f"\n💥 [CRITICAL] {e}")
            sys.exit(1)

if __name__ == "__main__":
    run_test()
