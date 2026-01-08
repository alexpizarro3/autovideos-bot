import os
import time
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self, cookies_path="youtube_cookies.json"):
        self.cookies_path = cookies_path

    def upload_video(self, video_path: str, title: str, description: str):
        """
        Uploads a video to YouTube Shorts using Playwright.
        """
        logger.info("Starting YouTube upload...")
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not os.path.exists(self.cookies_path):
            logger.error(f"YouTube cookies not found at {self.cookies_path}")
            return False

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            
            # Load Cookies
            try:
                import json
                with open(self.cookies_path, 'r') as f:
                    cookies = json.load(f)
                
                # Sanitize cookies
                for cookie in cookies:
                     if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                            cookie['sameSite'] = 'None'
                            cookie['secure'] = True

                context.add_cookies(cookies)
            except Exception as e:
                logger.error(f"Failed to load YouTube cookies: {e}")
                return False

            page = context.new_page()

            try:
                logger.info("Navigating to YouTube Studio...")
                page.goto("https://studio.youtube.com", timeout=60000)
                
                # Check login
                if "accounts.google.com" in page.url:
                    logger.error("Redirected to Google Login. Cookies invalid.")
                    return False

                # Click Create -> Upload videos
                logger.info("Opening upload dialog...")
                page.click("#create-icon")
                page.click("text=Upload videos")
                
                # Upload file
                logger.info(f"Uploading file: {video_path}")
                with page.expect_file_chooser() as fc_info:
                    page.click("#select-files-button")
                file_chooser = fc_info.value
                file_chooser.set_files(video_path)

                # Wait for upload to complete
                # This is tricky, usually we wait for the progress bar to say "Checks complete"
                logger.info("Waiting for upload processing...")
                # Basic Wait - sophisticated logic would check the progress bar text
                time.sleep(10)
                
                # Title
                logger.info("Setting title...")
                # YouTube defaults the title to filename, let's update it
                # Logic to clear and type title
                title_box = page.locator("#textbox").first
                title_box.click()
                title_box.press("Control+a")
                title_box.press("Backspace")
                title_box.type(title[:99]) # YouTube limit 100

                # Description
                # description_box = page.locator("#textbox").nth(1) # Approximate

                # Click Next, Next, Next until Visibility
                logger.info("Navigating wizard...")
                for _ in range(3):
                    page.click("#next-button")
                    time.sleep(1)

                # Set Visibility to Public
                logger.info("Setting visibility to Public...")
                page.click("name=PUBLIC") # Radio button

                # Publish
                logger.info("Publishing...")
                page.click("#done-button")
                
                logger.info("Upload sequence finished.")
                time.sleep(5)
                return True

            except Exception as e:
                logger.error(f"YouTube upload failed: {e}")
                page.screenshot(path="debug_yt_fail.png")
                return False
            finally:
                browser.close()
