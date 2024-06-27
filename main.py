from scrape_info import get_blog_info
import os
import subprocess
import json
from create_movie import create_movie
import re


# Get resposne from LLM on Modal
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



# Each scene is a sentence, sometiems LLM gets cut off and doesn't include END so just in case we end it at the last sentence. (period, exclamation point, question mark, etc.)
# If sentence is longer than 10 words, cut it in half, cuz generated videos can't be that long unless they are looped
def extract_scenes(full_text):
    script_start = full_text.find("BEGIN_SCRIPT") + len("BEGIN_SCRIPT")
    script_end = full_text.find("END_SCRIPT")
    if script_end == -1:
        script_end = len(full_text)
    script_text = full_text[script_start:script_end].strip()
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s', script_text)
    
    def split_long_sentence(sentence, max_words=10):
        words = sentence.split()
        if len(words) > max_words:
            mid = len(words) // 2
            split_index = min(mid, max_words)
            return [' '.join(words[:split_index]), ' '.join(words[split_index:])]
        else:
            return [sentence]
        
    # Strip whitespace, not empty
    scenes = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            scenes.extend(split_long_sentence(sentence))
    if scenes and not re.match(r'.*[\.\?\!]$', scenes[-1]):
        scenes.pop()
    return scenes




# Creates list for image descriptions
def extract_image_scenes(full_text):
    image_pattern = re.compile(r'IMAGE_\d+: (.*?)(?=\nIMAGE_\d+:|\Z)', re.DOTALL)
    matches = image_pattern.findall(full_text)
    return [match.strip() for match in matches]



# Gen images
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



# For the music prompt
def get_music_prompt(full_text):
    script_start = full_text.find("BEGIN_PROMPT") + len("BEGIN_PROMPT")
    script_end = full_text.find("END_PROMPT")
    if script_end == -1:
        script_end = len(full_text)
    script_text = full_text[script_start:script_end].strip()
    return script_text






def main():
    
    ########## USER INPUTS ##########
    
    url = "https://www.rxbar.com/en_US/real-talk/articles/8-easy-habits-for-a-better-new-year.html"
    style = "cartoony"
    
    narration_speed = 1
    
    ########## USER INPUTS ##########
    
    
    
    

    blog_info = get_blog_info(url)

    full_text = f"Title: {blog_info['title']}\nDate: {blog_info['date']}\nAuthor: {blog_info['author']}\nContent: {blog_info['content']}"
    # print("Full Blog Text:\n", full_text)
    print('\n\n\n\n\n')

    # Get script
    prompt = "Can you generate a concise, compelling, and immersive narration for a video that summarizes the blog provided below:" + full_text + "Do not include anything other than the narrator's dialogue. Start it with: BEGIN_SCRIPT and end it with END_SCRIPT, for example: BEGIN_SCRIPT The sun dipped below the horizon, casting a golden hue over the sprawling meadow. The air was crisp and carried the faint scent of blooming wildflowers. In the midst of this serene landscape, a lone figure ambled along a narrow, winding path, his silhouette elongated by the setting sun. This was Ethan, a man of quiet contemplation, seeking solace in the embrace of nature. His footsteps were slow and deliberate, crunching softly against the gravel underfoot. Each step seemed to resonate with a sense of purpose, a rhythm in harmony with the whispering breeze. END_SCRIPT."
    response = get_text(prompt, 200) #384
    # print("Raw Response:\n", response)
    
    # make a list for each scene (sentence)
    response_scenes = extract_scenes(response[0])
    for i, scene in enumerate(response_scenes):
        print("\nScene " + str(i) + ": " + scene + "\n\n")
    
    
    # Get image descriptions
    # we embed the blog title: {blog_info['title']}, because sometimes a sentence will say something unrelated or a filler like if we're talking about movies, it could say Do you like popcorn? or something. We could embed the whole blog but it's quicker to do just the title, and we could also jsut embed the whole script, but we don't know how much attention the specific sentence for that scene will be getting.
    image_prompt = "For each scene in this script: "
    for i, scene in enumerate(response_scenes):
        image_prompt += "Scene " + str(i) + ": " + scene + "\n\n"
    image_prompt += "come up with a very short description of a " + style + " styled image for each scene that aligns with what the script is talking about and also the overall theme, which is: " + blog_info['title'] + "Begin each description with IMAGE_X:, for example: IMAGE_1: description IMAGE_2: description IMAGE_3: description. Do it for all " + " 0 to" + str(len(response_scenes) - 1) + " scenes given."
    image_prompt_response = get_text(image_prompt, 1500)
    print("\nImage Prompt Response:\n", image_prompt_response)  
    
    image_descriptions = extract_image_scenes(image_prompt_response[0])
    for description in image_descriptions:
        description += "generate in a " + style + "style"
    for i, description in enumerate(image_descriptions):
        print("\Scene " + str(i) + ": " + description + "\n\n")



    # Generate images for each image description
    image_urls = generate_images(image_descriptions)
    # print("Image URLs:\n", image_urls)  
    with open("image_urls.json", "w") as file:
        json.dump(image_urls, file)
    print("\n\n\n\n Image URLS: " + str(len(image_urls)))
        
        
    # Generate short videos
    
    
    
    # Get music prompt
    music_prompt = "Generate a prompt for a music generator for music that would go along with a story like this: "
    for scene in response_scenes:
        music_prompt += scene
    music_response = get_text(music_prompt, 50)[0]
    print(music_response)
        



    # Create movie
    narration_script = response_scenes  
    
    if image_urls:
        create_movie(image_urls, narration_script, music_response, narration_speed)




if __name__ == "__main__":
    main()
