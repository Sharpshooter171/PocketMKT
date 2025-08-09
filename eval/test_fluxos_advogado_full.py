import requests
import csv
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000/atendimento"

# Exemplos de fluxos e mensagens para cada fluxo
fluxos_testes = {
    "aprovacao_peticao": [
        "Tenho uma petição pronta, preciso de aprovação.",
        "O cliente já assinou o documento?",
        "Existe alguma pendência para protocolar?"
    ],
    "alerta_prazo": [
        "Existe algum prazo importante para hoje?",
        "Quais prazos vencem esta semana?",
    ],
    "honorarios": [
        "Quais são os honorários deste processo?",
        "Tenho parcelas pendentes de honorários?"
    ],
    "documento_juridico": [
        "Preciso gerar uma procuração para um novo cliente.",
        "Como faço para enviar documentos para o cliente?"
    ],
    "envio_documento_cliente": [
        "Envie o contrato para o cliente assinar.",
        "O cliente já recebeu o documento?"
    ],
    "consulta_andamento": [
        "Qual o andamento do processo 12345-67.2024.8.09.0001?",
        "Houve alguma atualização recente no processo?"
    ],
    "pagamento_fora_padrao": [
        "Recebi um pagamento fora do padrão.",
        "Como registrar um pagamento extra do cliente?"
    ],
    "indicacao": [
        "Fui indicado por um cliente.",
        "Como registrar uma indicação de cliente?"
    ],
    "documento_pendente": [
        "Há algum documento pendente do cliente?",
        "Quais documentos faltam para o processo?"
    ],
    "revisao_documento": [
        "Preciso revisar um contrato antes de enviar.",
        "A petição inicial foi revisada?"
    ],
    "status_negociacao": [
        "Qual o status da negociação com o cliente João?",
        "A negociação foi fechada?"
    ],
    "decisao_permuta": [
        "O cliente aceitou a permuta?",
        "Há alguma decisão pendente sobre a permuta?"
    ],
    "sumico_cliente": [
        "Não consigo contato com o cliente.",
        "O cliente sumiu e não responde."
    ],
    "update_clientes_aguardando": [
        "Quais clientes estão aguardando retorno?",
        "Preciso atualizar a lista de clientes em espera."
    ],
    "update_documento_pendente": [
        "Atualize o status dos documentos pendentes.",
        "Documentos pendentes foram regularizados?"
    ],
    "nao_atendimento_area": [
        "Vocês atendem Direito Marítimo?",
        "Minha área é Direito Espacial, há atendimento?"
    ],
    "status_multiplos_processos": [
        "Quero saber o status de todos meus processos.",
        "Me mostre o andamento dos processos ativos."
    ],
    "notificacao_cliente": [
        "Envie uma notificação para o cliente.",
        "O cliente foi notificado sobre a audiência?"
    ],
    "alterar_cancelar_agendamento": [
        "Quero alterar meu agendamento.",
        "Preciso cancelar a reunião marcada para amanhã."
    ],
    "resumo_estatisticas": [
        "Me mostre um resumo das minhas estatísticas.",
        "Quantos casos ganhei este mês?"
    ],
    "lembrete_audiencia": [
        "Me lembre da audiência de amanhã.",
        "Envie um lembrete para a equipe."
    ],
    "enviar_resumo_caso": [
        "Envie um resumo do caso para o cliente.",
        "Preciso de um resumo detalhado do processo."
    ],
}

# Parâmetros fixos (ajuste se necessário)
numero_teste = "11988887777"
escritorio_id = "FLUXO_ADV_TESTE"
tipo_usuario = "advogado"

for fluxo, mensagens in fluxos_testes.items():
    print(f"\n=== TESTE DE FLUXO: {fluxo.upper()} ===\n")
    resultados = []

    for idx, mensagem in enumerate(mensagens, start=1):
        payload = {
            "mensagem": mensagem,
            "numero": numero_teste,
            "escritorio_id": escritorio_id,
            "tipo": tipo_usuario
        }
        try:
            response = requests.post(BASE_URL, json=payload, timeout=30)
            resposta_json = response.json()
            resposta = resposta_json.get('resposta') or resposta_json.get('reply') or resposta_json
            print(f"{idx}. Usuário: {mensagem}")
            print(f"   Bot: {resposta}\n")
            resultados.append([idx, mensagem, resposta])
            time.sleep(1)  # Simula digitação
        except Exception as e:
            print(f"{idx}. ERRO ao enviar mensagem: {mensagem}")
            print(f"   {e}\n")
            resultados.append([idx, mensagem, f"ERRO: {e}"])
            time.sleep(1)

    # Salvar resultados em CSV para análise posterior
    csv_filename = f"resultados_{fluxo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(csv_filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Passo", "Mensagem do Usuário", "Resposta do Bot"])
        writer.writerows(resultados)

    print(f"=== FIM DO TESTE | Resultados do fluxo '{fluxo}' salvos em: {csv_filename} ===\n")

print("\n=== TODOS OS TESTES FINALIZADOS ===\n")
