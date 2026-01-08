import os
from dotenv import load_dotenv

load_dotenv()

# General Config
VIDEO_ORIENTATION = "portrait" # portrait, landscape, square
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 24

# Directories
ASSETS_DIR = "assets"
TEMP_DIR = "temp"
OUTPUT_DIR = "output"

# niches / topics
NICHES = [
    "Mind-blowing scientific facts",
    "History's most bizarre events",
    "Future technology predictions",
    "Psychological hacks and tricks",
    "Space mysteries and anomalies",
    "Deep ocean discoveries"
]

# API Keys (Loaded from env)
HF_TOKEN = os.getenv("HF_TOKEN")
