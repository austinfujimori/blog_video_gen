from scrape_info import get_blog_info
import os
import subprocess
import json
from create_movie import create_movie
import re

# for clearing modal volume

def list_files_in_volume(volume_name):
    command = f"modal volume ls {volume_name}"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.returncode == 0:
            files = result.stdout.strip().split("\n")
            return files
        else:
            print(f"Failed to list files in volume with exit code {result.returncode}")
            print(f"Standard Output:\n{result.stdout}")
            print(f"Standard Error:\n{result.stderr}")
            return []
    except subprocess.CalledProcessError as e:
        print(f"Error listing files in volume: {e}")
        return []

def delete_files_in_volume(volume_name, files):
    for file in files:
        command = f"modal volume rm {volume_name} {file}"
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"File {file} deleted successfully.")
            else:
                print(f"Failed to delete file {file} with exit code {result.returncode}")
                print(f"Standard Output:\n{result.stdout}")
                print(f"Standard Error:\n{result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Error deleting file {file}: {e}")

def clear_modal_cache(volume_name):
    files = list_files_in_volume(volume_name)
    if files:
        delete_files_in_volume(volume_name, files)
    else:
        print("No files to delete in volume.")


















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

def upload_image_to_volume(local_image_path, remote_image_name, volume_name):
    command = f"modal volume put {volume_name} {local_image_path} {remote_image_name}"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("Image uploaded to volume successfully.")
        print(f"Standard Output:\n{result.stdout}")
        print(f"Standard Error:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr:
            print("Image already exists in volume. Skipping upload.")
        else:
            print(f"Image upload failed with exit code {e.returncode}")
            print(f"Standard Output:\n{e.stdout}")
            print(f"Standard Error:\n{e.stderr}")

def run_modal_main(image_paths, prompts, file_mount_names, sample_names, durations, resolutions, aspect_ratios):
    # Upload images to volume
    for idx in range(len(image_paths)):
        upload_image_to_volume(image_paths[idx], file_mount_names[idx], "model-cache-volume")

    # Prepare command to run generate_video.py
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
        
        
        
    

def remove_quotes(image_descriptions):
    return [desc.replace('"', '').replace("'", '') for desc in image_descriptions]






def create_movie(image_urls, image_descriptions, narrations, music_prompt, narration_speed=1.0, output_file="output_video.mp4", fps=24, resolution="480p", aspect_ratio="9:16"):
    image_descriptions = remove_quotes(image_descriptions)
    

    
    audio_clips = []
    audio_files = []
    sum_of_clips_duration = 0
    images_paths = []

    # Generate narration audio and calculate the sum of clip durations
    for i in range(11):
        # Download the image and save the path

        images_paths.append(os.path.join('images', f"image{i+1}.png"))

    
     
    durations = []
    prompts = []
    file_mount_names = []
    sample_names = []
    resolutions = []
    aspect_ratios = []
    for i, image_path in enumerate(images_paths):
        durations.append("2s")
        
        # args for create videos
        file_mount_names.append(f"image{i}.png")
        sample_names.append(f"gen_video_{i}")
        resolutions.append(resolution)
        aspect_ratios.append(aspect_ratio)
        prompts.append(image_descriptions[i])

    
    run_modal_main(images_paths, prompts, file_mount_names, sample_names, durations, resolutions, aspect_ratios)












if __name__ == "__main__":
    
    
    clear_modal_cache("model-cache-volume")

    image_urls=["https://oaidalleapiprodscus.blob.core.windows.net/private/org-Ezo8UMeBcApqtqraXRz7chxn/user-oE1H8wX7wk2DYKtlL8cqwCfR/img-YNHdXuka1HXusskUp8RvYd92.png?st=2024-07-16T18%3A23%3A13Z&se=2024-07-16T20%3A23%3A13Z&sp=r&sv=2023-11-03&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-07-15T21%3A57%3A21Z&ske=2024-07-16T21%3A57%3A21Z&sks=b&skv=2023-11-03&sig=EXFAuwMd1e/f4c/GK1gr8vL/isPonQftZBCVCn5BMbY%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-Ezo8UMeBcApqtqraXRz7chxn/user-oE1H8wX7wk2DYKtlL8cqwCfR/img-80BCFDxNfMizBj0vBqNUyvaE.png?st=2024-07-16T18%3A23%3A25Z&se=2024-07-16T20%3A23%3A25Z&sp=r&sv=2023-11-03&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-07-15T21%3A40%3A48Z&ske=2024-07-16T21%3A40%3A48Z&sks=b&skv=2023-11-03&sig=0vg2VM/RHp/GbvtJC9n0NEJIkIyyRejwxa%2BACuTFar8%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-Ezo8UMeBcApqtqraXRz7chxn/user-oE1H8wX7wk2DYKtlL8cqwCfR/img-NED6KM9mgX7OOM51Cq1algT5.png?st=2024-07-16T18%3A23%3A40Z&se=2024-07-16T20%3A23%3A40Z&sp=r&sv=2023-11-03&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-07-15T21%3A35%3A43Z&ske=2024-07-16T21%3A35%3A43Z&sks=b&skv=2023-11-03&sig=9Q4JJzHRwfWdqWrtTAiTO9UG5LhnKR/sg16abo2at9g%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-Ezo8UMeBcApqtqraXRz7chxn/user-oE1H8wX7wk2DYKtlL8cqwCfR/img-4ylMJIAxq8oHvWIkS69cfAPv.png?st=2024-07-16T18%3A23%3A50Z&se=2024-07-16T20%3A23%3A50Z&sp=r&sv=2023-11-03&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-07-15T21%3A36%3A37Z&ske=2024-07-16T21%3A36%3A37Z&sks=b&skv=2023-11-03&sig=BEZGB/yynu0uIUvNw71i1wcbwVgWoGqwLyLFwkRx1vw%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-Ezo8UMeBcApqtqraXRz7chxn/user-oE1H8wX7wk2DYKtlL8cqwCfR/img-S00DaDMnGfcEgnGjs4mqLqtW.png?st=2024-07-16T18%3A24%3A04Z&se=2024-07-16T20%3A24%3A04Z&sp=r&sv=2023-11-03&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-07-15T21%3A36%3A48Z&ske=2024-07-16T21%3A36%3A48Z&sks=b&skv=2023-11-03&sig=HghXa/XGwNQHWiuxyaVqjZ34co%2B/hsReVmCow0%2BeJXE%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-Ezo8UMeBcApqtqraXRz7chxn/user-oE1H8wX7wk2DYKtlL8cqwCfR/img-QJySKaBdFpPB23JlEj3DnToT.png?st=2024-07-16T18%3A24%3A17Z&se=2024-07-16T20%3A24%3A17Z&sp=r&sv=2023-11-03&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-07-15T21%3A38%3A10Z&ske=2024-07-16T21%3A38%3A10Z&sks=b&skv=2023-11-03&sig=QKaPh4n74hy%2BjJykJIlLT%2BmTpbUJZo6rE5V%2BjujFvuQ%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-Ezo8UMeBcApqtqraXRz7chxn/user-oE1H8wX7wk2DYKtlL8cqwCfR/img-QmqMrfsKHM3RKY7kNigfqQFY.png?st=2024-07-16T18%3A24%3A30Z&se=2024-07-16T20%3A24%3A30Z&sp=r&sv=2023-11-03&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-07-16T00%3A09%3A32Z&ske=2024-07-17T00%3A09%3A32Z&sks=b&skv=2023-11-03&sig=ErCLUaPeoYBhT78nBDBmSjYzjV4g8Gu3UUoYsCII1xY%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-Ezo8UMeBcApqtqraXRz7chxn/user-oE1H8wX7wk2DYKtlL8cqwCfR/img-qSbEByItfZh1vGy4kAdH6sZM.png?st=2024-07-16T18%3A24%3A43Z&se=2024-07-16T20%3A24%3A43Z&sp=r&sv=2023-11-03&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-07-16T03%3A38%3A30Z&ske=2024-07-17T03%3A38%3A30Z&sks=b&skv=2023-11-03&sig=bTml5Qa4TexV%2Bm0zSKgp2c2Rvd9y1jauBeadWcs5/9E%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-Ezo8UMeBcApqtqraXRz7chxn/user-oE1H8wX7wk2DYKtlL8cqwCfR/img-ib6ImTaqAIKaXpIwRpQepzTj.png?st=2024-07-16T18%3A25%3A00Z&se=2024-07-16T20%3A25%3A00Z&sp=r&sv=2023-11-03&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-07-15T21%3A32%3A56Z&ske=2024-07-16T21%3A32%3A56Z&sks=b&skv=2023-11-03&sig=9BdlrIJWpRva6pYrCPPV8y4CE3RyzOcelb7A12DjRcE%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-Ezo8UMeBcApqtqraXRz7chxn/user-oE1H8wX7wk2DYKtlL8cqwCfR/img-J3OSHiHt2CqYCnDRbPByLHEf.png?st=2024-07-16T18%3A25%3A10Z&se=2024-07-16T20%3A25%3A10Z&sp=r&sv=2023-11-03&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-07-15T21%3A40%3A55Z&ske=2024-07-16T21%3A40%3A55Z&sks=b&skv=2023-11-03&sig=GWthm4%2BcI/XFl9nyH00eYZ2py9ULWNs76rJwir7/4H0%3D","https://oaidalleapiprodscus.blob.core.windows.net/private/org-Ezo8UMeBcApqtqraXRz7chxn/user-oE1H8wX7wk2DYKtlL8cqwCfR/img-X3m8KkJxRupc7VHBziIZgNBv.png?st=2024-07-16T18%3A25%3A21Z&se=2024-07-16T20%3A25%3A21Z&sp=r&sv=2023-11-03&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-07-15T21%3A36%3A38Z&ske=2024-07-16T21%3A36%3A38Z&sks=b&skv=2023-11-03&sig=043gYGi/4miwKJbH5q8%2B4vKB6MXKzzZ/JZhht1zKfs0%3D"]

    image_descriptions = ["A clock striking midnight, with confetti and balloons in the background, symbolizing the start of a new year."," A person holding a sign that says \"Same Old, Same Old\" with a shrugging emoji, indicating a lack of enthusiasm for change.","A small notebook with eight sticky notes attached, each representing one of the habits to focus on."," A tiny workout enthusiast, wearing a superhero cape, riding a bike or jogging in place on the sidewalk, showing the impact of small changes."," A cityscape with a subway train in the distance, and a person stepping off at an earlier stop, with a speech bubble saying \"I'm taking a detour...to fitness!\""," A graph showing a gradual increase in physical activity, with a running shoe or a fitness tracker as the icon."," A glass of water with a few ice cubes and a straw, surrounded by healthy snacks like fruits and nuts, promoting hydration."," A magnifying glass zooming in on a single water droplet, highlighting the importance of staying hydrated."," A person sipping from a refillable water bottle, with a radiant aura surrounding them, emphasizing the energy boost."," A speedometer gauge with a needle moving up, indicating increased metabolism, and a burst of energy radiating from the center."," A person enjoying a post-workout snack, with a satisfied expression and a thumbs-up, signaling the benefits of adopting these habits. 😊"]
    
    narrations =["As we step into the new year,","we're not looking to revolutionize our lives.","Instead, let's focus on eight small habits","that can have a big impact.","Imagine taking your daily commute and turning it into a workout.","By getting off the subway or bus a stop early, you'll","get your blood pumping without committing to a marathon session.","Hydrate and recharge with an extra","glass of water throughout the day.","It's a simple habit that will boost your","metabolism and give you the energy you need" ]
    
    music_prompt = "Here's a prompt for a music generator to create a soundtrack for this story:**Title:** \"Step by Step\"**Mood:** Uplifting, Motivational, and Energizing**Instruments:** * Acoustic guitar as"

    
    
    narration_speed = 1
    output_file="movie.mp4"
    fps=24
    resolution="480p"
    aspect_ratio="9:16"
    
    create_movie(image_urls, image_descriptions, narrations, music_prompt, narration_speed,output_file,fps,resolution,aspect_ratio)