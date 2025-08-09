from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, PeftConfig
import torch, os

os.environ["HF_HOME"] = "/opt/dlami/nvme/hf_cache"
os.environ["TRANSFORMERS_CACHE"] = "/opt/dlami/nvme/hf_cache"

adapter_path = "content/fine_tuned_advocacia"
offload_folder = "/opt/dlami/nvme/offload"
peft_config = PeftConfig.from_pretrained(adapter_path)
base_model = peft_config.base_model_name_or_path

model = AutoModelForCausalLM.from_pretrained(
    base_model,
    torch_dtype=torch.float16,
    device_map="auto",
    offload_folder=offload_folder
)
tokenizer = AutoTokenizer.from_pretrained(base_model)
model = PeftModel.from_pretrained(
    model,
    adapter_path,
    offload_folder=offload_folder
)

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
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        outputs = model.generate(**inputs, max_new_tokens=max_new_tokens)
        resposta = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove o prompt da resposta, se presente
        if resposta.startswith(prompt):
            resposta = resposta[len(prompt):].lstrip()
        print(f"[LLM DEBUG] Resposta gerada: {repr(resposta)[:500]}")
        return jsonify({"response": resposta})
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
