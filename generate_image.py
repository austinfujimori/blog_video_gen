import sys
from openai import OpenAI

client = OpenAI()

if len(sys.argv) < 2:
    raise ValueError("No scene description provided.")

scene_description = sys.argv[1]

response = client.images.generate(
  model="dall-e-3",
  prompt=scene_description,
  size="1024x1024",
  quality="standard",
  n=1,
)

image_url = response.data[0].url
print(image_url)
