import os
import time
import logging
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TikTokUploader:
    def __init__(self, cookies_path="tiktok_cookies.json"):
        self.cookies_path = cookies_path
        # TikTok selectors (these can change, so we try to be robust)
        self.SELECTORS = {
            "upload_iframe": "iframe", 
            "file_input": "input[type='file']",
            "caption_editor": ".public-DraftEditor-content",
            "post_button": "button:has-text('Post')", 
            # Fallback selectors or specific classes could be added here
        }

    def upload_video(self, video_path: str, title: str, hashtags: list[str]):
        """
        Uploads a video to TikTok using Playwright.
        Requires valid cookies for authentication.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        caption_text = f"{title} {' '.join(hashtags)}"
        
        with sync_playwright() as p:
            # Launch in headful mode first for debugging if needed, or headless=True for prod
            # Using headless=False is often safer for TikTok to avoid immediate bot detection, 
            # but creates a visible window. GitHub Actions requires headless=True.
            # Let's try headless=True with a proper user agent.
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            
            # Load Cookies
            if os.path.exists(self.cookies_path):
                logger.info(f"Loading cookies from {self.cookies_path}")
                # We need to parse the cookies file format properly. 
                # Assuming standard JSON list of cookies.
                try:
                    import json
                    with open(self.cookies_path, 'r') as f:
                        cookies = json.load(f)
                    
                    # Fix 'sameSite' attribute for Playwright
                    for cookie in cookies:
                        if 'sameSite' in cookie:
                            if cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                                cookie['sameSite'] = 'None'
                                cookie['secure'] = True # None requires Secure
                    
                    context.add_cookies(cookies)
                except Exception as e:
                    logger.error(f"Failed to load cookies: {e}")
                    return False
            else:
                logger.error(f"No cookies found at {self.cookies_path}. Cannot authenticate.")
                return False

            page = context.new_page()
            
            try:
                logger.info("Navigating to TikTok upload page...")
                page.goto("https://www.tiktok.com/upload?lang=en", timeout=60000)
                
                # Check if we are still logged in
                # A simple check is seeing if the URL redirects to login or if a 'Log in' button is prominent
                time.sleep(5)
                if "login" in page.url:
                    logger.error("Redirected to login page. Session cookies are invalid.")
                    return False

                logger.info("Waiting for file input...")
                
                # Handle potential IFrame wrapper (common in TikTok's architecture changes)
                # We try to find the input in the requested frame or main frame
                try:
                    # Try targeting the file input directly first
                    file_input = page.wait_for_selector('input[type="file"]', timeout=15000)
                except:
                    # If not found, look for iframe
                    logger.info("File input not found globally, checking iframes...")
                    frames = page.frames
                    file_input = None
                    for frame in frames:
                        try:
                            if frame.query_selector('input[type="file"]'):
                                file_input = frame.query_selector('input[type="file"]')
                                break
                        except:
                            continue
                    
                    if not file_input:
                        logger.error("Could not find file input element.")
                        return False

                # Upload the file
                logger.info(f"Uploading file: {video_path}")
                file_input.set_input_files(video_path)
                
                # Wait for upload to process
                logger.info("Waiting for video to upload and process...")
                time.sleep(10) 
                page.screenshot(path="debug_1_uploaded.png")

                # Set Caption
                logger.info("Setting caption...")
                try:
                    # Try generic contenteditable div for caption
                    # "public-DraftEditor-content" is a common Draft.js class used by TikTok
                    # But we also try a broader locator if that fails
                    caption_box = page.locator(".public-DraftEditor-content, div[contenteditable='true']").first
                    if caption_box.is_visible():
                        caption_box.click()
                        time.sleep(1)
                        # Clear existing text (filename is often pre-filled)
                        logger.info("Clearing default caption...")
                        page.keyboard.press("Control+A")
                        time.sleep(0.5)
                        page.keyboard.press("Backspace")
                        time.sleep(0.5)
                        
                        # Type new caption
                        page.keyboard.type(caption_text, delay=50)
                    else:
                        logger.warning("Caption box not visible.")
                except Exception as e:
                    logger.warning(f"Could not key in caption: {e}")
                
                # Wait for upload to complete
                logger.info("Waiting for video to upload and process...")
                # ... (upload logic logic is fine, jumping to Post button interaction)
                
                # --- NEW POST BUTTON & MODAL LOGIC ---
                try:
                    # 1. Handle Cookie Banner (if present, it might block the bottom buttons)
                    try:
                        cookie_btn = page.locator("button:has-text('Decline all'), button:has-text('Allow all'), button:has-text('Accept all')").first
                        if cookie_btn.is_visible():
                            logger.info("Closing cookie banner...")
                            cookie_btn.click()
                            time.sleep(1)
                    except:
                        pass

                    # 2. Scroll to bottom aggressively
                    logger.info("Scrolling to bottom to find Post button...")
                    page.keyboard.press("End")
                    time.sleep(1)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)

                    # 3. Locate Post button
                    # Main "Post" button (usually red)
                    post_btn = page.locator("button:has-text('Post'), button:has-text('Publicar')").last
                    
                    # Ensure it's in view
                    if not post_btn.is_visible():
                        logger.warning("Post button not visible immediately. Trying to scroll more...")
                        post_btn.scroll_into_view_if_needed()
                        time.sleep(1)
                    
                    if post_btn.is_enabled():
                        # Debug: Check for any visible warning/error before clicking
                        try:
                            # Try to capture context around 'Checks' or generic error text
                            content = page.content()
                            if "Something went wrong" in content:
                                logger.warning("Potential error detected in page content: 'Something went wrong'")
                            
                            # Log visible text of buttons just to be sure
                            logger.info(f"Post button text: {post_btn.text_content()}")
                        except:
                            pass

                        logger.info("Clicking Post...")
                        # Use JS click to avoid strictness issues if something small overlaps
                        post_btn.click(force=True)

                        # Check for Toasts (Error messages)
                        try:
                            # TUXToast or generic toast class
                            toast = page.locator("div[class*='Toast'], div[role='alert']").first
                            # We listen for a brief moment
                            time.sleep(1)
                            if toast.is_visible():
                                logger.info(f"Toast detected: {toast.text_content()}")
                        except:
                            pass

                        
                        # Check for Modal with DEEP DEBUGGING
                        logger.info("Checking for potential blocking modal...")
                        
                        # Wait a moment for modal animation
                        time.sleep(6)
                        
                        # Capture state for analysis
                        page.screenshot(path="debug_modal_visible.png")
                        with open("debug_page_source.html", "w", encoding="utf-8") as f:
                            f.write(page.content())
                        logger.info("Dumped page source to debug_page_source.html")
                        
                        try:
                            # Try to find the button by text content using XPath which is often more robust for full text matching
                            # XPath looking for a button that contains "Publicar ahora"
                            confirm_btn = page.locator("//button[contains(., 'Publicar ahora')] | //button[contains(., 'Post now')]").first
                            
                            if confirm_btn.is_visible():
                                logger.info("Found confirmation button via XPath! Clicking...")
                                confirm_btn.click()
                                time.sleep(2)
                            else:
                                logger.warning("Confirmation button not found via XPath. Checking frames...")
                                # Check frames just in case
                                for frame in page.frames:
                                    btn = frame.locator("//button[contains(., 'Publicar ahora')] | //button[contains(., 'Post now')]").first
                                    if btn.is_visible():
                                        logger.info(f"Found button in frame {frame.name}! Clicking...")
                                        btn.click()
                                        break
                                
                        except Exception as e:
                            logger.error(f"Error handling modal: {e}")

                        # Now wait for the button to DISAPPEAR (indicating navigation)
                        logger.info("Waiting for Post button to disappear / Navigation...")
                        try:
                            post_btn.wait_for(state="hidden", timeout=15000)
                            logger.info("Post button hidden. Success.")
                        except:
                             logger.warning("Post button still active. Upload might have failed.")
                            
                    else:
                        logger.error("Post button never became enabled.")
                        page.screenshot(path="debug_error_post_disabled.png")
                        return False
                        
                except Exception as e:
                    logger.error(f"Error clicking Post: {e}")
                    raise e
                
                # Wait for confirmation
                logger.info("Waiting for confirmation (Redirect or Modal)...")
                try:
                    # Extended timeout for upload processing
                    page.wait_for_url("**/content**", timeout=30000)
                    logger.info("Redirected to content page. SUCCESS.")
                except:
                    logger.warning("No redirect detected. Checking for success modal...")
                    # Screenshot status at this point
                    page.screenshot(path="debug_check_success.png")
                    
                    # Check for "Video uploaded" text
                    if page.locator("text='Video uploaded'").count() > 0:
                         logger.info("Success message detected.")
                    elif page.locator("text='Manage your posts'").count() > 0:
                         logger.info("Manage posts link detected.")
                    else:
                         logger.warning("No confirmation found. Dump screenshot.")
                         page.screenshot(path="debug_warning_no_confirmation.png")

                # Final grace period - Extended for GitHub Actions to ensure upload processes
                logger.info("Waiting 60s to ensure upload finalizing...")
                time.sleep(60)
                return True

            except Exception as e:
                logger.error(f"Error during upload execution: {e}")
                # Capture screenshot for debugging
                timestamp = int(time.time())
                page.screenshot(path=f"error_upload_{timestamp}.png")
                raise e
            finally:
                browser.close()

if __name__ == "__main__":
    # Test stub
    pass
