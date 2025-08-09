"""
Configuração do Sistema de Atendimento Legal
============================================

Este arquivo contém as configurações principais do sistema de intake de casos legais
com integração LLM, Google Sheets, Gmail e Google Calendar.
"""

import os
from datetime import timedelta

class Config:
    """Configuração base do sistema"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'legal-intake-system-2024'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Google APIs
    GOOGLE_CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    GOOGLE_TOKEN_FILE = os.environ.get('GOOGLE_TOKEN_FILE', 'token.json')
    
    # Scopes do Google
    GOOGLE_SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/calendar'
    ]
    
    # Whisper
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large
    MAX_AUDIO_SIZE_MB = int(os.environ.get('MAX_AUDIO_SIZE_MB', 25))
    
    # LLM Configuration
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    LLM_MODEL = os.environ.get('LLM_MODEL', 'llama2')
    LLM_TIMEOUT = int(os.environ.get('LLM_TIMEOUT', 30))
    
    # Sistema de conversas
    CONVERSA_TIMEOUT_HOURS = int(os.environ.get('CONVERSA_TIMEOUT_HOURS', 24))
    MAX_HISTORICO_MENSAGENS = int(os.environ.get('MAX_HISTORICO_MENSAGENS', 50))
    
    # Planilhas Google
    PLANILHA_TEMPLATE_ID = os.environ.get('PLANILHA_TEMPLATE_ID', '')
    PASTA_PLANILHAS_DRIVE = os.environ.get('PASTA_PLANILHAS_DRIVE', '')
    
    # Email
    EMAIL_REMETENTE = os.environ.get('EMAIL_REMETENTE', 'sistema@escritorio.com')
    ASSUNTO_EMAIL_DEFAULT = 'Nova Planilha de Casos - Sistema Legal'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/legal_system.log')
    
    # Dados obrigatórios para casos
    CAMPOS_OBRIGATORIOS_CASO = [
        'nome_cliente',
        'tipo_caso', 
        'descricao_caso'
    ]
    
    # Tipos de caso suportados
    TIPOS_CASO_VALIDOS = [
        'trabalhista',
        'civil',
        'criminal',
        'previdenciario',
        'consumidor',
        'familia',
        'tributario',
        'empresarial',
        'imobiliario',
        'outros'
    ]
    
    # Níveis de urgência
    NIVEIS_URGENCIA = [
        'baixa',
        'media', 
        'alta',
        'urgente'
    ]
    
    @staticmethod
    def init_app(app):
        """Inicializa configurações na aplicação Flask"""
        pass


class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    TESTING = False
    
    # Configurações de segurança para produção
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """Configuração para testes"""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False


# Configuração baseada no ambiente
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


# Prompts do sistema
PROMPTS = {
    'extracao_dados': """
Você é um assistente especializado em direito brasileiro. Analise o texto abaixo e extraia APENAS as informações estruturadas que conseguir identificar claramente.

TEXTO DO CLIENTE:
{texto}

DADOS JÁ COLETADOS:
{dados_existentes}

Extraia e retorne APENAS em formato JSON válido as seguintes informações que conseguir identificar no texto:

{{
  "nome_cliente": "string (nome completo se mencionado)",
  "cpf_cliente": "string (CPF se mencionado)",
  "telefone_cliente": "string (telefone se mencionado)",
  "email_cliente": "string (email se mencionado)", 
  "tipo_caso": "string (área do direito: trabalhista, civil, criminal, etc)",
  "descricao_caso": "string (resumo do problema legal)",
  "valor_causa": "string (valor monetário se mencionado)",
  "data_fatos": "string (quando aconteceu se mencionado)",
  "urgencia": "string (alta, média, baixa)",
  "documentos_mencionados": ["array de strings com documentos citados"],
  "outras_partes": ["array com nomes de outras pessoas/empresas envolvidas"]
}}

IMPORTANTE:
- Retorne APENAS o JSON, sem texto adicional
- Se não conseguir identificar um campo, não o inclua no JSON
- Não invente informações que não estão no texto
- Seja preciso e conservador na extração
""",

    'resposta_contextual': """
Você é um assistente virtual especializado em atendimento legal para escritórios de advocacia no Brasil. 

CONTEXTO DA CONVERSA:
{historico}

DADOS JÁ COLETADOS:
{dados_coletados}

ÚLTIMA MENSAGEM DO CLIENTE:
{mensagem_cliente}

INSTRUÇÕES:
1. Responda de forma natural, empática e profissional
2. Faça perguntas específicas para coletar dados que ainda faltam
3. Demonstre compreensão do caso e dê orientações iniciais quando apropriado
4. Mantenha o tom acolhedor e confiável
5. Se já tiver dados suficientes, confirme e informe sobre os próximos passos
6. Não peça documentos específicos ainda, apenas informações básicas
7. Seja conciso mas completo (máximo 200 palavras)

DADOS ESSENCIAIS PARA COLETAR:
- Nome completo
- Tipo de caso (área do direito)
- Descrição detalhada do problema
- Urgência da situação

Responda naturalmente como um advogado experiente faria:
""",

    'onboarding_advogado': """
Extraia as informações do advogado do texto abaixo em JSON:

Texto: {mensagem}

Retorne apenas o JSON com os campos que conseguir identificar:
{{
  "nome": "nome completo",
  "oab": "número da OAB", 
  "email": "email profissional",
  "escritorio": "nome do escritório",
  "especialidade": "área de especialização"
}}
"""
}


# Headers padrão para planilhas
PLANILHA_HEADERS = [
    'Data/Hora',
    'Nome Cliente', 
    'CPF',
    'Telefone',
    'Email',
    'Tipo de Caso',
    'Descrição do Caso',
    'Valor da Causa',
    'Data dos Fatos',
    'Urgência',
    'Documentos Mencionados',
    'Outras Partes',
    'Status',
    'Advogado Responsável',
    'Observações'
]


print("⚙️ Configurações do Sistema Legal carregadas!")
print(f"🤖 Modelo LLM: {Config.LLM_MODEL}")
print(f"🎤 Modelo Whisper: {Config.WHISPER_MODEL}")
print(f"📊 Campos obrigatórios: {len(Config.CAMPOS_OBRIGATORIOS_CASO)}")
print(f"📋 Tipos de caso: {len(Config.TIPOS_CASO_VALIDOS)}")
