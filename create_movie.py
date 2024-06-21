from moviepy.editor import ImageClip, concatenate_videoclips, concatenate_audioclips, AudioFileClip
import requests
from PIL import Image
from io import BytesIO
import os
import uuid
from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

# Load environment variables from .env file
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


def download_image(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        image_path = f"{image_url.split('/')[-1]}.png"
        image.save(image_path)
        return image_path
    else:
        raise Exception(f"Failed to download image from {image_url}")


# ElevenLabs
def generate_narration(text):
    print(f"Generating narration for text: {text}")
    response = client.text_to_speech.convert(
        # Adam
        voice_id="pNInz6obpgDQGcFmaJgB",
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    save_file_path = f"{uuid.uuid4()}.mp3"
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{save_file_path}: A new audio file was saved successfully!")
    return save_file_path


def create_movie(image_urls, narrations, output_file="output_video.mp4", fps=24):
    clips = []
    audio_clips = []
    audio_files = []

    for i, image_url in enumerate(image_urls):
        # Download the image
        image_path = download_image(image_url)
        print(f"Downloaded image {i + 1}: {image_path}")  # Debug info

        # Generate narration audio
        narration = narrations[i]
        audio_file = generate_narration(narration)
        audio_clip = AudioFileClip(audio_file)
        audio_duration = audio_clip.duration
        audio_clips.append(audio_clip.set_duration(audio_duration))
        audio_files.append(audio_file)
        print(f"Generated narration {i + 1}: {audio_file} with duration {audio_duration}")  # Debug info

        # Create an ImageClip for each image
        image_clip = ImageClip(image_path).set_duration(audio_duration)
        clips.append(image_clip)

    # Concatenate all the video clips
    video = concatenate_videoclips(clips, method="compose")
    # Concatenate all the audio clips
    audio = concatenate_audioclips(audio_clips)

    # Set audio to the video
    final_video = video.set_audio(audio)
    # Write the result to a file with fps specified and ensure audio codec is AAC
    final_video.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=fps)
    print(f"Video written to {output_file}")  # Debug info

    # Clean up audio files
    for audio_file in audio_files:
        os.remove(audio_file)


if __name__ == "__main__":
    image_urls = ["https://example.com/image1.png", "https://example.com/image2.png"]
    narrations = ["Narration for image 1", "Narration for image 2"]
    create_movie(image_urls, narrations)
