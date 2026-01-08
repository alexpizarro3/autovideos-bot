import logging
import os
import json
import time

try:
    from kling import VideoGen
except ImportError:
    pass

logger = logging.getLogger(__name__)

class KlingGenerator:
    def __init__(self, cookie_path: str = "kling_cookie.txt"):
        self.cookie_path = cookie_path
        self.cookie = self._load_cookie()
        self.gen = None
        if self.cookie:
            self._init_api()

    def _load_cookie(self) -> str:
        """Loads the Kling AI cookie from a file."""
        if not os.path.exists(self.cookie_path):
            logger.warning(f"Kling cookie file not found at: {self.cookie_path}")
            return None
        
        try:
            with open(self.cookie_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Handle JSON format often exported by cookie editors
                if content.startswith('[') or content.startswith('{'):
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            cookie_parts = []
                            for c in data:
                                if 'name' in c and 'value' in c:
                                    cookie_parts.append(f"{c['name']}={c['value']}")
                            cookie_str = "; ".join(cookie_parts)
                            logger.info(f"Parsed cookie string (first 50 chars): {cookie_str[:50]}...")
                            return cookie_str
                    except json.JSONDecodeError:
                        pass
                return content
        except Exception as e:
            logger.error(f"Error reading cookie file: {e}")
            return None

    def _init_api(self):
        try:
            if 'VideoGen' not in globals():
                 logger.error("Kling library not imported.")
                 return

            logger.info("Initializing Kling AI VideoGen...")
            self.gen = VideoGen(self.cookie)
            logger.info("Kling AI VideoGen initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Kling VideoGen: {e}")

    def generate_video(self, prompt: str, output_path: str, duration_sec: int = 5) -> str:
        """
        Generates a video from a text prompt and saves it to output_path.
        """
        if not self.gen:
            logger.error("Kling API not initialized.")
            return None

        logger.info(f"Generating Kling video for prompt: '{prompt[:30]}...'")

        try:
            # VideoGen.save_video(prompt, output_dir, ...)
            # The library saves with its own filename based on prompt timestamp probably.
            # We need to see how it saves. 
            # documentation says: save_video(prompt, output_dir, ...)
            # It implies it downloads to the dir. We might need to rename it or pass full path if supported?
            # actually looking at signature: prompt, output_dir. 
            # So we pass the folder of output_path, then find the file and rename it.
            
            output_dir = os.path.dirname(output_path)
            # Ensure dir exists if it's not the current directory
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            # We need to track what file was created.
            # Let's list files before and after? Or just use get_video returning a list of urls/paths?
            # get_video returns a list. Doc says: -> list.
            # Let's use get_video checking for URLs, then download manually to control filename.
            
            video_links = self.gen.get_video(
                prompt=prompt,
                model_name="1.0" # Use 1.0 for better success rate on free tier? or 1.5?
                 # Defaults to 1.0 in signature.
            )
            
            if not video_links:
                raise Exception("No video links returned.")
            
            # Returns a list of strings (URLs)
            video_url = video_links[0]
            logger.info(f"Video generated at URL: {video_url}")
            
            # Download
            import requests
            response = requests.get(video_url)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
                
            logger.info(f"Video saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating video: {e}")
            return None
