import requests
from app.prompt_config import prompt_config

print("🧠 Carregando serviço de integração com Ollama...")

OLLAMA_API_URL = "http://3.92.70.163:8000/infer"


def get_llama_response(client_message, system_prompt=None, contexto_cliente=None):
    print("🧠 Chamando get_llama_response()...")
    try:
        if system_prompt is None:
            system_prompt = prompt_config['system_prompt']
        contexto = ""
        if contexto_cliente:
            contexto = (
                f"\n\n[Contexto do cliente]\n"
                f"Nome: {contexto_cliente.get('nome','')}\n"
                f"Necessidade: {contexto_cliente.get('necessidade','')}\n"
                f"Preferência: {contexto_cliente.get('preferencia_horario','')}\n"
            )
        full_prompt = f"{system_prompt}{contexto}\nUsuário: {client_message}\nAtendente:"
        print("📨 PROMPT COMPLETO ENVIADO:")
        print(full_prompt)
        response = requests.post(OLLAMA_API_URL, json={
            "model": "mistral-7b-instruct-v0.2-advocacia",
            "prompt": full_prompt,
            "stream": False
        }, timeout=90)
        if response.status_code != 200:
            print(f"❌ ERRO HTTP {response.status_code}: {response.text}")
            return "Erro ao obter resposta da IA."
        try:
            full_response = response.json().get("response", "Desculpe, não consegui entender.")
            if not isinstance(full_response, str):
                full_response = str(full_response)
        except Exception as e:
            print(f"❌ Erro ao processar resposta JSON: {e}")
            return "Erro ao processar resposta da IA."
        print("✅ RESPOSTA COMPLETA DA IA:")
        print(full_response)
        return full_response  # <--- NÃO use truncate_response aqui!
    except Exception as e:
        print("❌ ERRO AO CHAMAR OLLAMA:", e)
        return "Erro ao processar a resposta da IA."

# 🔎 Classificação de intenção (rótulos fechados, saída 1 rótulo)
def classify_intent_llm(texto: str) -> str:
    """Retorna um rótulo dentre:
    relato_caso | agendar_consulta_cliente | enviar_documento_cliente | consulta_andamento_cliente | outro
    """
    import requests
    try:
        system = (
            "Você é um classificador. Responda APENAS um rótulo exato, em minúsculas, "
            "entre: relato_caso | agendar_consulta_cliente | enviar_documento_cliente | consulta_andamento_cliente | outro. "
            "Sem explicações, sem texto adicional."
        )
        prompt = f"{system}\n\nMENSAGEM: {texto}\nRÓTULO:"
        payload = {"model": "mistral-7b-instruct-v0.2-advocacia", "prompt": prompt, "stream": False}
        resp = requests.post(OLLAMA_API_URL, json=payload, timeout=45)
        if resp.status_code != 200:
            print(f"❌ classify_intent_llm HTTP {resp.status_code}: {resp.text}")
            return "outro"
        out = (resp.json().get("response") or "").strip().split()[0].lower()
        return out if out in {
            "relato_caso","agendar_consulta_cliente","enviar_documento_cliente","consulta_andamento_cliente","outro"
        } else "outro"
    except Exception as e:
        print("❌ classify_intent_llm erro:", e)
        return "outro"
