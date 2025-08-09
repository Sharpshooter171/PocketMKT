#!/usr/bin/env python3
"""
Script para configurar credenciais Google para testes E2E
Execute este script se você não tem as credenciais configuradas
"""

import os
import json
from pathlib import Path

def criar_credenciais_mock():
    """Cria arquivo de credenciais mock para testes"""
    
    print("🔧 CONFIGURADOR DE CREDENCIAIS GOOGLE")
    print("="*50)
    
    # Caminho do arquivo de credenciais
    creds_path = "/home/igor-caldas/PocketMKT/credentials.json"
    
    if os.path.exists(creds_path):
        print(f"✅ Arquivo de credenciais já existe: {creds_path}")
        resposta = input("Deseja sobrescrever? (s/N): ").lower()
        if resposta != 's':
            print("❌ Operação cancelada")
            return
    
    print("\n📋 OPÇÕES DE CONFIGURAÇÃO:")
    print("1. Criar arquivo mock (para testes sem Google)")
    print("2. Instruções para credenciais reais")
    print("3. Cancelar")
    
    opcao = input("\nEscolha uma opção (1-3): ").strip()
    
    if opcao == "1":
        # Criar arquivo mock
        mock_creds = {
            "type": "service_account",
            "project_id": "pocket-mkt-test",
            "private_key_id": "mock_key_id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
            "client_email": "mock@pocket-mkt-test.iam.gserviceaccount.com",
            "client_id": "mock_client_id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mock%40pocket-mkt-test.iam.gserviceaccount.com"
        }
        
        try:
            with open(creds_path, 'w') as f:
                json.dump(mock_creds, f, indent=2)
            
            print(f"✅ Arquivo mock criado: {creds_path}")
            print("⚠️ ATENÇÃO: Este é um arquivo MOCK - as validações Google falharão")
            print("💡 Use este modo para testar apenas o retorno JSON do Flask")
            
        except Exception as e:
            print(f"❌ Erro ao criar arquivo: {e}")
    
    elif opcao == "2":
        print("\n📖 INSTRUÇÕES PARA CREDENCIAIS REAIS:")
        print("="*50)
        print("1. Acesse https://console.cloud.google.com/")
        print("2. Crie um novo projeto ou selecione existente")
        print("3. Ative as APIs:")
        print("   • Google Sheets API")
        print("   • Google Calendar API") 
        print("   • Gmail API")
        print("4. Vá em 'Credenciais' > 'Criar credenciais' > 'Conta de serviço'")
        print("5. Baixe o arquivo JSON e salve como:")
        print(f"   {creds_path}")
        print("6. Execute novamente o teste E2E")
        print("\n💡 Documentação: https://developers.google.com/workspace/guides/create-credentials")
    
    else:
        print("❌ Operação cancelada")

def verificar_ambiente():
    """Verifica se o ambiente está pronto para testes E2E"""
    print("\n🔍 VERIFICANDO AMBIENTE:")
    print("="*30)
    
    # Verificar Flask
    try:
        import requests
        response = requests.get("http://127.0.0.1:5000/teste", timeout=5)
        if response.status_code == 200:
            print("✅ Flask rodando em http://127.0.0.1:5000")
        else:
            print(f"⚠️ Flask respondeu com código: {response.status_code}")
    except Exception:
        print("❌ Flask não está rodando ou inacessível")
        print("💡 Inicie o Flask antes de executar os testes E2E")
    
    # Verificar credenciais
    creds_path = "/home/igor-caldas/PocketMKT/credentials.json"
    if os.path.exists(creds_path):
        try:
            with open(creds_path) as f:
                creds = json.load(f)
            if creds.get('private_key') == "-----BEGIN PRIVATE KEY-----\nMOCK_PRIVATE_KEY\n-----END PRIVATE KEY-----\n":
                print("⚠️ Credenciais MOCK detectadas - validações Google serão simuladas")
            else:
                print("✅ Credenciais Google configuradas")
        except Exception:
            print("❌ Arquivo de credenciais corrompido")
    else:
        print("❌ Credenciais Google não encontradas")
    
    # Verificar dependências
    try:
        import googleapiclient
        print("✅ Google API Client instalada")
    except ImportError:
        print("❌ Google API Client não instalada")
        print("💡 Execute: pip install google-api-python-client google-auth")

if __name__ == "__main__":
    criar_credenciais_mock()
    verificar_ambiente()
    
    print(f"\n🚀 Para executar os testes E2E:")
    print(f"cd /home/igor-caldas/PocketMKT/eval")
    print(f"python test_e2e_integracoes.py")
