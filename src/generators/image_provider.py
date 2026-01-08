import logging
import requests
import time
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageProvider:
    def __init__(self, width=1080, height=1920):
        """
        Initialize the Image Provider.
        Pollinations.ai is free and no token is needed.
        """
        self.width = width
        self.height = height

    def generate_image(self, prompt: str, output_file: str) -> str:
        """
        Generates an image for the given prompt and saves it to output_file.
        Returns the path to the output file.
        """
        for attempt in range(1, 4):
            try:
                logger.info(f"Generating image for prompt (Attempt {attempt}/3): '{prompt[:30]}...' -> {output_file}")
                
                # URL encode the prompt
                encoded_prompt = quote(prompt)
                
                # Add aggressive delay to avoid rate limits (GitHub Actions IPs are often throttled)
                logger.info("Waiting 30s to respect Pollinations rate limit...")
                time.sleep(30)

                # Construct URL with random seed to ensure freshness
                import random
                seed = random.randint(0, 999999)
                url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={self.width}&height={self.height}&nologo=true&model=flux&seed={seed}" 
                
                response = requests.get(url, timeout=60) # Increased timeout to 60s
                response.raise_for_status()
                
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                logger.info("Image saved successfully.")
                return output_file

            except Exception as e:
                logger.warning(f"Error generating image (Attempt {attempt}): {e}")
                if attempt == 3:
                    logger.error("Failed to generate image after 3 attempts.")
                    raise e
                time.sleep(2) # Wait before retry

if __name__ == "__main__":
    ip = ImageProvider()
    ip.generate_image("A futuristic city on Mars, cinematic, realistic, 8k", "test_mars.jpg")
