#!/usr/bin/env python3
"""
Exemplos específicos de validação de cada integração Google
Use este script para testar integrações isoladamente
"""

import requests
import json
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

BASE_URL = "http://127.0.0.1:5000"

def exemplo_validacao_planilha():
    """
    Exemplo: Cliente relata caso -> Validar se planilha foi criada
    """
    print("🧪 TESTE: Criação de Planilha Google Sheets")
    print("="*50)
    
    # Enviar relato de caso completo
    payload = {
        "mensagem": "Sou João Silva, CPF 111.222.333-44, trabalho na empresa ABC há 3 anos. Fui demitido sem justa causa e quero entrar com ação trabalhista.",
        "numero": "11999990001", 
        "escritorio_id": "ESCRITORIO_TESTE"
    }
    
    print("📤 Enviando relato de caso...")
    response = requests.post(f"{BASE_URL}/processar_atendimento", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Resposta recebida: {result.get('resposta', '')[:100]}...")
        
        # Verificar se retornou ID da planilha
        sheet_id = result.get('id_planilha') or result.get('sheet_id')
        if sheet_id:
            print(f"✅ ID da planilha retornado: {sheet_id}")
            
            # Tentar validar na API do Google Sheets
            try:
                # Substitua pelo seu arquivo de credenciais
                creds = Credentials.from_service_account_file(
                    '/home/igor-caldas/PocketMKT/credentials.json',
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
                
                service = build('sheets', 'v4', credentials=creds)
                
                # Ler dados da planilha
                sheet = service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range="A1:H10"  # Primeiras 10 linhas
                ).execute()
                
                valores = sheet.get('values', [])
                print(f"✅ Planilha validada! {len(valores)} linhas encontradas")
                
                if valores:
                    print("📋 Primeira linha (cabeçalho):")
                    print(f"   {valores[0]}")
                    
                    if len(valores) > 1:
                        print("📋 Segunda linha (dados):")
                        print(f"   {valores[1]}")
                
            except Exception as e:
                print(f"❌ Erro ao validar planilha: {e}")
                print("💡 Verifique se as credenciais Google estão configuradas")
        else:
            print("❌ ID da planilha não retornado no JSON")
            print(f"🔍 Campos disponíveis: {list(result.keys())}")
    else:
        print(f"❌ Erro HTTP: {response.status_code}")

def exemplo_validacao_calendario():
    """
    Exemplo: Cliente agenda consulta -> Validar se evento foi criado
    """
    print("\n🧪 TESTE: Criação de Evento Google Calendar")
    print("="*50)
    
    payload = {
        "mensagem": "Preciso agendar uma consulta para segunda-feira às 14h para discutir meu caso trabalhista.",
        "numero": "11999990001",
        "escritorio_id": "ESCRITORIO_TESTE"
    }
    
    print("📤 Enviando solicitação de agendamento...")
    response = requests.post(f"{BASE_URL}/processar_atendimento", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Resposta recebida: {result.get('resposta', '')[:100]}...")
        
        # Verificar se retornou ID do evento
        event_id = result.get('id_evento') or result.get('event_id') or result.get('calendar_id')
        if event_id:
            print(f"✅ ID do evento retornado: {event_id}")
            
            try:
                creds = Credentials.from_service_account_file(
                    '/home/igor-caldas/PocketMKT/credentials.json',
                    scopes=['https://www.googleapis.com/auth/calendar.readonly']
                )
                
                service = build('calendar', 'v3', credentials=creds)
                
                # Buscar evento
                event = service.events().get(
                    calendarId='primary',
                    eventId=event_id
                ).execute()
                
                print(f"✅ Evento validado!")
                print(f"📅 Título: {event.get('summary', 'Sem título')}")
                print(f"🕐 Início: {event.get('start', {}).get('dateTime', 'Não definido')}")
                print(f"📍 Local: {event.get('location', 'Não definido')}")
                
            except Exception as e:
                print(f"❌ Erro ao validar evento: {e}")
        else:
            print("❌ ID do evento não retornado no JSON")
    else:
        print(f"❌ Erro HTTP: {response.status_code}")

def exemplo_validacao_email():
    """
    Exemplo: Advogado completa onboarding -> Validar se email foi enviado
    """
    print("\n🧪 TESTE: Envio de Email Gmail")
    print("="*50)
    
    payload = {
        "mensagem": "Sou Dr. Carlos Oliveira, OAB/SP 987654, email carlos@advocacia.com, especialidade direito civil.",
        "numero": "11988887777"
    }
    
    print("📤 Enviando onboarding de advogado...")
    response = requests.post(f"{BASE_URL}/mensagem", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Resposta recebida: {result.get('reply', '')[:100]}...")
        
        # Verificar se retornou status de email
        email_status = result.get('email_enviado') or result.get('email_status') or result.get('message_id')
        if email_status:
            print(f"✅ Status de email retornado: {email_status}")
            
            try:
                creds = Credentials.from_service_account_file(
                    '/home/igor-caldas/PocketMKT/credentials.json',
                    scopes=['https://www.googleapis.com/auth/gmail.readonly']
                )
                
                service = build('gmail', 'v1', credentials=creds)
                
                # Buscar emails enviados nos últimos 5 minutos
                from datetime import datetime, timedelta
                cinco_min_atras = int((datetime.now() - timedelta(minutes=5)).timestamp())
                
                messages = service.users().messages().list(
                    userId='me',
                    q=f'in:sent after:{cinco_min_atras}',
                    maxResults=5
                ).execute()
                
                emails_encontrados = messages.get('messages', [])
                print(f"✅ {len(emails_encontrados)} emails enviados nos últimos 5 minutos")
                
                for msg in emails_encontrados[:2]:  # Mostrar apenas os 2 primeiros
                    message = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['Subject', 'To']
                    ).execute()
                    
                    headers = message.get('payload', {}).get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sem assunto')
                    to = next((h['value'] for h in headers if h['name'] == 'To'), 'Destinatário não encontrado')
                    
                    print(f"📧 Email: {subject} -> {to}")
                
            except Exception as e:
                print(f"❌ Erro ao validar emails: {e}")
        else:
            print("❌ Status de email não retornado no JSON")
    else:
        print(f"❌ Erro HTTP: {response.status_code}")

def verificar_retorno_esperado():
    """
    Mostra exemplo do retorno JSON esperado para cada integração
    """
    print("\n📋 RETORNOS JSON ESPERADOS:")
    print("="*50)
    
    print("🔹 Para criação de planilha:")
    exemplo_planilha = {
        "resposta": "Seu caso foi registrado com sucesso!",
        "id_planilha": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        "dados_coletados": {
            "nome_cliente": "João Silva",
            "tipo_caso": "trabalhista",
            "descricao_caso": "Demissão sem justa causa"
        }
    }
    print(json.dumps(exemplo_planilha, indent=2, ensure_ascii=False))
    
    print("\n🔹 Para agendamento:")
    exemplo_agenda = {
        "resposta": "Consulta agendada para segunda-feira às 14h",
        "id_evento": "abc123def456ghi789",
        "data_agendamento": "2025-08-11T14:00:00-03:00"
    }
    print(json.dumps(exemplo_agenda, indent=2, ensure_ascii=False))
    
    print("\n🔹 Para email:")
    exemplo_email = {
        "resposta": "Cadastro concluído! Verifique seu email.",
        "email_enviado": True,
        "message_id": "1234567890abcdef",
        "destinatario": "carlos@advocacia.com"
    }
    print(json.dumps(exemplo_email, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("🧪 VALIDADOR DE INTEGRAÇÕES GOOGLE - EXEMPLOS")
    print("="*60)
    
    verificar_retorno_esperado()
    
    print(f"\n🚀 Escolha um teste para executar:")
    print(f"1. Validar criação de planilha")
    print(f"2. Validar criação de evento")
    print(f"3. Validar envio de email")
    print(f"4. Executar todos")
    
    opcao = input(f"\nOpção (1-4): ").strip()
    
    if opcao == "1":
        exemplo_validacao_planilha()
    elif opcao == "2":
        exemplo_validacao_calendario()
    elif opcao == "3":
        exemplo_validacao_email()
    elif opcao == "4":
        exemplo_validacao_planilha()
        exemplo_validacao_calendario()
        exemplo_validacao_email()
    else:
        print("❌ Opção inválida")
