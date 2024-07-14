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




def download_video(remote_video_name, index):
    volume_name = "model-cache-volume"
    local_video_path = os.path.join('videos')
    local_video_path_name = os.path.join('videos', f"12_gen_video_{index}_0000.mp4")

    if not os.path.exists('videos'):
        os.makedirs('videos')

    command = f"modal volume get {volume_name} {remote_video_name} {local_video_path}"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("Video downloaded from volume successfully.")
        print(f"Standard Output:\n{result.stdout}")
        print(f"Standard Error:\n{result.stderr}")
        return local_video_path_name
    except subprocess.CalledProcessError as e:
        print(f"Video download failed with exit code {e.returncode}")
        print(f"Standard Output:\n{e.stdout}")
        print(f"Standard Error:\n{e.stderr}")
        return None




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
    for idx in range(len(image_paths)):
        upload_image_to_volume(image_paths[idx], file_mount_names[idx], "model-cache-volume")

    command = (
        f"modal run generate_video.py::main "
        f"--image-paths '{json.dumps(image_paths)}' "
        f"--prompts '{json.dumps(prompts)}' "
        f"--file-mount-names '{json.dumps(file_mount_names)}' "
        f"--sample-names '{json.dumps(sample_names)}' "
        f"--durations '{json.dumps(durations)}' "
        f"--resolutions '{json.dumps(resolutions)}' "
        f"--aspect-ratios '{json.dumps(aspect_ratios)}'"
    )

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("Modal run command executed successfully.")
        print(f"Standard Output:\n{result.stdout}")
        print(f"Standard Error:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Modal run command failed with exit code {e.returncode}")
        print(f"Standard Output:\n{e.stdout}")
        print(f"Standard Error:\n{e.stderr}")
        
        
        
        
        

def download_image(image_url, index):
    response = requests.get(image_url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        if not os.path.exists('images'):
            os.makedirs('images')
        image_path = os.path.join('images', f"image{index}.png")
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

def generate_music(prompt, duration):
    output = replicate.run(
        "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
        input={
            "top_k": 250,
            "top_p": 0,
            "prompt": prompt,
            "duration": int(duration),
            "temperature": 1,
            "continuation": False,
            "model_version": "stereo-melody-large",
            "output_format": "mp3",
            "continuation_start": 0,
            "multi_band_diffusion": False,
            "normalization_strategy": "peak",
            "classifier_free_guidance": 3
        }
    )

    music_url = output
    if music_url:
        music_response = requests.get(music_url)
        music_file_path = f"{uuid.uuid4()}.mp3"
        with open(music_file_path, "wb") as music_file:
            music_file.write(music_response.content)
        return music_file_path
    else:
        raise Exception("Failed to get music URL from response.")

def create_movie(image_urls, image_descriptions, narrations, music_prompt, narration_speed=1.0, output_file="output_video.mp4", fps=24, resolution="480p", aspect_ratio="9:16"):
    audio_clips = []
    audio_files = []
    sum_of_clips_duration = 0
    images_paths = []

    # Generate narration audio and calculate the sum of clip durations
    for i, image_url in enumerate(image_urls):
        # Download the image and save the path
        image_path = download_image(image_url, i+1)
        images_paths.append(image_path)
        print(f"Downloaded image {i + 1}: {image_path}")  # Debug info

        # Generate narration audio
        narration = narrations[i]
        if not narration.strip():
            print(f"Skipping empty narration for slide {i + 1}")
            continue

        audio_file = generate_narration(narration, narration_speed)
        audio_clip = AudioFileClip(audio_file)
        audio_duration = audio_clip.duration
        sum_of_clips_duration += audio_duration
        audio_clips.append(audio_clip.set_duration(audio_duration))
        audio_files.append(audio_file)
        print(f"Generated narration {i + 1}: {audio_file} with duration {audio_duration}")

    if not audio_clips:
        print("No valid clips to concatenate. Exiting.")
        return
    
     
    # get the duration for the audio that goes over the full script (concatenated witha ll strings), then sum up the audio for all of the little clips that we tested to get sum_of_clips_duration. Then duration_scale = actual_duration/sum_of_clips_duration and then for all the clips multiply their duration by duration_scale

    # Generate full narration audio for the entire script
    full_narration_text = " ".join(narrations)
    full_narration_file = generate_narration(full_narration_text, narration_speed)
    final_audio_clip = AudioFileClip(full_narration_file)
    audio_files.append(full_narration_file)

    # Calculate the actual duration of the full narration audio
    actual_duration = final_audio_clip.duration

    # Calculate the duration scale factor
    duration_scale = actual_duration / sum_of_clips_duration

    # Create video clips with scaled durations
    scaled_clips = []
    
    # Scaled durations for the audio clips (due to audio for full script taking longer/shorter than audio for combined clips)
    # These durations also represent the length for each "scene"
    scaled_durations = []
    prompts = []
    file_mount_names = []
    sample_names = []
    resolutions = []
    aspect_ratios = []
    for i, image_path in enumerate(images_paths):
        audio_clip = audio_clips[i]
        scaled_durations.append(audio_clip.duration * duration_scale)
        
        # args for create videos
        file_mount_names.append(f"12_image{i}.png")
        sample_names.append(f"12_gen_video_{i}")
        resolutions.append(resolution)
        aspect_ratios.append(aspect_ratio)
        prompts.append(image_descriptions[i])
        # prompts.append(image_descriptions[i])
        
    # since open-sora only accepts durations of 2, 4, 8, 16s, we have to make it longer then cut it short
    durations = []
    for duration in scaled_durations:
        if duration < 2:
            durations.append("2s")
        elif duration < 4:
            durations.append("4s")
        elif duration < 8:
            durations.append("8s")
        else:
            durations.append("16s")
    
    for prompt in prompts:
        print(f"\n\n\n{prompt}")
    
    # rn generate_video has some issues with accepting the arrays of prompts as input (specifically jsut using first image for all of them)
    # so let's run it individually in the meantime
    for i in range(len(images_paths)):
        run_modal_main([images_paths[i]], [prompts[i]], [file_mount_names[i]], [sample_names[i]], [durations[i]], [resolutions[i]], [aspect_ratios[i]])
    
    print("\n\n\n\n\n\n\nfinished inference for vids\n\n\n\n\n\n\n")
    
    
    # Download videos and store paths
    video_paths = []
    for i in range(len(images_paths)):
        video_path = download_video(f"12_gen_video_{i}_0000.mp4", i)
        if video_path:
            video_paths.append(video_path)

        
    for i, video_path in enumerate(video_paths):
        scaled_duration = scaled_durations[i]

        # Create a VideoClip with the scaled duration
        video_clip = VideoFileClip(video_path).subclip(0, scaled_duration)

        # Split the narration into lines for subtitles
        narration = narrations[i]
        lines = split_text_into_lines(narration, MAX_WORDS_PER_LINE)
        if not lines:
            print(f"No lines generated for slide {i + 1}")
            continue

        # Create clips for each line of subtitles
        line_clips = []
        for j, line in enumerate(lines):
            # Create a TextClip for the line
            subtitle = TextClip(line, fontsize=30, color='white', font=FONT_PATH, method='caption', size=(video_clip.size[0], None))

            if j < len(lines) - 1:
                # Set the duration for non-last subtitles
                subtitle_duration = scaled_duration / len(lines)
            else:
                # Set the duration for the last subtitle to extend to the end of the scene
                subtitle_duration = scaled_duration - (len(lines) - 1) * (scaled_duration / len(lines))

            subtitle = subtitle.set_duration(subtitle_duration).set_start(j * (scaled_duration / len(lines))).set_position(('center', 'bottom'))

            # Create a semi-transparent black background for each line
            bg_size = subtitle.size
            bg_clip = ColorClip(size=(bg_size[0] + 20, bg_size[1] + 10), color=(0, 0, 0, 128)).set_duration(subtitle_duration).set_start(j * (scaled_duration / len(lines)))

            # Combine the background and text
            subtitle_with_bg = CompositeVideoClip([bg_clip.set_position(('center', 'bottom')), subtitle.set_position(('center', 'bottom'))])
            line_clips.append(subtitle_with_bg)

        # Overlay the final subtitle clip on the video
        video_clip = CompositeVideoClip([video_clip] + line_clips)
        scaled_clips.append(video_clip)
    
    
    
    

    # Concatenate the scaled clips into the final video
    final_video = concatenate_videoclips(scaled_clips, method="compose")

    # Set the continuous audio to the video
    final_video = final_video.set_audio(final_audio_clip)

    # Generate music based on the prompt and video duration
    music_file_path = generate_music(music_prompt, int(actual_duration))  # Ensure duration is an integer
    music_clip = AudioFileClip(music_file_path)

    # Adjust the music duration to match the video duration
    music_clip = music_clip.subclip(0, min(music_clip.duration, actual_duration))

    # Combine the final audio clip and the music clip
    combined_audio = CompositeAudioClip([final_video.audio, music_clip])
    final_video = final_video.set_audio(combined_audio)

    # Write the result to a file with fps specified and ensure audio codec is AAC
    final_video.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=fps)
    print(f"Video written to {output_file}")

    # Clean up audio files
    for audio_file in audio_files:
        os.remove(audio_file)
    os.remove(music_file_path)

if __name__ == "__main__":
    image_urls = ["https://example.com/image1.png", "https://example.com/image2.png"]
    image_descriptions = ["image prompt 1", "image prompt 2"]
    narrations = ["Narration for image 1. This is the first narration.", "Narration for image 2. This is the second narration."]
    narration_speed = 1
    music_prompt = "Example music prompt for testing"
    output_file="movie.mp4"
    fps=24
    resolution="480p"
    aspect_ratio="9:16"
    
    create_movie(image_urls, image_descriptions, narrations, music_prompt, narration_speed,output_file,fps,resolution,aspect_ratio)