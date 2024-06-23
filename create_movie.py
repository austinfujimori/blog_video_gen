from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips, AudioFileClip, ColorClip
import requests
from PIL import Image
from io import BytesIO
import os
import uuid
from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from moviepy.video.fx.all import speedx  # Import the speedx function

# Set the path to the ImageMagick executable
os.environ['IMAGEMAGICK_BINARY'] = '/opt/homebrew/bin/magick'

# Load environment variables from .env file
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Path to the custom font file
FONT_PATH = "Arial-Bold.ttf"  # Replace with the path to your font file

MAX_WORDS_PER_LINE = 10  # Adjust this number based on your preference


def download_image(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        image_path = f"{image_url.split('/')[-1]}.png"
        image.save(image_path)
        return image_path
    else:
        raise Exception(f"Failed to download image from {image_url}")


def generate_narration(text, narration_speed):
    print(f"Generating narration for text: {text}")
    response = client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",  # Adam pre-made voice
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

    # Adjust narration speed
    audio_clip = AudioFileClip(save_file_path)
    adjusted_audio_clip = speedx(audio_clip, narration_speed)
    adjusted_audio_path = f"{uuid.uuid4()}_adjusted.mp3"
    adjusted_audio_clip.write_audiofile(adjusted_audio_path)

    return adjusted_audio_path


def split_text_into_lines(text, max_words_per_line):
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        if len(current_line) + len(word.split()) <= max_words_per_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def create_movie(image_urls, narrations, narration_speed=1.0, output_file="output_video.mp4", fps=24):
    clips = []
    audio_clips = []
    audio_files = []

    for i, image_url in enumerate(image_urls):
        # Download the image
        image_path = download_image(image_url)
        print(f"Downloaded image {i + 1}: {image_path}")  # Debug info

        # Generate narration audio
        narration = narrations[i]
        if not narration.strip():
            print(f"Skipping empty narration for slide {i + 1}")
            continue

        audio_file = generate_narration(narration, narration_speed)
        audio_clip = AudioFileClip(audio_file)
        audio_duration = audio_clip.duration
        audio_clips.append(audio_clip.set_duration(audio_duration))
        audio_files.append(audio_file)
        print(f"Generated narration {i + 1}: {audio_file} with duration {audio_duration}")  # Debug info

        # Create an ImageClip for each image
        image_clip = ImageClip(image_path).set_duration(audio_duration)

        # Split the narration into lines for subtitles
        lines = split_text_into_lines(narration, MAX_WORDS_PER_LINE)
        if not lines:
            print(f"No lines generated for slide {i + 1}")
            continue

        line_duration = audio_duration / len(lines)

        # Create clips for each line of subtitles
        line_clips = []
        for line in lines:
            # Create a TextClip for the line
            subtitle = TextClip(line, fontsize=30, color='white', font=FONT_PATH, method='caption', size=(image_clip.size[0], None))
            subtitle = subtitle.set_duration(line_duration).set_position(('center', 'bottom'))
            
            # Create a semi-transparent black background for each line
            bg_size = subtitle.size
            bg_clip = ColorClip(size=(bg_size[0] + 20, bg_size[1] + 10), color=(0, 0, 0, 128)).set_duration(line_duration)
            
            # Combine the background and text
            subtitle_with_bg = CompositeVideoClip([bg_clip.set_position(('center', 'bottom')), subtitle.set_position(('center', 'bottom'))])
            line_clips.append(subtitle_with_bg)
        
        # Concatenate line clips and set the position at the bottom of the image
        final_subtitle_clip = concatenate_videoclips(line_clips).set_position(('center', 'bottom'))

        # Overlay the final subtitle clip on the image
        video_clip = CompositeVideoClip([image_clip, final_subtitle_clip])
        clips.append(video_clip)

    if not clips:
        print("No valid clips to concatenate. Exiting.")
        return

    # Concatenate all the video clips
    final_video = concatenate_videoclips(clips, method="compose")
    # Concatenate all the audio clips
    final_audio = concatenate_audioclips(audio_clips)

    # Set audio to the video
    final_video = final_video.set_audio(final_audio)
    # Write the result to a file with fps specified and ensure audio codec is AAC
    final_video.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=fps)
    print(f"Video written to {output_file}")  # Debug info

    # Clean up audio files
    for audio_file in audio_files:
        os.remove(audio_file)


if __name__ == "__main__":
    image_urls = ["https://example.com/image1.png", "https://example.com/image2.png"]  # Example image URLs
    narrations = ["Narration for image 1. This is the first narration.", "Narration for image 2. This is the second narration."]  # Example narrations
    narration_speed = 1.1  # Adjust the speed here
    create_movie(image_urls, narrations, narration_speed)
