
import logging
import os
import time
from src.generators.kling_generator import KlingGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_kling_video_generation():
    logger.info("Starting Kling AI video generation test...")

    # Initialize generator
    generator = KlingGenerator(cookie_path="kling_cookie.txt")
    
    if not generator.cookie:
        logger.error("Failed to load cookie. Please check 'kling_cookie.txt'.")
        return

    # Define a simple prompt
    prompt = "A futuristic city with flying cars, cinematic, 8k, realistic"
    output_path = "debug_kling_test_video.mp4"

    # Attempt generation
    try:
        logger.info(f"Generating video for prompt: '{prompt}'")
        video_path = generator.generate_video(prompt, output_path, duration_sec=5)
        
        if video_path and os.path.exists(video_path):
            logger.info(f"SUCCESS! Video generated at: {video_path}")
            logger.info(f"File size: {os.path.getsize(video_path)} bytes")
        else:
            logger.error("FAILED to generate video (no file created or None returned).")

    except Exception as e:
        logger.error(f"Exception during test: {e}")

if __name__ == "__main__":
    test_kling_video_generation()
