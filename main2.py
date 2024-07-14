import subprocess
import os
import json




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
        
        

if __name__ == "__main__":
    image_paths = [["/Users/austinfujimori/Desktop/blog_video_gen/image_test1.png"], ["/Users/austinfujimori/Desktop/blog_video_gen/image_test2.png"]]
    prompts = [["ocean monster"], ["ocean monster"]]
    file_mount_names = [["3_sim_test_1.png"], ["3_sim_test_2.png"]]
    sample_names = [["3_vid1"], ["3_vid2"]]
    durations = [["4s"], ["4s"]]
    resolutions = [["480p"], ["480p"]]
    aspect_ratios = [["9:16"], ["9:16"]]
    
    for i in range(len(image_paths)):
        run_modal_main(image_paths[i], prompts[i], file_mount_names[i], sample_names[i], durations[i], resolutions[i], aspect_ratios[i])





