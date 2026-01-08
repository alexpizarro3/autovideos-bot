import logging
import os
from src.uploaders.uploader import TikTokUploader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_upload_only():
    # Find the latest video
    output_dir = "output"
    videos = [f for f in os.listdir(output_dir) if f.endswith(".mp4")]
    if not videos:
        print("No videos found to upload.")
        return
    
    # Sort by time
    latest_video = sorted(videos, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))[-1]
    video_path = os.path.join(os.getcwd(), output_dir, latest_video)
    
    print(f"Testing upload for: {video_path}")
    
    # Init Uploader
    # Ensure correct cookie path
    cwd = os.getcwd()
    cookie_path = os.path.join(cwd, "tiktok_cookies.json")
    
    uploader = TikTokUploader(cookies_path=cookie_path)
    
    if not os.path.exists(uploader.cookies_path):
        print("Cookies not found!")
        return

    try:
        title = "Daily Fact: Psychological hacks (Test Upload)"
        hashtags = ["#test", "#ai", "#automation"]
        
        uploader.upload_video(video_path, title, hashtags)
        print("Upload test completed (check browser/logs).")
        
    except Exception as e:
        print(f"Upload failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_upload_only()
