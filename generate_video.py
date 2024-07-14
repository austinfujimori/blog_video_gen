


import modal
import os
import subprocess
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

# Combined function to setup and run inference with Open-Sora
@app.function(image=image, volumes={"/mnt/volume": volume}, gpu=modal.gpu.A100(count=2, size="80GB"), timeout=1200)
def setup_and_run_open_sora_inference(image_paths: list, prompts: list, file_mount_names: list, sample_names: list, durations: list, resolutions: list, aspect_ratios: list) -> list:
    results = []

    for idx in range(len(image_paths)):
        image_path = image_paths[idx]
        prompt = prompts[idx]
        file_mount_name = file_mount_names[idx]
        sample_name = sample_names[idx]
        duration = durations[idx]
        resolution = resolutions[idx]
        aspect_ratio = aspect_ratios[idx]

        print(f"\n\n\n\n prompt: {prompt} \n")
        print(f"\n sample name: {sample_name} \n")
        print(f"\n duration: {duration} \n")
        print(f"\n resolution: {resolution} \n")
        print(f"\n aspect ratio: {aspect_ratio} \n")
        print(f"\n file_mount_name: {file_mount_name} \n\n\n\n")

        import os

        # Ensure the /mnt/volume directory exists
        os.makedirs("/mnt/volume", exist_ok=True)

        if not os.path.exists("/root/Open-Sora"):
            os.system("git clone https://github.com/hpcaitech/Open-Sora.git /root/Open-Sora")

        os.chdir("/root/Open-Sora")

        # Install dependencies
        if not os.path.isfile("setup.py"):
            print("setup.py not found.")
        else:
            os.system("pip install -r requirements/requirements-cu121.txt")
            os.system("pip install -v .")
            print("Open-Sora setup complete.")

        import numpy as np
        print(f"NumPy version: {np.__version__}")

        # List files in the volume
        print("Listing files in /mnt/volume:")
        volume_contents = os.listdir("/mnt/volume")
        print(volume_contents)

        # Construct the inference command
        image_path = f"/mnt/volume/{file_mount_name}"
        if not os.path.isfile(image_path):
            print(f"The file {image_path} does not exist.")
            results.append("The file does not exist.")
            continue

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

        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print("Inference command executed successfully.")
            print(f"Standard Output:\n{result.stdout}")
            print(f"Standard Error:\n{result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Inference command failed with exit code {e.returncode}")
            print(f"Standard Output:\n{e.stdout}")
            print(f"Standard Error:\n{e.stderr}")
            results.append("Inference command failed")
            continue

        # Check and log the contents of the samples directory
        if os.path.exists(samples_dir):
            print(f"Contents of {samples_dir}: {os.listdir(samples_dir)}")

        # Check if the video was generated in the expected location
        if os.path.exists(output_path):
            print(f"Video successfully generated at: {output_path}")
            # Verify that the video was copied to the Volume
            os.system("ls -l /mnt/volume")
            results.append(output_path)
        else:
            # If the video is not found in the expected location, check the samples directory
            video_files = [f for f in os.listdir(samples_dir) if f.endswith('.mp4')]
            if video_files:
                video_path = os.path.join(samples_dir, video_files[0])
                print(f"Video found at: {video_path}")
                print(f"Putting video to Volume: {video_path} -> /mnt/volume/{sample_name}_0000.mp4")

                # Copy the video to the Volume
                command = f"cp {video_path} /mnt/volume/{sample_name}_0000.mp4"
                os.system(command)
                print(f"File successfully copied to Volume at: /mnt/volume/{sample_name}_0000.mp4")

                # Verify that the video was copied to the Volume
                os.system("ls -l /mnt/volume")
                results.append(video_path)
            else:
                print(f"Video not found at: {output_path} or in {samples_dir}")
                results.append("Inference completed but video not found")

    return results

@app.local_entrypoint()
def main(
    image_paths: str,
    prompts: str,
    file_mount_names: str,
    sample_names: str,
    durations: str,
    resolutions: str,
    aspect_ratios: str
):
    # Parse the arguments from JSON strings
    image_paths = json.loads(image_paths)
    prompts = json.loads(prompts)
    file_mount_names = json.loads(file_mount_names)
    sample_names = json.loads(sample_names)
    durations = json.loads(durations)
    resolutions = json.loads(resolutions)
    aspect_ratios = json.loads(aspect_ratios)

    # Upload the images and run inference
    function_call = setup_and_run_open_sora_inference.spawn(image_paths, prompts, file_mount_names, sample_names, durations, resolutions, aspect_ratios)
    volume_video_paths = function_call.get()
    print(f"Function call returned: {volume_video_paths}")

if __name__ == "__main__":
    main(
        json.dumps(["/Users/austinfujimori/Desktop/open-sora-test/image_2.png"]),
        json.dumps(["waterfall running down"]),
        json.dumps(["file_mount_name.png"]),
        json.dumps(["sample_name"]),
        json.dumps(["1s"]),
        json.dumps(["128p"]),
        json.dumps(["16:9"])
    )

