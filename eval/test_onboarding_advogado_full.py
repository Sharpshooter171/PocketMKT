import requests
import csv
import time
from datetime import datetime

# Configuração do endpoint do Flask local
BASE_URL = "http://127.0.0.1:5000/atendimento"

# Simulação de conversação de onboarding de advogado autônomo
conversa_onboarding = [
    "Olá! Gostaria de me cadastrar como advogado na plataforma.",
    "Meu nome é Dr. Rafael Souza.",
    "Meu número da OAB é 123456/SP.",
    "Meu e-mail é rafael.souza@advocacia.com.br.",
    "Minha área de atuação principal é Direito Trabalhista.",
    "Sim, trabalho sozinho (sou autônomo).",
    "Não tenho CNPJ ainda.",
    "Posso cadastrar depois um endereço de escritório?",
    "Obrigado pela atenção!"
]

# Para guardar o histórico do teste
resultados = []

# Parâmetros fictícios de usuário (pode customizar)
numero_teste = "11988887777"
escritorio_id = "ONBOARDING_ADV_TESTE"

print("\n=== TESTE DE FLUXO: ONBOARDING ADVOGADO AUTÔNOMO ===\n")

for idx, mensagem in enumerate(conversa_onboarding, start=1):
    payload = {
        "mensagem": mensagem,
        "numero": numero_teste,
        "escritorio_id": escritorio_id,
        "tipo": "advogado"
    }
    try:
        response = requests.post(BASE_URL, json=payload, timeout=30)
        resposta_json = response.json()
        resposta = resposta_json.get('resposta') or resposta_json.get('reply') or resposta_json
        print(f"{idx}. Usuário: {mensagem}")
        print(f"   Bot: {resposta}\n")
        resultados.append([idx, mensagem, resposta])
        time.sleep(1)  # Dá uma pausa para simular tempo de digitação
    except Exception as e:
        print(f"{idx}. ERRO ao enviar mensagem: {mensagem}")
        print(f"   {e}\n")
        resultados.append([idx, mensagem, f"ERRO: {e}"])
        time.sleep(1)

# Salvar resultados em CSV para análise
csv_filename = f"resultados_onboarding_advogado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open(csv_filename, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Passo", "Mensagem do Usuário", "Resposta do Bot"])
    writer.writerows(resultados)

print(f"\n=== FIM DO TESTE | Resultados salvos em: {csv_filename} ===\n")
