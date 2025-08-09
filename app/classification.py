from app.ollama_service import get_llama_response

def classificar_tipo_mensagem(texto):
    print(f"🔍 Classificando mensagem: {texto}")
    prompt = f"Classifique a seguinte mensagem como 'Lead', 'Dúvida' ou 'Reclamação':\nMensagem: \"{texto}\""
    resposta = get_llama_response(prompt).strip().lower()
    if "lead" in resposta:
        return "Lead"
    elif "dúvida" in resposta:
        return "Dúvida"
    elif "reclamação" in resposta:
        return "Reclamação"
    return "Indefinido"

def extrair_infos(texto_usuario):
    prompt = (
        f"O cliente enviou: \"{texto_usuario}\"\n"
        "Extraia as informações possíveis:\n"
        "- Nome completo\n- Necessidade (motivo do contato)\n- Preferência de período (manhã, tarde, noite ou data)\n"
        "Se algo não for identificado, use explicitamente: NOME_NAO_ENCONTRADO, NECESSIDADE_NAO_ENCONTRADA, PREFERENCIA_NAO_ENCONTRADA.\n"
        "Responda só assim:\nNome: ...\nNecessidade: ...\nPreferencia: ..."
    )
    resposta = get_llama_response(prompt, system_prompt="Você é um extrator seguro. Seja objetivo.")
    return resposta
