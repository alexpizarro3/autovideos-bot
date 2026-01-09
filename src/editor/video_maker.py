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
                
                # Apply "Ken Burns" (Zoom In) effect for static images
                if not scene.get('video_path'):
                    clip = self._apply_ken_burns(clip)

                # Set Audio
                clip = clip.set_audio(audio)
                
                # Add Captions (Overlay Text)
                text = scene.get('text', '')
                if text:
                    txt_clip = self._create_caption_clip(text, duration, filesize=(self.width, self.height))
                    clip = CompositeVideoClip([clip, txt_clip])

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
        # compose needed for crossfade or composite clips
        final_video = concatenate_videoclips(clips, method="compose") 
        
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

    def _apply_ken_burns(self, clip, zoom_factor=1.1):
        """
        Applies a slow zoom-in effect.
        """
        return clip.resize(lambda t: 1 + (zoom_factor - 1) * t / clip.duration)

    def _create_caption_clip(self, text, duration, filesize):
        """
        Creates a transparent ImageClip with text using PIL (No ImageMagick required).
        """
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        w, h = filesize
        
        # Create transparent image
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load font (try standard windows font)
        try:
            # Impact or Arial Black are good for memes/shorts
            font_path = "C:\\Windows\\Fonts\\impact.ttf"
            if not os.path.exists(font_path):
                font_path = "arial.ttf" # Fallback
            font = ImageFont.truetype(font_path, size=70)
        except:
            font = ImageFont.load_default()

        # Text wrapping
        lines = textwrap.wrap(text, width=20) # Short width for big text
        
        # Calculate text height to center it
        # Basic estimation
        line_height = 80 
        total_text_height = len(lines) * line_height
        y_text = h - total_text_height - 250 # Position near bottom

        # Draw text with outline
        shadow_color = "black"
        fill_color = "white"
        stroke_width = 4
        
        for line in lines:
            # We use getbbox usually but let's keep it simple for now
            # Center horizontally
            left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
            text_width = right - left
            x_text = (w - text_width) / 2
            
            # Stroke (Manual lazy stroke)
            for x_off in range(-stroke_width, stroke_width+1):
                for y_off in range(-stroke_width, stroke_width+1):
                    draw.text((x_text+x_off, y_text+y_off), line, font=font, fill=shadow_color)
            
            draw.text((x_text, y_text), line, font=font, fill=fill_color)
            y_text += line_height

        # Convert to Moviepy ImageClip
        img_np = np.array(img)
        txt_clip = ImageClip(img_np).set_duration(duration)
        return txt_clip

if __name__ == "__main__":
    pass
