import os
print("HUGGINGFACE_HUB_TOKEN:", os.environ.get("HUGGINGFACE_HUB_TOKEN"))
os.environ["HF_HOME"] = "/opt/dlami/nvme/hf_cache"
os.environ["TRANSFORMERS_CACHE"] = "/opt/dlami/nvme/hf_cache"
os.environ["HUGGINGFACE_HUB_TOKEN"] = os.environ.get("HUGGINGFACE_HUB_TOKEN") or "HF_TOKEN_REMOVED"

from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel, PeftConfig
import torch

# Caminhos locais
cache_dir = "/opt/dlami/nvme/hf_cache"
SNAPSHOT_PATH = "/home/ubuntu/.cache/huggingface/hub/models--mistralai--Mistral-7B-Instruct-v0.2/snapshots/63a8b081895390a26e140280378bc85ec8bce07a"
adapter_path = "mistral-finetune-advocacia-45k/checkpoint-3750"
offload_folder = "/opt/dlami/nvme/offload"

print("Carregando peft_config...")
peft_config = PeftConfig.from_pretrained(adapter_path)
print("Base model:", SNAPSHOT_PATH)

# Quantização 4-bit (bnb/nf4) para reduzir uso de memória
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True
)

print("Carregando modelo base (4-bit)…")
model = AutoModelForCausalLM.from_pretrained(
    SNAPSHOT_PATH,
    device_map="auto",
    quantization_config=bnb_config,
    torch_dtype=torch.float16,
    offload_folder=offload_folder,
    cache_dir=cache_dir
)
print("Modelo base carregado.")

print("Carregando tokenizer…")
tokenizer = AutoTokenizer.from_pretrained(SNAPSHOT_PATH)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
print("Tokenizer carregado.")

print("Carregando adapter LoRA/PEFT…")
model = PeftModel.from_pretrained(
    model,
    adapter_path,
    offload_folder=offload_folder
)
print("Adapter carregado.")

# Diagnóstico
print("Model class:", type(model))
print("Model config:", model.config)
if hasattr(model, "peft_config"):
    print("PEFT LOADED:", model.peft_config)
else:
    print("PEFT NÃO CARREGADO!")

app = Flask(__name__)

@app.route("/infer", methods=["POST"])
def infer():
    try:
        print("=== CHEGOU NO ENDPOINT /infer ===")
        data = request.get_json(force=True) or {}
        prompt = data.get("prompt", "")
        max_new_tokens = int(data.get("max_new_tokens", 128))
        client_ip = request.remote_addr
        print(f"[LLM DEBUG] Requisição de {client_ip}")
        print(f"[LLM DEBUG] Prompt: {repr(prompt)[:500]}")
        print(f"[LLM DEBUG] max_new_tokens: {max_new_tokens}")

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                early_stopping=True
            )

        texto = tokenizer.decode(outputs[0], skip_special_tokens=True)

        if texto.startswith(prompt):
            texto = texto[len(prompt):].lstrip()

        if "[FIM]" in texto:
            texto = texto.split("[FIM]")[0].strip()

        print(f"[LLM DEBUG] Resposta gerada: {repr(texto)[:500]}")
        return jsonify({"response": texto})
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, use_reloader=False)
