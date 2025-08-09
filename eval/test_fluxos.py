import requests
import csv
from datetime import datetime

# URL base do seu Flask
BASE_URL = "http://127.0.0.1:5000/processar_atendimento"
# Ou, se for testar de outro dispositivo na rede, use o IP:
# BASE_URL = "http://192.168.0.127:5000/processar_atendimento"

# Mensagens de teste para cada fluxo
mensagens_teste = {
    "fluxo_onboarding_advogado": "Quero me cadastrar como advogado no escritório.",
    "fluxo_aprovacao_peticao": "A minuta está correta, pode protocolar.",
    "fluxo_alerta_prazo": "Pode me lembrar do prazo da audiência de amanhã?",
    "fluxo_honorarios": "Quais são os honorários para esse tipo de caso?",
    "fluxo_documento_juridico": "Preciso de um modelo de contrato de prestação de serviço.",
    "fluxo_envio_documento_cliente": "Pode enviar o documento por e-mail para o cliente?",
    "fluxo_consulta_andamento": "Quero consultar o andamento do processo número 123456-78.2023.8.09.0001.",
    "fluxo_pagamento_fora_padrao": "Consigo pagar os honorários com um imóvel em permuta?",
    "fluxo_indicacao": "Você pode me indicar um advogado especialista em direito previdenciário?",
    "fluxo_documento_pendente": "Faltou enviar a certidão de nascimento, posso mandar agora?",
    "fluxo_revisao_documento": "Preciso revisar o contrato que enviei ontem.",
    "fluxo_status_negociacao": "Já negociou os honorários com o cliente?",
    "fluxo_decisao_permuta": "Prefere receber em dinheiro ou aceitar permuta?",
    "fluxo_sumiço_cliente": "O cliente sumiu, não responde há dias.",
    "fluxo_update_clientes_aguardando": "Atualize a lista de clientes que ainda não responderam.",
    "fluxo_update_documento_pendente": "Atualização: o cliente enviou o documento pendente.",
    "fluxo_nao_atendimento_area": "Não atendo casos de direito penal.",
    "fluxo_status_multiplos_processos": "Quero o status dos meus 5 processos em andamento.",
    "fluxo_notificacao_cliente": "O bot já notificou o cliente sobre o prazo?",
    "fluxo_alterar_cancelar_agendamento": "Preciso cancelar o agendamento marcado para amanhã.",
    "fluxo_resumo_estatisticas": "Me envie um resumo das estatísticas do escritório este mês.",
    "fluxo_lembrete_audiencia": "Lembrete de audiência para dia 15 de agosto, por favor.",
    "fluxo_enviar_resumo_caso": "Pode enviar um resumo do caso da Maria Silva para o advogado responsável?"
}

# Número e escritório fictício para simular os testes
numero_teste = "11999999999"
escritorio_id = "ESCRITORIO_TESTE"

resultados = []
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
nome_arquivo_csv = f"resultados_teste_fluxos_{timestamp}.csv"

print("\n=== TESTE AUTOMÁTICO DE FLUXOS DO BOT JURÍDICO ===\n")

# Abre o arquivo CSV para escrita
with open(nome_arquivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Fluxo', 'Mensagem de Teste', 'Resposta do Bot', 'Status']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for fluxo, mensagem in mensagens_teste.items():
        payload = {
            "mensagem": mensagem,
            "numero": numero_teste,
            "escritorio_id": escritorio_id
        }
        try:
            response = requests.post(BASE_URL, json=payload, timeout=30)
            resposta_json = response.json()
            resposta = resposta_json.get('resposta') or resposta_json.get('reply') or resposta_json
            status = "✅" if resposta and "erro" not in str(resposta).lower() else "⚠️"
        except Exception as e:
            resposta = f"Erro na requisição: {e}"
            status = "❌"
        
        # Adiciona na lista para exibição no console
        resultados.append((fluxo, mensagem, resposta, status))
        
        # Escreve no arquivo CSV
        writer.writerow({
            'Fluxo': fluxo,
            'Mensagem de Teste': mensagem,
            'Resposta do Bot': str(resposta),
            'Status': status
        })

# Exibir resultados bonitos no console
for fluxo, mensagem, resposta, status in resultados:
    print(f"\n{status} [{fluxo}]")
    print(f"Mensagem de teste: {mensagem}")
    print(f"Resposta do bot:\n{resposta}")
    print("-" * 60)

print(f"\n=== FIM DOS TESTES ===\n")
print(f"Resultados exportados para o arquivo: {nome_arquivo_csv}\n")
