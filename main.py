from scrape_info import get_blog_info
import os
import subprocess
import json
from create_movie import create_movie

def get_text(user_input):
     env = os.environ.copy()
     env["USER_INPUT"] = user_input
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
    sections = full_text.split('\nSection ')
    for section in sections[1:]:  # Skip the first part before the first section
        section_number_and_title = section.split('\n', 1)
        if len(section_number_and_title) == 2:
            section_number, section_content = section_number_and_title
            scenes.append(f"Section {section_number.strip()}\n{section_content.strip()}")
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
     blog_info = get_blog_info(url)


     full_text = f"Title: {blog_info['title']}\nDate: {blog_info['date']}\nAuthor: {blog_info['author']}\nContent: {blog_info['content']}"
     print("Full Blog Text:\n", full_text)

     # Get script
     prompt = "Can you generate a script for a narrator for a short, interesting, persausive video that summarizes the details of the blog provided below. Break it down into sections titled Section X. Do not bold the title, just give the list of sections exactly in this format with nothing else (the following is an example) Section 1: [section], Section 2: [section]. Do not include Narrator:, just give the raw script. Generate at least 10 Sections. Make the script a summary of the following blog: "+ full_text
     response = get_text(prompt)
     response_scenes = extract_scenes(response[0])
     

     print("\n\n\n\n\n")
     image_prompt = "For each of these sections " 
     for section in response_scenes:
          print(section + "\n\n")
          image_prompt += section
          
          
     # Get image descriptions
     image_prompt += "come up with a detailed description of an image for each section that accomodates what the description is talking about. Provide the output in the format: Give the list of sections in the format: Section 1: [image description], Section 2: [image description]."
     image_prompt_response = get_text(image_prompt)
     print(image_prompt_response)
     image_descriptions = extract_scenes(image_prompt_response[0])
     
     print("\n\n\n\n\n")
     for section in image_descriptions:
          print(section + "\n\n")
     
     
     # Generate image for each description
     image_urls = generate_images(image_descriptions)
     with open("image_urls.json", "w") as file:
          json.dump(image_urls, file)
          
     
     # strip responses of the title part for narration
     narration_script = strip_titles(response_scenes)
     
     
     # Create movie
     if image_urls:
          create_movie(image_urls, narration_script)


if __name__ == "__main__":
    main()
