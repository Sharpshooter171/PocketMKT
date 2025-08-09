import unittest
import requests

# URL base do seu Flask (a mesma do outro script)
BASE_URL = "http://127.0.0.1:5000/processar_atendimento"

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

class TestBotJuridicoFluxos(unittest.TestCase):

    def test_fluxos_respostas_sem_erro(self):
        """
        Testa todos os fluxos definidos em 'mensagens_teste' e verifica
        se a resposta não contém um indicativo de erro.
        """
        for fluxo, mensagem in mensagens_teste.items():
            with self.subTest(fluxo=fluxo):
                payload = {
                    "mensagem": mensagem,
                    "numero": numero_teste,
                    "escritorio_id": escritorio_id
                }
                try:
                    response = requests.post(BASE_URL, json=payload, timeout=30)
                    
                    # Verifica se a requisição foi bem sucedida
                    self.assertEqual(response.status_code, 200, f"Fluxo '{fluxo}' retornou status code {response.status_code}")

                    resposta_json = response.json()
                    resposta = resposta_json.get('resposta') or resposta_json.get('reply') or resposta_json

                    # Verifica se a resposta existe
                    self.assertIsNotNone(resposta, f"Fluxo '{fluxo}' não retornou uma resposta.")

                    # Verifica se a resposta não contém a palavra "erro" (case-insensitive)
                    self.assertNotIn("erro", str(resposta).lower(), f"Fluxo '{fluxo}' retornou uma resposta de erro: {resposta}")

                except requests.exceptions.RequestException as e:
                    self.fail(f"Erro de requisição no fluxo '{fluxo}': {e}")

if __name__ == '__main__':
    print("Executando testes unitários dos fluxos do Bot Jurídico...")
    unittest.main(verbosity=2)
