import os
print("HUGGINGFACE_HUB_TOKEN:", os.environ.get("HUGGINGFACE_HUB_TOKEN"))
os.environ["HF_HOME"] = "/opt/dlami/nvme/hf_cache"
os.environ["TRANSFORMERS_CACHE"] = "/opt/dlami/nvme/hf_cache"
os.environ["HUGGINGFACE_HUB_TOKEN"] = "HF_TOKEN_REMOVED"


from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, PeftConfig
import torch

#model_name = "mistralai/Mistral-7B-Instruct-v0.2"
cache_dir = "/opt/dlami/nvme/hf_cache"
SNAPSHOT_PATH = "/home/ubuntu/.cache/huggingface/hub/models--mistralai--Mistral-7B-Instruct-v0.2/snapshots/63a8b081895390a26e140280378bc85ec8bce07a"
adapter_path = "mistral-finetune-advocacia-45k/checkpoint-3750"
offload_folder = "/opt/dlami/nvme/offload"

print("Carregando peft_config...")
peft_config = PeftConfig.from_pretrained(adapter_path)
base_model = SNAPSHOT_PATH
print("Base model:", base_model)

print("Carregando modelo base...")
model = AutoModelForCausalLM.from_pretrained(
    SNAPSHOT_PATH,
    torch_dtype=torch.float16,
    device_map="auto",
    offload_folder=offload_folder,
    cache_dir=cache_dir
)
print("Modelo base carregado.")

print("Carregando tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(SNAPSHOT_PATH)
print("Tokenizer carregado.")

print("Carregando adapter LoRA/PEFT...")
model = PeftModel.from_pretrained(
    model,
    adapter_path,
    offload_folder=offload_folder
)
print("Adapter carregado.")
# ========== AQUI OS PRINTS DE DIAGNÓSTICO DO LOADER PEFT ===========
print("Model class:", type(model))
print("Model config:", model.config)
if hasattr(model, "peft_config"):
    print("PEFT LOADED:", model.peft_config)
else:
    print("PEFT NÃO CARREGADO!")
# ====================================================================

app = Flask(__name__)


@app.route("/infer", methods=["POST"])
def infer():
    try:
        print("=== CHEGOU NO ENDPOINT /infer ===")
        prompt = request.json.get("prompt", "")
        max_new_tokens = request.json.get("max_new_tokens", 128)
        client_ip = request.remote_addr
        print(f"[LLM DEBUG] Requisição recebida de {client_ip}")
        print(f"[LLM DEBUG] Prompt: {repr(prompt)[:500]}")  # Limita a 500 chars para não poluir
        print(f"[LLM DEBUG] max_new_tokens: {max_new_tokens}")
        
        # Configurar tokenizer corretamente
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048).to("cuda")
        
        # Parâmetros de geração otimizados para o fine-tuning
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,  # Reduzido para menos aleatoriedade
                top_p=0.9,
                repetition_penalty=1.1,  # Reduzido para evitar repetições excessivas
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                early_stopping=True
            )
        
        resposta = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove o prompt da resposta, se presente
        if resposta.startswith(prompt):
            resposta = resposta[len(prompt):].lstrip()
        
        # Remover token de fim se presente
        if "[FIM]" in resposta:
            resposta = resposta.split("[FIM]")[0].strip()
        
        print(f"[LLM DEBUG] Resposta gerada: {repr(resposta)[:500]}")
        return jsonify({"response": resposta})
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
