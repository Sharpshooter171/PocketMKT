import sys
import os
import unittest

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.routes.text_processing import (
    fluxo_aprovacao_peticao,
    fluxo_alerta_prazo,
    fluxo_revisao_documento,
    fluxo_status_negociacao,
    fluxo_indicacao,
    fluxo_consulta_andamento,
    fluxo_enviar_resumo_caso,
    fluxo_honorarios,
    fluxo_documento_juridico,
    extrair_nome,
    extrair_numero_processo
)

class TestFluxos(unittest.TestCase):

    def test_fluxo_aprovacao_peticao(self):
        # Casos Positivos (Aprovação)
        self.assertEqual(fluxo_aprovacao_peticao("aprovo a minuta")['status'], "aprovado")
        self.assertEqual(fluxo_aprovacao_peticao("ok, pode protocolar")['status'], "aprovado")
        self.assertEqual(fluxo_aprovacao_peticao("concordo com os termos, pode seguir")['status'], "aprovado")
        self.assertEqual(fluxo_aprovacao_peticao("autorizo o envio do documento")['status'], "aprovado")
        self.assertEqual(fluxo_aprovacao_peticao("Aprovado.")['status'], "aprovado")

        # Casos Positivos (Revisão)
        self.assertEqual(fluxo_aprovacao_peticao("revisar o documento, por favor")['status'], "revisar")
        self.assertEqual(fluxo_aprovacao_peticao("preciso que altere a cláusula 4")['status'], "revisar")
        self.assertEqual(fluxo_aprovacao_peticao("não aprovei, precisa corrigir o nome")['status'], "revisar")
        self.assertEqual(fluxo_aprovacao_peticao("ajustar o valor antes de enviar")['status'], "revisar")
        self.assertEqual(fluxo_aprovacao_peticao("tem um errro de digitassão, corrija pf")['status'], "revisar") # Erro ortográfico

        # Casos Negativos (Pendentes)
        self.assertEqual(fluxo_aprovacao_peticao("bom dia, alguma novidade?")['status'], "pendente")
        self.assertEqual(fluxo_aprovacao_peticao("vou analisar a minuta e retorno em breve")['status'], "pendente")
        self.assertEqual(fluxo_aprovacao_peticao("recebi o documento, obrigado")['status'], "pendente")
        self.assertEqual(fluxo_aprovacao_peticao("qual o prazo para aprovar?")['status'], "pendente")

    def test_fluxo_alerta_prazo(self):
        # Casos Positivos
        self.assertIsNotNone(fluxo_alerta_prazo("não esquece do prazo de amanhã"))
        self.assertIsNotNone(fluxo_alerta_prazo("temos audiência dia 5"))
        self.assertIsNotNone(fluxo_alerta_prazo("me lembre da audiência na sexta-feira"))
        self.assertIsNotNone(fluxo_alerta_prazo("qual o prazo para a contestação?"))
        self.assertIsNotNone(fluxo_alerta_prazo("lembrete importante sobre o prazo"))

        # Casos Negativos
        self.assertIsNone(fluxo_alerta_prazo("preciso de um modelo de contrato"))
        self.assertIsNone(fluxo_alerta_prazo("o cliente aprovou a petição"))
        self.assertIsNone(fluxo_alerta_prazo("a audiência foi um sucesso"))
        self.assertIsNone(fluxo_alerta_prazo("me envie o resumo do caso, por favor"))

    def test_fluxo_revisao_documento(self):
        # Casos Positivos
        self.assertIsNotNone(fluxo_revisao_documento("por favor, revise a cláusula 3"))
        self.assertIsNotNone(fluxo_revisao_documento("preciso que corrija o contrato"))
        self.assertIsNotNone(fluxo_revisao_documento("ajuste o parágrafo final do acordo"))
        self.assertIsNotNone(fluxo_revisao_documento("verifique o documento que enviei")) # Sinônimo
        self.assertIsNotNone(fluxo_revisao_documento("o nome da testemunha está errado, favor corrigir"))

        # Casos Negativos
        self.assertIsNone(fluxo_revisao_documento("o cliente aprovou a petição"))
        self.assertIsNone(fluxo_revisao_documento("enviando o documento para o cliente"))
        self.assertIsNone(fluxo_revisao_documento("qual o status da negociação?"))

    def test_fluxo_consulta_andamento(self):
        # Positivos (com informação)
        self.assertIsNotNone(fluxo_consulta_andamento("qual o andamento do processo 1234567-89.2023.1.23.4567"))
        self.assertIsNotNone(fluxo_consulta_andamento("consulta o processo do cliente João da Silva"))
        self.assertIsNotNone(fluxo_consulta_andamento("me dá um update do processo da Maria Souza"))

        # Positivos (sem informação, pedindo dados)
        self.assertEqual(fluxo_consulta_andamento("como está o processo?")['status'], "info_faltante")
        self.assertEqual(fluxo_consulta_andamento("qual o andamento?")['status'], "info_faltante")
        self.assertEqual(fluxo_consulta_andamento("e o processo, alguma novidade?")['status'], "info_faltante")

        # Negativos
        self.assertIsNone(fluxo_consulta_andamento("preciso de uma cópia da petição"))
        self.assertIsNone(fluxo_consulta_andamento("o processo foi arquivado"))
        self.assertIsNone(fluxo_consulta_andamento("vamos processar a empresa X"))

    def test_fluxo_enviar_resumo_caso(self):
        # Positivos
        self.assertIsNotNone(fluxo_enviar_resumo_caso("me manda o resumo do caso da Maria"))
        self.assertIsNotNone(fluxo_enviar_resumo_caso("resumir o caso para o novo advogado"))
        self.assertIsNotNone(fluxo_enviar_resumo_caso("pode fazer um sumário do processo, por favor?")) # Sinônimo
        self.assertIsNotNone(fluxo_enviar_resumo_caso("enviar resumo")) # Incompleto

        # Negativos
        self.assertIsNone(fluxo_enviar_resumo_caso("o caso foi encerrado com sucesso"))
        self.assertIsNone(fluxo_enviar_resumo_caso("o cliente resumiu o que aconteceu"))
        self.assertIsNone(fluxo_enviar_resumo_caso("apresente suas estatísticas de resumo"))

    def test_fluxos_com_multipla_intencao(self):
        # Múltiplas intenções
        msg1 = "ok, aprovo a minuta. por favor, me lembre do prazo na sexta."
        self.assertEqual(fluxo_aprovacao_peticao(msg1)['status'], "aprovado")
        self.assertIsNotNone(fluxo_alerta_prazo(msg1))

        msg2 = "revise o contrato e me envie o resumo do caso do Pedro."
        self.assertIsNotNone(fluxo_revisao_documento(msg2))
        self.assertIsNotNone(fluxo_enviar_resumo_caso(msg2))

        msg3 = "qual o andamento do processo e como estão os honorários?"
        self.assertIsNotNone(fluxo_consulta_andamento(msg3))
        self.assertIsNotNone(fluxo_honorarios(msg3))

if __name__ == '__main__':
    unittest.main()
