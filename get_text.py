import os
import time
import modal
import json

MODEL_DIR = "/model"
MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"

def download_model_to_image(model_dir, model_name):
    from huggingface_hub import snapshot_download
    from transformers.utils import move_cache

    os.makedirs(model_dir, exist_ok=True)

    hf_token = os.environ.get("HF_TOKEN")
    snapshot_download(
        model_name,
        local_dir=model_dir,
        token=hf_token,
        ignore_patterns=["*.pt", "*.gguf"],
    )
    move_cache()

image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "vllm==0.4.0.post1",
        "torch==2.1.2",
        "transformers==4.39.3",
        "ray==2.10.0",
        "huggingface_hub==0.19.4",
        "hf-transfer==0.1.4"
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_function(
        download_model_to_image,
        secrets=[modal.Secret.from_name("huggingface-secret")],
        timeout=60 * 20,
        kwargs={"model_dir": MODEL_DIR, "model_name": MODEL_NAME},
    )
)

app = modal.App(f"example-vllm-{MODEL_NAME}", image=image)

with image.imports():
    import vllm

GPU_CONFIG = modal.gpu.H100(count=1)

@app.cls(gpu=GPU_CONFIG, secrets=[modal.Secret.from_name("huggingface-secret")])
class Model:
    @modal.enter()
    def load(self):
        self.template = (
            "<start_of_turn>user\n{user}<end_of_turn>\n<start_of_turn>model\n"
        )
        self.llm = vllm.LLM(
            MODEL_DIR,
            enforce_eager=True,
            tensor_parallel_size=GPU_CONFIG.count,
        )

    @modal.method()
    def generate(self, user_questions):
        prompts = [self.template.format(user=q) for q in user_questions]

        sampling_params = vllm.SamplingParams(
            temperature=0.75,
            top_p=0.99,
            # can increase or decrease max_tokens if you want more or less scenes, although I realized that the model sometimes will start generating jibberish past 512, especially if we exclude the stop parameter
            max_tokens=512,
            presence_penalty=1.15,
            stop=["<end_of_turn>", "<start_of_turn>user"]
        )
        result = self.llm.generate(prompts, sampling_params)
        return [output.outputs[0].text.strip() for output in result]

@app.local_entrypoint()
def main():
    user_input = os.environ.get("USER_INPUT")
    if not user_input:
        raise ValueError("No input provided.")
    questions = [user_input]
    model = Model()
    results = model.generate.remote(questions)
    print(json.dumps(results))
