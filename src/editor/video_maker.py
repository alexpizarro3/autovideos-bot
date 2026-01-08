import logging
import os
import random
import numpy as np
from PIL import Image
from moviepy.editor import *

# Monkeypatch for moviepy 1.x compatibility with Pillow 10+
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

logger = logging.getLogger(__name__)

class VideoMaker:
    def __init__(self, width=1080, height=1920):
        self.width = width
        self.height = height

    def make_video(self, scenes: list[dict], output_file: str) -> str:
        """
        Compiles the video from scenes.
        scenes: list of dicts with 'image_path', 'audio_path'
        """
        clips = []
        
        logger.info(f"Compiling video with {len(scenes)} scenes to {output_file}")
        
        for scene in scenes:
            try:
                # Load Audio
                audio = AudioFileClip(scene['audio_path'])
                duration = audio.duration + 0.5 # Add a little pause padding
                
                clip = None
                
                # Check if we have a generated video
                if 'video_path' in scene and scene['video_path'] and os.path.exists(scene['video_path']):
                    logger.info(f"Using video source for scene: {scene['video_path']}")
                    # Load Video
                    video_clip = VideoFileClip(scene['video_path'])
                    
                    # Loop video if it is shorter than audio
                    if video_clip.duration < duration:
                        # Crossfade loop or simple loop? Simple loop is safer for now
                        video_clip = video_clip.loop(duration=duration)
                    else:
                        video_clip = video_clip.subclip(0, duration)
                        
                    clip = video_clip
                else:
                    logger.info(f"Using image source for scene: {scene['image_path']}")
                    # Load Image using PIL to bypass imageio backend issues
                    pil_img = Image.open(scene['image_path']).convert('RGB')
                    img_array = np.array(pil_img)
                    clip = ImageClip(img_array).set_duration(duration)

                # Resize/Crop to fill screen (Logic applies to both Image and Video)
                # Ensure we are filling the target 9:16 frame
                target_ratio = self.width / self.height
                clip_ratio = clip.w / clip.h
                
                if clip_ratio > target_ratio:
                    # Clip is wider than target -> Resize by height, crop width
                    clip = clip.resize(height=self.height)
                    clip = clip.crop(x1=clip.w/2 - self.width/2, width=self.width, height=self.height)
                else:
                    # Clip is taller/narrower -> Resize by width, crop height (or just fit width)
                    clip = clip.resize(width=self.width)
                    # Center vertically usually
                    clip = clip.crop(y1=clip.h/2 - self.height/2, width=self.width, height=self.height)

                # Set Audio
                clip = clip.set_audio(audio)
                
                # Explicitly set fps to avoid issues
                clip = clip.set_fps(24)
                
                clips.append(clip)
                
            except Exception as e:
                logger.error(f"Error processing scene: {e}")
                continue

        if not clips:
            raise ValueError("No clips were generated.")

        # Concatenate
        logger.info("Concatenating clips...")
        final_video = concatenate_videoclips(clips, method="compose") # compose needed for crossfade
        
        # Write File
        logger.info(f"Writing video file to {output_file}...")
        final_video.write_videofile(
            output_file, 
            fps=24, 
            codec='libx264', 
            audio_codec='aac', 
            threads=4,
            preset='medium'
        )
        
        return output_file

if __name__ == "__main__":
    pass
