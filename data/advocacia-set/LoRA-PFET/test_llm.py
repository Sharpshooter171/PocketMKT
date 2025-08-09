import os
print("TOKEN (parcial):", os.environ.get("HUGGINGFACE_HUB_TOKEN"))

from huggingface_hub import hf_hub_download
file_path = hf_hub_download(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2", 
    filename="config.json"
)
print("Arquivo baixado:", file_path)
