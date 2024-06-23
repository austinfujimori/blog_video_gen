from scrape_info import get_blog_info
import os
import subprocess
import json
from create_movie import create_movie

import replicate
def get_text(user_input, max_tokens=512):
    env = os.environ.copy()
    env["USER_INPUT"] = user_input
    env["MAX_TOKENS"] = str(max_tokens)
    result = subprocess.run(["modal", "run", "get_text.py"], capture_output=True, text=True, env=env)
    # Filter the JSON part from the output
    output_lines = result.stdout.splitlines()
    json_output = None
    for line in output_lines:
        try:
            json_output = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    if json_output is None:
        raise ValueError("No valid JSON output found.")
    return json_output

def extract_scenes(full_text):
    scenes = []
    slides = full_text.split('\nSlide ')
    for slide in slides[1:]:  # Skip the first part before the first slide
        slide_number_and_title = slide.split('\n', 1)
        if len(slide_number_and_title) == 2:
            slide_number, slide_content = slide_number_and_title
            scenes.append(f"Slide {slide_number.strip()}\n{slide_content.strip()}")
    return scenes

def strip_titles(scenes):
    stripped_scenes = []
    for scene in scenes:
        title_split = scene.split('\n', 1)
        if len(title_split) == 2:
            _, content = title_split
            stripped_scenes.append(content.strip())
    return stripped_scenes

def generate_images(scenes):
    image_urls = []
    for i, scene in enumerate(scenes):
        prompt = scene
        result = subprocess.run(
            ["python3", "generate_image.py", prompt],
            capture_output=True,
            text=True
        )
        image_url = result.stdout.strip()
        if image_url:
            image_urls.append(image_url)
    return image_urls

def main():
    url = "https://www.rxbar.com/en_US/real-talk/articles/8-easy-habits-for-a-better-new-year.html"
    style = "photo-realistic"
    
    
    blog_info = get_blog_info(url)

    full_text = f"Title: {blog_info['title']}\nDate: {blog_info['date']}\nAuthor: {blog_info['author']}\nContent: {blog_info['content']}"
    print("Full Blog Text:\n", full_text)

    # Get script
    prompt = "Can you generate a script for a narrator for a short, interesting, persuasive slideshow video that summarizes the details of the blog provided below. Break the slides down into slides titled Slide X. Do not bold the title, just give the list of slides exactly in this format with nothing else (the following is an example) Slide 1: [slide], Slide 2: [slide]. Do not include Narrator:, just give the raw script. Generate at least 3 slides. Make the script a summary of the following blog: " + full_text
    response = get_text(prompt, 200)
    response_scenes = extract_scenes(response[0])

        
    print("\n\n\n\n\n")
    print("Generating video for first scene: " + response_scenes[0])
    
    
    
    # test for first slide
    
    

    # Get image descriptions
    image_prompt = "generate 5 detailed descriptions for 5 images that could represent the scene in a larger video. Provide the output in the format: Give the list of slides in the format: Slide 1: [image description], Slide 2: [image description]."

    image_prompt_response = get_text(image_prompt, 500)
    
    image_descriptions = extract_scenes(image_prompt_response[0])
    

    
    
    print("\n\n\n\n\n")
    for slide in image_descriptions:
        print(slide + "\n\n")
        slide += "Generate in a" + style + "style."

    # Generate image for each description
    image_urls = generate_images(image_descriptions)
    with open("image_urls.json", "w") as file:
        json.dump(image_urls, file)
        
     
    # make it in the form: {"image_1" : image_url}
    
    input = {}
    
    for i,image in enumerate(image_urls):
        input.update({"image_" + str(i): image})
    
    
    print("\n\n\n\n\n")
    print(input)

    output = replicate.run(
        "fofr/tooncrafter:51bf654d60d307ab45c4ffe09546a3c9606f8f33861ab28f5bb0e43ad3fa40ed", input=input)
    print(output)


if __name__ == "__main__":
    main()