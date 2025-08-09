import sys
import os
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.routes.text_processing import (
    fluxo_onboarding_advogado,
    fluxo_aprovacao_peticao,
    fluxo_alerta_prazo,
    fluxo_honorarios,
    fluxo_documento_juridico,
    fluxo_envio_documento_cliente,
    fluxo_consulta_andamento,
    fluxo_pagamento_fora_padrao,
    fluxo_indicacao,
    fluxo_documento_pendente,
    fluxo_revisao_documento,
    fluxo_status_negociacao,
    fluxo_decisao_permuta,
    fluxo_sumiço_cliente,
    fluxo_update_clientes_aguardando,
    fluxo_update_documento_pendente,
    fluxo_nao_atendimento_area,
    fluxo_status_multiplos_processos,
    fluxo_notificacao_cliente,
    fluxo_alterar_cancelar_agendamento,
    fluxo_resumo_estatisticas,
    fluxo_lembrete_audiencia,
    fluxo_enviar_resumo_caso
)

class TestFluxos(unittest.TestCase):

    def test_fluxo_aprovacao_peticao(self):
        self.assertIsNotNone(fluxo_aprovacao_peticao("aprovo a minuta"))
        self.assertIsNotNone(fluxo_aprovacao_peticao("ok, pode enviar"))
        self.assertIsNotNone(fluxo_aprovacao_peticao("revisar o documento, por favor"))
        self.assertEqual(fluxo_aprovacao_peticao("bom dia"), {'status': 'pendente'})

    def test_fluxo_alerta_prazo(self):
        self.assertIsNotNone(fluxo_alerta_prazo("me lembre do prazo amanhã"))
        self.assertIsNotNone(fluxo_alerta_prazo("qual a data da audiência?"))
        self.assertIsNone(fluxo_alerta_prazo("preciso de um modelo de contrato"))

    def test_fluxo_revisao_documento(self):
        self.assertIsNotNone(fluxo_revisao_documento("por favor, revise este contrato"))
        self.assertIsNotNone(fluxo_revisao_documento("preciso ajustar a petição"))
        self.assertIsNotNone(fluxo_revisao_documento("corrigir a cláusula 4"))
        self.assertIsNone(fluxo_revisao_documento("o documento está aprovado"))

    def test_fluxo_alterar_cancelar_agendamento(self):
        self.assertIsNotNone(fluxo_alterar_cancelar_agendamento("quero cancelar nosso agendamento"))
        self.assertIsNotNone(fluxo_alterar_cancelar_agendamento("podemos alterar o horário da reunião?"))
        self.assertIsNone(fluxo_alterar_cancelar_agendamento("confirmando nosso horário"))

    def test_fluxo_resumo_estatisticas(self):
        self.assertIsNotNone(fluxo_resumo_estatisticas("me envie um resumo dos casos"))
        self.assertIsNotNone(fluxo_resumo_estatisticas("qual o relatório de honorários?"))
        self.assertIsNotNone(fluxo_resumo_estatisticas("preciso de uma estatística de clientes"))
        self.assertIsNone(fluxo_resumo_estatisticas("resumo do caso do João")) # Deve cair em outro fluxo

    def test_fluxo_nao_atendimento_area(self):
        self.assertIsNotNone(fluxo_nao_atendimento_area("não atendo casos criminais"))
        self.assertIsNotNone(fluxo_nao_atendimento_area("isso é fora da minha área"))
        self.assertIsNone(fluxo_nao_atendimento_area("sou especialista em direito civil"))

if __name__ == '__main__':
    unittest.main()
