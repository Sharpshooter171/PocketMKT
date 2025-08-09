import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
LORA_DIR = "mistral-finetune-advocacia-45k/checkpoint-3750"

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
tokenizer.pad_token = tokenizer.eos_token
bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, quantization_config=bnb_config, device_map="auto")
model = PeftModel.from_pretrained(base_model, LORA_DIR)

def responder(prompt, max_new_tokens=25):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0,
            top_p=0.9,
            repetition_penalty=1.8,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )
    resposta = tokenizer.decode(output[0], skip_special_tokens=True)
    resposta = resposta.split("Atendente:")[-1].strip().split("\n")[0]  # pega só a primeira frase após "Atendente:"
    return resposta

# Coloque seus prompts aqui!
eval_prompts = [
    "Usuário: Preciso cancelar uma consulta.\nAtendente:",
    "Usuário: Já enviei meus documentos, o que falta?\nAtendente:",
    "Usuário: Qual o horário de funcionamento?\nAtendente:",
    "Usuário: Qual o prazo para recurso de apelação?\nAtendente:",
    "Usuário: Pode me dar um parecer sobre meu caso?\nAtendente:",
    "Usuário: Advogado, o que devo fazer para recorrer?\nAtendente:",
    "Usuário: kkk perdi a hora do atendimento, e agora?\nAtendente:",
    "Usuário: Oi, só testando se responde.\nAtendente:",
    "Usuário: Prezados, gostaria de remarcar minha audiência.\nAtendente:",
    "Usuário: E aí, posso remarcar rapidão?\nAtendente:",
]

system_prompt = """Você é um assistente virtual de triagem para um escritório de advocacia. O cliente já está cadastrado. Responda apenas dúvidas administrativas, de agenda, documentos pendentes e rotinas do escritório. Nunca forneça opiniões jurídicas, detalhes técnicos, leis ou prazos. Não invente procedimentos. Se a dúvida for técnica, explique que o advogado responderá posteriormente. Use frases curtas, profissionais, acolhedoras e SEM repetir a coleta de dados. Reconheça informações já fornecidas pelo cliente e oriente sobre próximos passos.
"""

with open("eval_results.txt", "w", encoding="utf-8") as f:
    for i, prompt in enumerate(eval_prompts):
        full_prompt = f"{system_prompt}\n{prompt}"
        resposta = responder(full_prompt)
        print(f"Prompt {i+1}: {prompt}")
        print(f"Resposta: {resposta}\n")
        f.write(f"Prompt {i+1}: {prompt}\nResposta: {resposta}\n\n")
