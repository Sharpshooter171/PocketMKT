import sys
import os
import unittest

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.routes.text_processing import (
    extrair_nome,
    extrair_oab,
    extrair_email,
    extrair_nome_escritorio,
    extrair_area,
    extrair_numero_processo
)

class TestExtracao(unittest.TestCase):

    def test_extrair_nome(self):
        self.assertEqual(extrair_nome("meu nome é João da Silva"), "João Da Silva")
        self.assertEqual(extrair_nome("Sou a Dra. Maria Oliveira"), "Maria Oliveira")
        self.assertEqual(extrair_nome("aqui é o carlos pereira"), "Carlos Pereira")
        self.assertIsNone(extrair_nome("qual o seu nome?"))
        self.assertIsNone(extrair_nome("bom dia"))
        self.assertEqual(extrair_nome("Dr. José"), "José") # Nome simples com título
        self.assertEqual(extrair_nome("falar com fernanda"), "Fernanda") # Nome sem "meu nome é"

    def test_extrair_oab(self):
        self.assertEqual(extrair_oab("minha oab é 123456 SP"), ("123456", "SP"))
        self.assertEqual(extrair_oab("OAB/RJ 98765"), ("98765", "RJ"))
        self.assertEqual(extrair_oab("oab 123.456-MG"), ("123456", "MG")) # Com pontuação
        self.assertEqual(extrair_oab("oab: 112233ba"), ("112233", "BA")) # Com "ba" minúsculo
        self.assertIsNone(extrair_oab("sou advogado")[0])
        self.assertEqual(extrair_oab("oab 12345"), (None, None)) # Número curto demais sem UF

    def test_extrair_email(self):
        self.assertEqual(extrair_email("meu email é teste@exemplo.com"), "teste@exemplo.com")
        self.assertEqual(extrair_email("pode mandar para joao.silva-123@meu.dominio.co.uk"), "joao.silva-123@meu.dominio.co.uk")
        self.assertIsNone(extrair_email("não tenho email"))
        self.assertEqual(extrair_email("contato em email @dominio.com"), "email@dominio.com") # Com espaço

    def test_extrair_nome_escritorio(self):
        self.assertEqual(extrair_nome_escritorio("trabalho no Silva & Advogados"), "Silva & Advogados")
        self.assertEqual(extrair_nome_escritorio("meu escritório é o Advocacia Central"), "Advocacia Central")
        self.assertEqual(extrair_nome_escritorio("sou profissional autônomo"), "Autônomo")
        self.assertIsNone(extrair_nome_escritorio("sou advogado apenas"))

    def test_extrair_area(self):
        self.assertIn('Civil', extrair_area("sou especialista em direito civil"))
        self.assertIn('Trabalhista', extrair_area("atuo na área trabalhista e de família"))
        self.assertIn('Família', extrair_area("atuo na área trabalhista e de família"))
        self.assertEqual(len(extrair_area("atuo na área trabalhista e de família")), 2)
        self.assertEqual(extrair_area("gosto de futebol"), [])

    def test_extrair_numero_processo(self):
        self.assertEqual(extrair_numero_processo("o número do processo é 1234567-89.2023.1.23.4567"), "1234567-89.2023.1.23.4567")
        self.assertEqual(extrair_numero_processo("consulta para o proc. 00001234520238260001"), "00001234520238260001")
        self.assertIsNone(extrair_numero_processo("qual o número do seu cpf?"))

if __name__ == '__main__':
    unittest.main()
