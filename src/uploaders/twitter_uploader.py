import os
import time
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

class TwitterUploader:
    def __init__(self, cookies_path="twitter_cookies.json"):
        self.cookies_path = cookies_path

    def upload_video(self, video_path: str, text: str):
        """
        Uploads a video to X (Twitter).
        """
        logger.info("Starting X (Twitter) upload...")
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not os.path.exists(self.cookies_path):
            logger.error(f"Twitter cookies not found at {self.cookies_path}")
            return False

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            
            try:
                import json
                with open(self.cookies_path, 'r') as f:
                    cookies = json.load(f)
                
                # Sanitize
                for cookie in cookies:
                     if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                            cookie['sameSite'] = 'None'
                            cookie['secure'] = True

                context.add_cookies(cookies)
            except Exception as e:
                logger.error(f"Failed to load Twitter cookies: {e}")
                return False

            page = context.new_page()

            try:
                logger.info("Navigating to X compose...")
                page.goto("https://x.com/compose/tweet", timeout=60000)
                
                if "login" in page.url:
                    logger.error("Redirected to Login. Cookies invalid.")
                    return False

                # Upload Media
                logger.info(f"Uploading file: {video_path}")
                with page.expect_file_chooser() as fc_info:
                    page.click("div[aria-label='Add photos or video']")
                file_chooser = fc_info.value
                file_chooser.set_files(video_path)
                
                # Set Text
                logger.info("Setting text...")
                page.click("div[data-testid='tweetTextarea_0']")
                page.keyboard.type(text)

                # Wait for upload (Progress circle)
                logger.info("Waiting for media upload...")
                time.sleep(10)

                # Post
                logger.info("Posting...")
                page.click("div[data-testid='tweetButton']")
                
                logger.info("Post sequence finished.")
                time.sleep(5)
                return True

            except Exception as e:
                logger.error(f"Twitter upload failed: {e}")
                page.screenshot(path="debug_twitter_fail.png")
                return False
            finally:
                browser.close()
