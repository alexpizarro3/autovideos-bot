import os
import logging
import random
import time
from datetime import datetime
from dotenv import load_dotenv

from config import NICHES, TEMP_DIR, OUTPUT_DIR, VIDEO_WIDTH, VIDEO_HEIGHT
from generators.llm_provider import LLMProvider
from generators.voice_provider import VoiceProvider
from generators.image_provider import ImageProvider
from editor.video_maker import VideoMaker
from uploaders.uploader import TikTokUploader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_dirs():
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def cleanup_temp():
    # Optional: Clean up temp files
    pass

def main():
    load_dotenv()
    ensure_dirs()
    
    logger.info("Starting Daily Video Bot Workflow (Free Stack)...")
    
    # 1. Select Topic
    topic = random.choice(NICHES)
    logger.info(f"Selected Topic: {topic}")

    # 2. Generate Script
    llm = LLMProvider()
    script_response = llm.generate_script(topic)
    
    if not script_response or 'scenes' not in script_response:
        logger.error("Failed to generate script or invalid format. Exiting.")
        return

    scenes_data = script_response['scenes']
    video_title = script_response.get('title', f"Daily Fact: {topic}")
    video_description = script_response.get('description', "")
    video_hashtags = script_response.get('hashtags', ["#fyp", "#genai"])

    # 3. Generate Assets (Voice & Images)
    voice_provider = VoiceProvider()
    image_provider = ImageProvider(width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
    
    scenes = []
    
    for i, scene_data in enumerate(scenes_data):
        try:
            timestamp = int(time.time())
            
            # Voice
            text = scene_data.get("text", "")
            audio_path = os.path.join(TEMP_DIR, f"scene_{i}_{timestamp}.mp3")
            voice_provider.generate_voice(text, audio_path)
            
            # Visuals (Image only - Free Stack)
            prompt = scene_data.get("image_prompt", "")
            
            img_out = os.path.join(TEMP_DIR, f"scene_{i}_{timestamp}.jpg")
            image_path = image_provider.generate_image(prompt, img_out)
            
            scenes.append({
                "text": text,
                "audio_path": audio_path,
                "image_path": image_path,
                "video_path": None  # No video generator
            })
            
        except Exception as e:
            logger.error(f"Error processing scene {i}: {e}")
            continue

    if not scenes:
        logger.error("No scenes were successfully generated. Exiting.")
        return

    # 4. Compile Video
    video_maker = VideoMaker(width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_video_path = os.path.join(OUTPUT_DIR, f"daily_video_{timestamp}.mp4")
    
    try:
        video_maker.make_video(scenes, output_video_path)
        logger.info(f"Video created successfully: {output_video_path}")
    except Exception as e:
        logger.error(f"Failed to create video: {e}")
        return

    # 5. Upload (Dry run check or actual upload)
    # Check for upload flag or environment variable
    # For now, we instantiate the uploader but might skip actual upload if no cookies
    
    # Ensure cookie path is absolute to avoid CWD issues
    # Assuming cookies are in the project root (where main.py's parent's parent is, or CWD)
    # Better: Use the CWD or script directory.
    project_root = os.getcwd() 
    cookie_path = os.path.join(project_root, "tiktok_cookies.json")
    
    uploader = TikTokUploader(cookies_path=cookie_path)
    if os.path.exists(uploader.cookies_path):
        try:
            # metadata
            full_title = f"{video_title} - {video_description}"
            logger.info(f"Attempting upload to TikTok with title: {full_title}")
            logger.info(f"Hashtags: {video_hashtags}")
            
            uploader.upload_video(output_video_path, full_title, video_hashtags)
            logger.info("Upload logic executed.")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
    else:
        logger.info("Skipping upload: No cookies found.")

    logger.info("Workflow completed.")

if __name__ == "__main__":
    main()
