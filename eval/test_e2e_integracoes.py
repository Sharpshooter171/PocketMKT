import requests
import csv
import time
import json
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os

# Configurações
BASE_URL = "http://127.0.0.1:5000"
ENDPOINT_PROCESSAR = f"{BASE_URL}/processar_atendimento"
ENDPOINT_MENSAGEM = f"{BASE_URL}/mensagem"

# Cenários E2E focados em integrações
cenarios_e2e = [
    {
        "nome": "E2E - Cliente relato completo com planilha",
        "tipo": "cliente",
        "mensagem": "Oi, sou Maria Silva, CPF 123.456.789-00, telefone (11) 99999-9999. Fui demitida sem justa causa ontem da empresa XYZ. Trabalhei lá por 2 anos como vendedora. Quero saber meus direitos trabalhistas e entrar com ação.",
        "validacoes_esperadas": {
            "planilha": True,
            "email": True,
            "dados_extraidos": True
        }
    },
    {
        "nome": "E2E - Cliente agendamento consulta",
        "tipo": "cliente", 
        "mensagem": "Preciso agendar uma consulta urgente com o advogado para discutir meu caso trabalhista. Tenho disponibilidade na próxima segunda-feira à tarde ou terça de manhã.",
        "validacoes_esperadas": {
            "calendario": True,
            "email": True,
            "planilha": True
        }
    },
    {
        "nome": "E2E - Advogado onboarding completo",
        "tipo": "advogado",
        "mensagem": "Sou Dr. Ricardo Mendes, OAB/SP 123456, email ricardo.mendes@advocacia.com, especialista em direito trabalhista e civil. Escritório: Mendes & Associados Advocacia.",
        "validacoes_esperadas": {
            "planilha": True,
            "email": True,
            "dados_extraidos": True
        }
    },
    {
        "nome": "E2E - Advogado solicita relatório com notificação",
        "tipo": "advogado",
        "mensagem": "Preciso de um relatório dos casos em andamento desta semana e me notifique sobre os prazos que vencem nos próximos 7 dias.",
        "validacoes_esperadas": {
            "email": True,
            "calendario": True,
            "planilha": False  # Consulta, não cria
        }
    }
]

class TestadorIntegracoes:
    def __init__(self):
        self.results = []
        self.google_services = {}
        self._init_google_services()
    
    def _init_google_services(self):
        """Inicializa serviços Google para validação"""
        try:
            # Tenta carregar credenciais do Google
            creds_path = "/home/igor-caldas/PocketMKT/credentials.json"  # Ajuste o caminho
            if os.path.exists(creds_path):
                creds = Credentials.from_service_account_file(
                    creds_path,
                    scopes=[
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/calendar',
                        'https://www.googleapis.com/auth/gmail.readonly'
                    ]
                )
                
                self.google_services = {
                    'sheets': build('sheets', 'v4', credentials=creds),
                    'calendar': build('calendar', 'v3', credentials=creds),
                    'gmail': build('gmail', 'v1', credentials=creds)
                }
                print("✅ Serviços Google inicializados com sucesso")
            else:
                print("⚠️ Credenciais Google não encontradas - modo simulado")
                self.google_services = {}
        except Exception as e:
            print(f"⚠️ Erro ao inicializar Google Services: {e}")
            self.google_services = {}
    
    def executar_cenario(self, cenario):
        """Executa um cenário E2E completo"""
        print(f"\n{'='*60}")
        print(f"🚀 EXECUTANDO: {cenario['nome']}")
        print(f"{'='*60}")
        
        # Passo 1: Enviar requisição
        resultado = self._enviar_requisicao(cenario)
        if not resultado:
            return None
        
        # Passo 2: Validar retorno JSON
        validacao_json = self._validar_retorno_json(resultado, cenario)
        
        # Passo 3: Validar APIs Google
        validacao_google = self._validar_apis_google(resultado, cenario)
        
        # Compilar resultado final
        resultado_final = {
            "cenario": cenario['nome'],
            "tipo": cenario['tipo'],
            "status_http": resultado.get('status_code'),
            "resposta_texto": resultado.get('resposta_texto', '')[:200],
            "validacao_json": validacao_json,
            "validacao_google": validacao_google,
            "score_final": self._calcular_score(validacao_json, validacao_google, cenario),
            "timestamp": datetime.now().isoformat()
        }
        
        self.results.append(resultado_final)
        self._imprimir_resultado(resultado_final)
        return resultado_final
    
    def _enviar_requisicao(self, cenario):
        """Passo 1: Enviar requisição para o Flask"""
        try:
            if cenario['tipo'] == 'cliente':
                url = ENDPOINT_PROCESSAR
                payload = {
                    "mensagem": cenario['mensagem'],
                    "numero": "11999990001",
                    "escritorio_id": "ESCRITORIO_TESTE"
                }
            else:
                url = ENDPOINT_MENSAGEM
                payload = {
                    "mensagem": cenario['mensagem'],
                    "numero": "11988887777"
                }
            
            print(f"📤 Enviando para: {url}")
            print(f"📦 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            response = requests.post(url, json=payload, timeout=30)
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                resposta_json = response.json()
                resposta_texto = resposta_json.get('resposta') or resposta_json.get('reply') or str(resposta_json)
                
                print(f"🤖 Resposta: {resposta_texto[:200]}...")
                
                return {
                    'status_code': response.status_code,
                    'json': resposta_json,
                    'resposta_texto': resposta_texto
                }
            else:
                print(f"❌ Erro HTTP: {response.status_code} - {response.text}")
                return {
                    'status_code': response.status_code,
                    'json': {},
                    'resposta_texto': f"Erro HTTP {response.status_code}"
                }
                
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return None
    
    def _validar_retorno_json(self, resultado, cenario):
        """Passo 2: Validar campos no retorno JSON"""
        validacao = {
            "id_planilha": None,
            "id_evento": None,
            "email_status": None,
            "dados_extraidos": None,
            "debug_info": None
        }
        
        resposta_json = resultado.get('json', {})
        resposta_texto = resultado.get('resposta_texto', '').lower()
        
        print(f"\n🔍 VALIDANDO RETORNO JSON:")
        
        # Buscar IDs e status no JSON
        for campo in ['id_planilha', 'sheet_id', 'planilha_id']:
            if campo in resposta_json:
                validacao['id_planilha'] = resposta_json[campo]
                print(f"✅ Planilha ID encontrado: {validacao['id_planilha']}")
                break
        
        for campo in ['id_evento', 'event_id', 'calendar_id']:
            if campo in resposta_json:
                validacao['id_evento'] = resposta_json[campo]
                print(f"✅ Evento ID encontrado: {validacao['id_evento']}")
                break
        
        for campo in ['email_enviado', 'email_status', 'message_id']:
            if campo in resposta_json:
                validacao['email_status'] = resposta_json[campo]
                print(f"✅ Email status encontrado: {validacao['email_status']}")
                break
        
        # Verificar dados extraídos
        if 'dados_coletados' in resposta_json or 'campos_extraidos' in resposta_json:
            validacao['dados_extraidos'] = True
            print(f"✅ Dados estruturados extraídos")
        
        # Verificar debug/log info
        if 'debug' in resposta_json:
            validacao['debug_info'] = resposta_json['debug']
            print(f"📋 Debug info disponível")
        
        # Buscar indicadores no texto da resposta
        indicadores = {
            'planilha': ['registrado', 'salvo', 'planilha', 'cadastrado'],
            'evento': ['agendado', 'marcado', 'calendario', 'consulta'],
            'email': ['email', 'notificacao', 'enviado', 'confirmacao']
        }
        
        for tipo, palavras in indicadores.items():
            if any(palavra in resposta_texto for palavra in palavras):
                print(f"📝 Indicador de {tipo} encontrado no texto")
        
        return validacao
    
    def _validar_apis_google(self, resultado, cenario):
        """Passo 3: Validar diretamente nas APIs Google"""
        validacao_google = {
            "planilha_validada": False,
            "evento_validado": False,
            "email_validado": False,
            "detalhes": []
        }
        
        if not self.google_services:
            validacao_google['detalhes'].append("Serviços Google não disponíveis - modo simulado")
            return validacao_google
        
        print(f"\n🔍 VALIDANDO APIS GOOGLE:")
        
        # Validar Google Sheets
        id_planilha = resultado.get('json', {}).get('id_planilha') or resultado.get('json', {}).get('sheet_id')
        if id_planilha and 'sheets' in self.google_services:
            try:
                sheet = self.google_services['sheets'].spreadsheets().values().get(
                    spreadsheetId=id_planilha, 
                    range="A1:H5"
                ).execute()
                
                valores = sheet.get('values', [])
                if valores:
                    validacao_google['planilha_validada'] = True
                    validacao_google['detalhes'].append(f"Planilha validada: {len(valores)} linhas")
                    print(f"✅ Planilha {id_planilha} validada - {len(valores)} linhas")
                else:
                    validacao_google['detalhes'].append("Planilha existe mas está vazia")
                    print(f"⚠️ Planilha {id_planilha} existe mas está vazia")
                    
            except Exception as e:
                validacao_google['detalhes'].append(f"Erro ao validar planilha: {str(e)}")
                print(f"❌ Erro ao validar planilha: {e}")
        
        # Validar Google Calendar
        id_evento = resultado.get('json', {}).get('id_evento') or resultado.get('json', {}).get('event_id')
        if id_evento and 'calendar' in self.google_services:
            try:
                event = self.google_services['calendar'].events().get(
                    calendarId='primary', 
                    eventId=id_evento
                ).execute()
                
                validacao_google['evento_validado'] = True
                validacao_google['detalhes'].append(f"Evento validado: {event.get('summary', 'Sem título')}")
                print(f"✅ Evento {id_evento} validado: {event.get('summary')}")
                
            except Exception as e:
                validacao_google['detalhes'].append(f"Erro ao validar evento: {str(e)}")
                print(f"❌ Erro ao validar evento: {e}")
        
        # Validar Gmail (últimos 10 emails enviados)
        if cenario['validacoes_esperadas'].get('email') and 'gmail' in self.google_services:
            try:
                # Buscar emails dos últimos 5 minutos
                cinco_min_atras = int((datetime.now() - timedelta(minutes=5)).timestamp())
                query = f"in:sent after:{cinco_min_atras}"
                
                messages = self.google_services['gmail'].users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=10
                ).execute()
                
                if messages.get('messages'):
                    validacao_google['email_validado'] = True
                    validacao_google['detalhes'].append(f"Emails recentes encontrados: {len(messages['messages'])}")
                    print(f"✅ Emails validados: {len(messages['messages'])} enviados recentemente")
                else:
                    validacao_google['detalhes'].append("Nenhum email recente encontrado")
                    print(f"⚠️ Nenhum email recente encontrado")
                    
            except Exception as e:
                validacao_google['detalhes'].append(f"Erro ao validar emails: {str(e)}")
                print(f"❌ Erro ao validar emails: {e}")
        
        return validacao_google
    
    def _calcular_score(self, validacao_json, validacao_google, cenario):
        """Calcula score baseado nas validações"""
        score = 0
        max_score = 100
        
        # Score por validação JSON (50%)
        if validacao_json['id_planilha'] and cenario['validacoes_esperadas'].get('planilha'):
            score += 15
        if validacao_json['id_evento'] and cenario['validacoes_esperadas'].get('calendario'):
            score += 15
        if validacao_json['email_status'] and cenario['validacoes_esperadas'].get('email'):
            score += 10
        if validacao_json['dados_extraidos'] and cenario['validacoes_esperadas'].get('dados_extraidos'):
            score += 10
        
        # Score por validação Google APIs (50%)
        if validacao_google['planilha_validada'] and cenario['validacoes_esperadas'].get('planilha'):
            score += 20
        if validacao_google['evento_validado'] and cenario['validacoes_esperadas'].get('calendario'):
            score += 20
        if validacao_google['email_validado'] and cenario['validacoes_esperadas'].get('email'):
            score += 10
        
        return min(score, max_score)
    
    def _imprimir_resultado(self, resultado):
        """Imprime resultado formatado"""
        print(f"\n📊 RESULTADO FINAL:")
        print(f"✅ Score: {resultado['score_final']}/100")
        print(f"📋 JSON: Planilha={bool(resultado['validacao_json']['id_planilha'])}, "
              f"Evento={bool(resultado['validacao_json']['id_evento'])}, "
              f"Email={bool(resultado['validacao_json']['email_status'])}")
        print(f"🔗 Google: Planilha={resultado['validacao_google']['planilha_validada']}, "
              f"Evento={resultado['validacao_google']['evento_validado']}, "
              f"Email={resultado['validacao_google']['email_validado']}")
        
        if resultado['validacao_google']['detalhes']:
            print(f"📝 Detalhes: {'; '.join(resultado['validacao_google']['detalhes'])}")
    
    def executar_todos_cenarios(self):
        """Executa todos os cenários E2E"""
        print("🚀 INICIANDO TESTES E2E - INTEGRAÇÕES GOOGLE")
        print("="*70)
        
        for i, cenario in enumerate(cenarios_e2e, 1):
            print(f"\n[{i}/{len(cenarios_e2e)}] {cenario['nome']}")
            self.executar_cenario(cenario)
            time.sleep(2)  # Pausa entre testes
        
        self._gerar_relatorio_final()
    
    def _gerar_relatorio_final(self):
        """Gera relatório consolidado"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"teste_e2e_integracoes_{timestamp}.csv"
        
        # Salvar CSV
        with open(csv_filename, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Cenário", "Tipo", "Score", "Status HTTP", "ID Planilha", "ID Evento", 
                "Email Status", "Planilha Validada", "Evento Validado", "Email Validado",
                "Detalhes Google", "Resposta", "Timestamp"
            ])
            
            for r in self.results:
                writer.writerow([
                    r['cenario'], r['tipo'], f"{r['score_final']}/100", r['status_http'],
                    r['validacao_json']['id_planilha'] or 'N/A',
                    r['validacao_json']['id_evento'] or 'N/A',
                    r['validacao_json']['email_status'] or 'N/A',
                    r['validacao_google']['planilha_validada'],
                    r['validacao_google']['evento_validado'],
                    r['validacao_google']['email_validado'],
                    '; '.join(r['validacao_google']['detalhes']),
                    r['resposta_texto'], r['timestamp']
                ])
        
        # Estatísticas finais
        scores = [r['score_final'] for r in self.results]
        media_score = sum(scores) / len(scores) if scores else 0
        
        planilhas_ok = sum(1 for r in self.results if r['validacao_google']['planilha_validada'])
        eventos_ok = sum(1 for r in self.results if r['validacao_google']['evento_validado'])
        emails_ok = sum(1 for r in self.results if r['validacao_google']['email_validado'])
        
        print(f"\n{'='*70}")
        print(f"📊 RELATÓRIO FINAL E2E")
        print(f"{'='*70}")
        print(f"📈 Score médio: {media_score:.1f}/100")
        print(f"📊 Google Sheets: {planilhas_ok}/{len(self.results)} validados")
        print(f"📅 Google Calendar: {eventos_ok}/{len(self.results)} validados")
        print(f"📧 Gmail: {emails_ok}/{len(self.results)} validados")
        print(f"📁 Relatório detalhado: {csv_filename}")
        print(f"{'='*70}")

if __name__ == "__main__":
    testador = TestadorIntegracoes()
    testador.executar_todos_cenarios()
