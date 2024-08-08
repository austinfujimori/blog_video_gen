from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, ColorClip, CompositeAudioClip, VideoFileClip
import requests
from PIL import Image
from io import BytesIO
import os
import uuid
from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from moviepy.video.fx.all import speedx
import replicate
import json
import subprocess

os.environ['IMAGEMAGICK_BINARY'] = '/opt/homebrew/bin/magick'


load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


FONT_PATH = "Arial-Bold.ttf"
MAX_WORDS_PER_LINE = 5


image_paths = ["image6.png", "image7.png"]
prompts = ["cool spiraling thing", "electric wiring with white connection strings moving across the air"]
file_mount_names = ["image6.png", "image7.png"]
sample_names = ["gen_video_6", "gen_video_7"]
durations = ["8s", "8s"]
resolutions = ["480p", "480p"]
aspect_ratios = ["9:16","9:16"]

command = [
     "modal", "run", "generate_video.py::main",
     "--image-paths", json.dumps(image_paths),
     "--prompts", json.dumps(prompts),
     "--file-mount-names", json.dumps(file_mount_names),
     "--sample-names", json.dumps(sample_names),
     "--durations", json.dumps(durations),
     "--resolutions", json.dumps(resolutions),
     "--aspect-ratios", json.dumps(aspect_ratios)
]

try:
     result = subprocess.run(command, check=True, capture_output=True, text=True)
     print("Modal run command executed successfully.")
     print(f"Standard Output:\n{result.stdout}")
     print(f"Standard Error:\n{result.stderr}")
except subprocess.CalledProcessError as e:
     print(f"Modal run command failed with exit code {e.returncode}")
     print(f"Standard Output:\n{e.stdout}")
     print(f"Standard Error:\n{e.stderr}")