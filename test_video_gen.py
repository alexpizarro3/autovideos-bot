import logging
import os
import numpy as np
from PIL import Image
from moviepy.editor import *

# Monkeypatch
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gen():
    # Pick a recent valid scene pair
    img_path = "temp/scene_5_1767755292.jpg"
    audio_path = "temp/scene_5_1767755292.mp3"
    
    if not os.path.exists(img_path):
        print(f"File not found: {img_path}")
        return

    print(f"Testing with {img_path}")
    
    try:
        # Load Image using PIL
        pil_img = Image.open(img_path).convert('RGB')
        print(f"PIL Image size: {pil_img.size}")
        
        img_array = np.array(pil_img)
        print(f"Numpy Array shape: {img_array.shape}, Dtype: {img_array.dtype}")
        
        # Audio
        audio_clip = AudioFileClip(audio_path).set_duration(2)
        
        # Create two identical clips
        clip1 = ImageClip(img_array).set_duration(2).resize(height=1920)
        # Resize logic simplified for test
        if clip1.w < 1080: clip1 = clip1.resize(width=1080)
        clip1 = clip1.crop(x1=clip1.w/2 - 540, width=1080, height=1920)
        
        # Ken Burns (Dynamic Resize)
        print("Applying Ken Burns...")
        zoom_factor = 1.15
        duration = 2
        clip1 = clip1.resize(lambda t: 1 + (zoom_factor - 1) * t / duration)
        
        # Crossfade
        print("Applying Crossfadein...")
        clip1 = clip1.crossfadein(0.5)
        
        clip1 = clip1.set_audio(audio_clip) # Add audio to clip 1
        
        clip2 = clip1.copy() # duplicate

        # Concatenate
        print("Concatenating...")
        final_clip = concatenate_videoclips([clip1, clip2], method="compose")

        # Write Video
        output = "debug_concat_audio.mp4"
        final_clip.write_videofile(
            output, 
            fps=24, 
            codec='libx264',
            audio_codec='aac'
        )
        
        print(f"Video written to {output}")
        print(f"File size: {os.path.getsize(output)} bytes")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gen()
