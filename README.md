Image Gen: OpenAI Dall-E 2, 512x512

Text Gen: LLama 3 (vllm) on Modal

Narrator: ElevenLabs API

Music Gen: https://replicate.com/meta/musicgen?prediction=7kmewmjq1hrge0cgaymbdp56eg

Video Gen: Open-Sora hcpaitech



# Use


#### 1. Clone Repo



#### 2. Virtual Env

Create a virtual env and activate it

```python -m venv modal-venv```

```source modal-venv/bin/activate```

Install the requirements (make sure you have a modal account)

```pip install -r requirements.txt```


#### 3. Create .env file in the root directory

And put:

REPLICATE_API_TOKEN=____

OPENAI_API_KEY=____

ELEVENLABS_API_KEY=____


#### 4. Your prompts

In **main.py**, go to line 149 and put in your desired URL as input.


For more options, you can change the resolution and aspect ratio of the movie by changing line 236 in **main.py** to create_movie(image_urls, image_descriptions, narration_script, music_response, narration_speed, "your aspect ratio", "your resolution").

The default aspect ratio is "9:16" and the default resolution is "480p". You can go up to "720p."


#### 5. Run

```python3 main.py```



# Output

The individually generated scenes will be under the videos folder (downloaded from Modal), the images, audio, music, etc. in the other folders.

The final movie will be downloaded to the root directory and is called output_movie.mp4.



# More info

Video generation right now uses the open source library Open-Sora by hcpaitech. It is computationally expensive, running them in parallel on 10 GPUs for 10+ scenes on A100s 80GB can take up to 10 minutes and cost at least $15 depending on the length of the videos (usually 4s -> $15-30).


# Continued

A slightly different implementation (due to structure) is implemented in the blog_gen_app repo. Idea and pipeline is basically the same, some updates there that were not implemented here.
