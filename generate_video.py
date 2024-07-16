
import modal
import os
import json

app = modal.App(name="open-sora-app")

# VUDA BASE IMAGE
cuda_version = "12.1.0"
image = (
    modal.Image.from_registry(f"nvidia/cuda:{cuda_version}-devel-ubuntu20.04", add_python="3.9")
    .apt_install("libgl1", "libglib2.0-0", "libsm6", "git", "clang-11", "clang++-11", "libcudnn8", "libcudnn8-dev")
    .run_commands(
        "update-alternatives --install /usr/bin/clang clang /usr/bin/clang-11 100",
        "update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-11 100",
        "pip install -U pip setuptools wheel",
        "pip uninstall -y torch torchvision torchaudio numpy",  # Uninstall existing PyTorch and NumPy
        "git clone https://github.com/hpcaitech/Open-Sora.git /root/Open-Sora",  # Clone the repository first
        "cd /root/Open-Sora && pip install -r requirements/requirements-cu121.txt",
        "cd /root/Open-Sora && pip install -v .",
        "pip install packaging ninja",
        "pip install flash-attn --no-build-isolation",
        "pip install -v --disable-pip-version-check --no-cache-dir --no-build-isolation --config-settings '--build-option=--cpp_ext' --config-settings '--build-option=--cuda_ext' git+https://github.com/NVIDIA/apex.git",
    )
)

# Create or retrieve the volume
volume = modal.Volume.from_name("model-cache-volume", create_if_missing=True)

@app.function(image=image, volumes={"/mnt/volume": volume}, gpu=modal.gpu.A100(count=2, size="80GB"), timeout=1200)
def run_open_sora_inference(image_path, prompt, file_mount_name, sample_name, duration, resolution, aspect_ratio):
    import os
    import numpy as np
    from subprocess import CalledProcessError, run

    # Ensure the /mnt/volume directory exists
    os.makedirs("/mnt/volume", exist_ok=True)

    if not os.path.exists("/root/Open-Sora"):
        os.system("git clone https://github.com/hpcaitech/Open-Sora.git /root/Open-Sora")

    os.chdir("/root/Open-Sora")

    # Install dependencies
    if not os.path.isfile("setup.py"):
        # print("setup.py not found.")
        pass
    else:
        os.system("pip install -r requirements/requirements-cu121.txt")
        os.system("pip install -v .")
        # print("Open-Sora setup complete.")

    # print(f"NumPy version: {np.__version__}")

    # List files in the volume
    # print("Listing files in /mnt/volume:")
    volume_contents = os.listdir("/mnt/volume")
    # print(volume_contents)

    # Construct the inference command
    image_path = f"/mnt/volume/{file_mount_name}"
    if not os.path.isfile(image_path):
        print(f"The file {image_path} does not exist.")
        return "The file does not exist."

    output_path = f"/mnt/volume/{sample_name}_0000.mp4"
    samples_dir = "./samples/samples/"



    command = (
        f"python scripts/inference.py configs/opensora-v1-2/inference/sample.py "
        f"--sample-name {sample_name} "
        f"--layernorm-kernel False --flash-attn False "
        f"--num-frames {duration} --resolution {resolution} --aspect-ratio {aspect_ratio} "
        f'--prompt "{prompt}{{\\"reference_path\\": \\"{image_path}\\",\\"mask_strategy\\": \\"0\\"}}" '
        f'--outputs "{output_path}"'
    )
    
        
    print(f"\n\n\n\nimage_path={image_path}, video = {sample_name}")

    try:
        result = run(command, shell=True, check=True, capture_output=True, text=True)
        print("Inference command executed successfully.")
        print(f"Standard Output:\n{result.stdout}")
        print(f"Standard Error:\n{result.stderr}")
    except CalledProcessError as e:
        print(f"Inference command failed with exit code {e.returncode}")
        print(f"Standard Output:\n{e.stdout}")
        print(f"Standard Error:\n{e.stderr}")
        return "Inference command failed"

    # Check and log the contents of the samples directory
    if os.path.exists(samples_dir):
        print(f"Contents of {samples_dir}: {os.listdir(samples_dir)}")

    # # Check if the video was generated in the expected location
    # if os.path.exists(output_path):
    #     print(f"Video successfully generated at: {output_path}")
    #     # Verify that the video was copied to the Volume
    #     os.system("ls -l /mnt/volume")
    #     return output_path
    # else:
    # If the video is not found in the expected location, check the samples directory
    video_files = [f for f in os.listdir(samples_dir) if f.endswith('.mp4')]
    if video_files:
        video_path = os.path.join(samples_dir, f"{sample_name}_0000.mp4")
        print(f"Video found at: {video_path}")
        print(f"Putting video to Volume: {video_path} -> /mnt/volume/{sample_name}_0000.mp4")

        # Copy the video to the Volume
        command = f"cp {video_path} /mnt/volume/{sample_name}_0000.mp4"
        os.system(command)
        print(f"File successfully copied to Volume at: /mnt/volume/{sample_name}_0000.mp4")

        # Verify that the video was copied to the Volume
        os.system("ls -l /mnt/volume")
        return video_path
    else:
        print(f"Video not found at: {output_path} or in {samples_dir}")
        return "Inference completed but video not found"

@app.local_entrypoint()
def main(image_paths, prompts, file_mount_names, sample_names, durations, resolutions, aspect_ratios):
    # Parse the arguments from JSON strings
    image_paths = json.loads(image_paths)
    prompts = json.loads(prompts)
    file_mount_names = json.loads(file_mount_names)
    sample_names = json.loads(sample_names)
    durations = json.loads(durations)
    resolutions = json.loads(resolutions)
    aspect_ratios = json.loads(aspect_ratios)

    # Debug: Print the inputs
    print("Image Paths:", image_paths)
    print("Prompts:", prompts)
    print("File Mount Names:", file_mount_names)
    print("Sample Names:", sample_names)
    print("Durations:", durations)
    print("Resolutions:", resolutions)
    print("Aspect Ratios:", aspect_ratios)
    
    inputs = [
        (
            image_paths[idx], 
            prompts[idx], 
            file_mount_names[idx], 
            sample_names[idx], 
            durations[idx], 
            resolutions[idx], 
            aspect_ratios[idx]
        )
        for idx in range(len(image_paths))
    ]

    # Debug: Print the prepared inputs
    print("Prepared Inputs for starmap:", inputs)

    # Run tasks in parallel using Function.starmap
    results = list(run_open_sora_inference.starmap(inputs))
    print(f"Function call returned: {results}")

if __name__ == "__main__":
    main(
        json.dumps(["/Users/austinfujimori/Desktop/open-sora-test/image_2.png", "/Users/austinfujimori/Desktop/open-sora-test/image_3.png"]),
        json.dumps(["waterfall running down", "mountain sunrise"]),
        json.dumps(["file_mount_name_1.png", "file_mount_name_2.png"]),
        json.dumps(["sample_name_1", "sample_name_2"]),
        json.dumps(["1s", "2s"]),
        json.dumps(["128p", "256p"]),
        json.dumps(["16:9", "4:3"])
    )

