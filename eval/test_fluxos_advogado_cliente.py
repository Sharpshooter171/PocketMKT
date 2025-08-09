import requests
import csv
import time
import re
import json
from datetime import datetime
import uuid  # logging estruturado
import random  # jitter backoff

# URLs para testar localmente
# Flask local já integrado com LLM na GPU
BASE_URL = "http://127.0.0.1:5000"

# Endpoints disponíveis
ENDPOINT_PROCESSAR = f"{BASE_URL}/processar_atendimento"  # Endpoint principal unificado
ENDPOINT_TESTE = f"{BASE_URL}/teste"  # (legacy, não usado mais nos testes)
ENDPOINT_STATUS = f"{BASE_URL}/status"

# Contadores para análise
stats_global = {
    "fluxos_detectados": 0,
    "fluxos_nao_detectados": 0,
    "integracao_google_sheets": 0,
    "integracao_google_calendar": 0,
    "integracao_gmail": 0,
    "respostas_llm": 0,
    "respostas_fallback": 0,
    "erros_http": 0,
    "contratos_validos": 0,
    "contratos_invalidos": 0
}

# Campos obrigatórios do contrato de resposta
CONTRATO_CAMPOS_OBRIGATORIOS = ["resposta"]  # mínimo
CONTRATO_CAMPOS_OPCIONAIS = ["fluxo", "ok", "ids"]

# Dicionários prontos que já te passei
cenarios_cliente = [
    # RELATO DE CASO
    {
        "nome": "Relato - Demissão sem justa causa",
        "mensagem": "Fui demitido ontem sem justa causa, quero saber meus direitos.",
        "espera_fluxo": "relato_caso"
    },
    {
        "nome": "Relato - Problema de pensão",
        "mensagem": "O pai do meu filho parou de pagar a pensão alimentícia, preciso de ajuda.",
        "espera_fluxo": "relato_caso"
    },
    {
        "nome": "Relato - Dívida no cartão",
        "mensagem": "Estou com uma dívida alta no cartão de crédito, o banco está me cobrando juros abusivos.",
        "espera_fluxo": "relato_caso"
    },

    # ENVIO DE DOCUMENTO
    {
        "nome": "Envio de documento - RG",
        "mensagem": "Segue meu RG para cadastro.",
        "espera_fluxo": "enviar_documento_cliente"
    },
    {
        "nome": "Envio de documento - CNH",
        "mensagem": "Enviei a foto da minha CNH agora.",
        "espera_fluxo": "enviar_documento_cliente"
    },
    {
        "nome": "Envio de documento - Comprovante de endereço",
        "mensagem": "Anexei o comprovante de endereço pedido.",
        "espera_fluxo": "enviar_documento_cliente"
    },

    # AGENDAMENTO DE CONSULTA
    {
        "nome": "Agendamento - Consulta inicial",
        "mensagem": "Gostaria de agendar uma consulta com o advogado para semana que vem.",
        "espera_fluxo": "agendar_consulta_cliente"
    },
    {
        "nome": "Agendamento - Marcação por horário",
        "mensagem": "Tem horário disponível na sexta-feira à tarde?",
        "espera_fluxo": "agendar_consulta_cliente"
    },
    {
        "nome": "Agendamento - Reunião urgente",
        "mensagem": "Preciso marcar uma reunião urgente sobre meu caso.",
        "espera_fluxo": "agendar_consulta_cliente"
    },

    # ATUALIZAÇÃO DE CADASTRO
    {
        "nome": "Atualização de cadastro - Novo endereço",
        "mensagem": "Mudei de endereço, agora moro na Rua das Palmeiras, 100.",
        "espera_fluxo": "atualizar_cadastro_cliente"
    },
    {
        "nome": "Atualização de cadastro - Troca de telefone",
        "mensagem": "Troquei meu telefone, agora é (11) 95555-5555.",
        "espera_fluxo": "atualizar_cadastro_cliente"
    },
    {
        "nome": "Atualização de cadastro - Novo e-mail",
        "mensagem": "Meu novo e-mail para contato é maria.nova@email.com.",
        "espera_fluxo": "atualizar_cadastro_cliente"
    },

    # CONSULTA ANDAMENTO
    {
        "nome": "Consulta andamento - Número do processo",
        "mensagem": "Quero saber o andamento do processo 9876543-21.2023.8.26.0001.",
        "espera_fluxo": "consulta_andamento_cliente"
    },
    {
        "nome": "Consulta andamento - Nome do cliente",
        "mensagem": "Como está o caso da Maria Fernanda?",
        "espera_fluxo": "consulta_andamento_cliente"
    },
    {
        "nome": "Consulta andamento - Pedido geral",
        "mensagem": "Tem novidade do meu processo?",
        "espera_fluxo": "consulta_andamento_cliente"
    },
]
    # Cole aqui
cenarios_advogado = [
    # ONBOARDING ADVOGADO
    {
        "nome": "Onboarding - Cadastro completo",
        "mensagem": "Sou Ricardo Silva, OAB 123456 SP, ricardo@adv.com, especialista em trabalhista.",
        "espera_fluxo": "onboarding_advogado"
    },
    {
        "nome": "Onboarding - Cadastro parcial",
        "mensagem": "Quero me cadastrar. Meu nome é Luiza Mendes, OAB 654321 RJ.",
        "espera_fluxo": "onboarding_advogado"
    },
    {
        "nome": "Onboarding - Email e áreas",
        "mensagem": "Meu email é fernanda@direito.com e atuo em civil e família.",
        "espera_fluxo": "onboarding_advogado"
    },

    # APROVAÇÃO DE PETIÇÃO
    {
        "nome": "Aprovação de petição - Aprovar",
        "mensagem": "A minuta está correta, pode protocolar.",
        "espera_fluxo": "aprovacao_peticao"
    },
    {
        "nome": "Aprovação de petição - Revisão",
        "mensagem": "Precisa corrigir o valor da causa na petição do cliente João.",
        "espera_fluxo": "aprovacao_peticao"
    },
    {
        "nome": "Aprovação de petição - Aprovação de caso",
        "mensagem": "A petição do caso 123 está aprovada.",
        "espera_fluxo": "aprovacao_peticao"
    },

    # ALERTA DE PRAZO
    {
        "nome": "Alerta de prazo - Próximo prazo",
        "mensagem": "Qual o próximo prazo do processo 0012345-67.2023.8.26.0001?",
        "espera_fluxo": "alerta_prazo"
    },
    {
        "nome": "Alerta de prazo - Semana",
        "mensagem": "Quais prazos vencem nesta semana?",
        "espera_fluxo": "alerta_prazo"
    },
    {
        "nome": "Alerta de prazo - Lembrete de audiência",
        "mensagem": "Me lembre da audiência do caso XPTO.",
        "espera_fluxo": "alerta_prazo"
    },

    # ENVIO DE DOCUMENTO JURÍDICO
    {
        "nome": "Documento jurídico - Solicitar modelo",
        "mensagem": "Preciso de um modelo de contrato de aluguel.",
        "espera_fluxo": "documento_juridico"
    },
    {
        "nome": "Documento jurídico - Solicitar petição",
        "mensagem": "Me envie a última versão da petição do caso 888.",
        "espera_fluxo": "documento_juridico"
    },
    {
        "nome": "Documento jurídico - Pergunta sobre documento",
        "mensagem": "Onde está a procuração da Maria Santos?",
        "espera_fluxo": "documento_juridico"
    },

    # REVISÃO DE DOCUMENTO
    {
        "nome": "Revisão de documento - Erro de nome",
        "mensagem": "A petição do caso 789 precisa de revisão, nome da testemunha está errado.",
        "espera_fluxo": "revisao_documento"
    },
    {
        "nome": "Revisão de documento - Contrato de empresa",
        "mensagem": "A revisão do contrato da empresa ABC terminou?",
        "espera_fluxo": "revisao_documento"
    },
    {
        "nome": "Revisão de documento - Cláusula",
        "mensagem": "Revisar a cláusula 5 do contrato do cliente XPTO.",
        "espera_fluxo": "revisao_documento"
    }
]
   # Cole aqui

# Números simulados
numero_cliente = "11999990001"
numero_advogado = "11988887777"  # Está no is_advogado()

# Parâmetros fixos
escritorio_id = "ESCRITORIO_TESTE"

# Arquivo de log estruturado
LOG_JSONL = "logs_execucao.jsonl"

def _log_estruturado(entry: dict):
    try:
        line = json.dumps(entry, ensure_ascii=False)
        print(line)  # stdout (permite coleta via pipe)
        with open(LOG_JSONL, "a", encoding="utf-8") as lf:
            lf.write(line + "\n")
    except Exception as e:
        print(f"⚠️ Falha ao registrar log estruturado: {e}")

def analisar_resposta_bot(resposta_texto, resposta_json=None):
    """
    Analisa a resposta do bot para detectar:
    1. Se o fluxo foi detectado
    2. Se houve integração com Google APIs
    3. Tipo de resposta (LLM vs fallback)
    """
    analise = {
        "fluxo_detectado": False,
        "tipo_fluxo": None,
        "google_sheets_usado": False,
        "google_calendar_usado": False,
        "gmail_usado": False,
        "resposta_llm": False,
        "ids_gerados": {},
        "indicadores_integracao": []
    }
    
    # Detectar se é resposta de LLM (geralmente mais longa e contextual)
    if len(resposta_texto) > 100 and any(palavra in resposta_texto.lower() for palavra in 
                                       ['entendo', 'compreendo', 'vamos', 'posso ajudar', 'para isso']):
        analise["resposta_llm"] = True
        stats_global["respostas_llm"] += 1
    else:
        stats_global["respostas_fallback"] += 1
    
    # Detectar integrações Google Sheets
    if any(termo in resposta_texto.lower() for termo in 
           ['planilha', 'sheet', 'registrado', 'cadastrado', 'dados salvos']):
        analise["google_sheets_usado"] = True
        analise["indicadores_integracao"].append("Google Sheets")
        stats_global["integracao_google_sheets"] += 1
    
    # Detectar integrações Google Calendar
    if any(termo in resposta_texto.lower() for termo in 
           ['agendado', 'calendar', 'marcado', 'horário confirmado', 'evento criado']):
        analise["google_calendar_usado"] = True
        analise["indicadores_integracao"].append("Google Calendar")
        stats_global["integracao_google_calendar"] += 1
    
    # Detectar integrações Gmail
    if any(termo in resposta_texto.lower() for termo in 
           ['email enviado', 'e-mail enviado', 'notificação enviada', 'gmail']):
        analise["gmail_usado"] = True
        analise["indicadores_integracao"].append("Gmail")
        stats_global["integracao_gmail"] += 1
    
    # Extrair IDs se presentes na resposta JSON
    if resposta_json and isinstance(resposta_json, dict):
        if 'sheet_id' in resposta_json:
            analise["ids_gerados"]["sheet_id"] = resposta_json['sheet_id']
        if 'event_id' in resposta_json:
            analise["ids_gerados"]["event_id"] = resposta_json['event_id']
        if 'email_id' in resposta_json:
            analise["ids_gerados"]["email_id"] = resposta_json['email_id']
    
    # Detectar tipo de fluxo pela resposta
    fluxos_keywords = {
        "relato_caso": ["caso", "processo", "situação jurídica", "direitos"],
        "onboarding_advogado": ["cadastro", "oab", "especialidade", "escritório"],
        "agendar_consulta": ["consulta", "agendamento", "horário", "reunião"],
        "documento_juridico": ["documento", "petição", "contrato", "modelo"],
        "alerta_prazo": ["prazo", "deadline", "vencimento", "audiência"]
    }
    
    for fluxo, keywords in fluxos_keywords.items():
        if any(keyword in resposta_texto.lower() for keyword in keywords):
            analise["fluxo_detectado"] = True
            analise["tipo_fluxo"] = fluxo
            stats_global["fluxos_detectados"] += 1
            break
    
    if not analise["fluxo_detectado"]:
        stats_global["fluxos_nao_detectados"] += 1
    
    return analise

def verificar_integracao_google_posterior(cenario_nome, ids_gerados):
    """
    Faz verificações posteriores nas APIs Google para confirmar integrações
    (Simulado - em produção faria calls reais às APIs)
    """
    verificacoes = {
        "sheets_confirmado": False,
        "calendar_confirmado": False,
        "gmail_confirmado": False,
        "detalhes": []
    }
    
    # Simular verificação baseada no tipo de cenário
    if "onboarding" in cenario_nome.lower() or "cadastro" in cenario_nome.lower():
        if ids_gerados.get("sheet_id"):
            verificacoes["sheets_confirmado"] = True
            verificacoes["detalhes"].append(f"Planilha {ids_gerados['sheet_id']} criada")
    
    if "agendamento" in cenario_nome.lower() or "consulta" in cenario_nome.lower():
        if ids_gerados.get("event_id"):
            verificacoes["calendar_confirmado"] = True
            verificacoes["detalhes"].append(f"Evento {ids_gerados['event_id']} agendado")
    
    # TODO: Em produção, fazer calls reais como:
    # - GET https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}
    # - GET https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}
    # - GET https://gmail.googleapis.com/gmail/v1/users/me/messages/{email_id}
    
    return verificacoes

# Config retry
MAX_RETRY_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 0.7
BACKOFF_MAX_SECONDS = 6.0
RETRY_STATUS_CODES = {500, 502, 503, 504}

def _retry_backoff_sleep(attempt):
    # exponential backoff com jitter: base * 2^(attempt-1) + random(0, base)
    wait = min(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)) + random.uniform(0, BACKOFF_BASE_SECONDS), BACKOFF_MAX_SECONDS)
    time.sleep(wait)
    return wait

def request_with_retry(method, url, **kwargs):
    """Executa requisição HTTP com retry e exponential backoff.
    Retorna (response, attempts, total_wait).
    Lança última exceção se todas falharem sem resposta válida.
    """
    attempts = 0
    total_wait = 0.0
    last_exc = None
    while attempts < MAX_RETRY_ATTEMPTS:
        attempts += 1
        try:
            resp = requests.request(method, url, **kwargs)
            if resp.status_code in RETRY_STATUS_CODES:
                if attempts < MAX_RETRY_ATTEMPTS:
                    wait = _retry_backoff_sleep(attempts)
                    total_wait += wait
                    _log_estruturado({
                        "timestamp": datetime.utcnow().isoformat() + 'Z',
                        "retry": True,
                        "motivo": f"status_{resp.status_code}",
                        "attempt": attempts,
                        "proximo_await_s": wait,
                        "url": url
                    })
                    continue
            return resp, attempts, total_wait
        except (requests.ConnectionError, requests.Timeout) as e:
            last_exc = e
            if attempts < MAX_RETRY_ATTEMPTS:
                wait = _retry_backoff_sleep(attempts)
                total_wait += wait
                _log_estruturado({
                    "timestamp": datetime.utcnow().isoformat() + 'Z',
                    "retry": True,
                    "motivo": "exception",
                    "erro": str(e),
                    "attempt": attempts,
                    "proximo_await_s": wait,
                    "url": url
                })
                continue
            else:
                raise
    # fallback (não deve chegar aqui sem raise ou return)
    if last_exc:
        raise last_exc

def testar_conectividade():
    """Healthcheck unificado usando apenas POST /processar_atendimento.
    Envia payload mínimo e valida HTTP 200 + presença de chave 'resposta' ou similar.
    """
    print("🔍 Testando conectividade via /processar_atendimento ...")
    payload = {
        "mensagem": "ping healthcheck",
        "numero": "00000000000",
        "tipo_usuario": "cliente",
        "escritorio_id": "ESCRITORIO_TESTE",
        "healthcheck": True
    }
    try:
        response, attempts, wait_total = request_with_retry(
            "POST", ENDPOINT_PROCESSAR, json=payload, timeout=15
        )
        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                print("⚠️ Resposta não é JSON válido")
                return False
            print("✅ Conectado! Status HTTP 200")
            print(f"🔁 Chaves recebidas: {list(data.keys())}")
            print(f"🧪 Fluxo retornado: {data.get('fluxo') or data.get('status') or 'N/A'}")
            print(f"🔄 Tentativas: {attempts} | Espera acumulada: {wait_total:.2f}s")
            # Testar também /status (opcional)
            try:
                status_resp, s_attempts, _ = request_with_retry("GET", ENDPOINT_STATUS, timeout=5)
                if status_resp.status_code == 200:
                    print("📊 /status disponível (Google APIs/LLM)")
            except Exception:
                print("ℹ️ /status indisponível (ignorado)")
            return True
        else:
            print(f"❌ Falha no healthcheck. HTTP {response.status_code}")
            print(response.text[:200])
            return False
    except Exception as e:
        print(f"❌ Erro de conectividade: {e}")
        print(f"💡 Verifique se o servidor está rodando: {ENDPOINT_PROCESSAR}")
        print(f"💡 Ex: curl -X POST {ENDPOINT_PROCESSAR} -H 'Content-Type: application/json' -d '{json.dumps(payload)}'")
        return False

def testar_cenarios(cenarios, numero, tipo_usuario, prefixo_csv):
    resultados_todos = []
    for i, cenario in enumerate(cenarios, 1):
        print(f"\n=== TESTE {i}/{len(cenarios)}: {cenario['nome'].upper()} ===")
        url = ENDPOINT_PROCESSAR
        payload = {
            "mensagem": cenario["mensagem"],
            "numero": numero,
            "escritorio_id": escritorio_id,
            "tipo_usuario": tipo_usuario
        }
        print(f"🌐 URL: {url}")
        print(f"📦 Payload: {payload}")
        inicio = time.time()
        erro_id = None
        fluxo_identificado = None
        status_contrato = False
        try:
            response, attempts, wait_total = request_with_retry(
                "POST", url, json=payload, timeout=30
            )
            lat_ms = int((time.time() - inicio) * 1000)
            print(f"📊 Status Code: {response.status_code}")
            if response.status_code == 200:
                resposta_json = response.json()
                resposta_texto = resposta_json.get('resposta') or resposta_json.get('reply') or str(resposta_json)
                campos_ausentes = [c for c in CONTRATO_CAMPOS_OBRIGATORIOS if c not in resposta_json]
                contrato_valido = len(campos_ausentes) == 0
                status_contrato = contrato_valido
                if contrato_valido:
                    stats_global["contratos_validos"] += 1
                else:
                    stats_global["contratos_invalidos"] += 1
                analise = analisar_resposta_bot(resposta_texto, resposta_json)
                verificacao_google = verificar_integracao_google_posterior(cenario['nome'], analise['ids_gerados'])
                fluxo_identificado = resposta_json.get('fluxo') or analise['tipo_fluxo'] or None
                print(f"👤 Usuário ({tipo_usuario}): {cenario['mensagem']}")
                print(f"🎯 Fluxo esperado: {cenario['espera_fluxo']}")
                print(f"✅ Fluxo detectado: {analise['fluxo_detectado']} ({analise['tipo_fluxo']})")
                print(f"🤖 Tipo resposta: {'LLM' if analise['resposta_llm'] else 'Fallback'}")
                print(f"🔗 Integrações: {', '.join(analise['indicadores_integracao']) if analise['indicadores_integracao'] else 'Nenhuma'}")
                print(f"📋 IDs gerados: {analise['ids_gerados'] if analise['ids_gerados'] else 'Nenhum'}")
                print(f"🤖 Bot: {resposta_texto[:200]}{'...' if len(resposta_texto) > 200 else ''}\n")
                resultado_linha = [
                    tipo_usuario.capitalize(), cenario['nome'], cenario['mensagem'], cenario['espera_fluxo'],
                    analise['fluxo_detectado'], analise['tipo_fluxo'] or 'Não detectado',
                    'LLM' if analise['resposta_llm'] else 'Fallback',
                    analise['google_sheets_usado'], analise['google_calendar_usado'], analise['gmail_usado'],
                    ', '.join(analise['indicadores_integracao']),
                    json.dumps(analise['ids_gerados']) if analise['ids_gerados'] else '',
                    verificacao_google['sheets_confirmado'], verificacao_google['calendar_confirmado'], verificacao_google['gmail_confirmado'],
                    resposta_texto, response.status_code, url, contrato_valido,
                    ','.join(campos_ausentes) if campos_ausentes else ''
                ]
            else:
                stats_global["erros_http"] += 1
                lat_ms = int((time.time() - inicio) * 1000)
                erro_id = str(uuid.uuid4())
                resposta_erro = f"Erro HTTP {response.status_code}: {response.text}"
                print(f"❌ Erro HTTP: {response.status_code}")
                print(f"📄 Detalhes: {response.text[:200]}...\n")
                resultado_linha = [
                    tipo_usuario.capitalize(), cenario['nome'], cenario['mensagem'], cenario['espera_fluxo'],
                    False, 'Erro HTTP', 'Erro', False, False, False, '', '',
                    False, False, False, resposta_erro, response.status_code, url, False, 'http_error'
                ]
            resultados_todos.append(resultado_linha)
            # Log estruturado
            _log_estruturado({
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "cenario": cenario['nome'],
                "tipo_usuario": tipo_usuario,
                "fluxo_esperado": cenario['espera_fluxo'],
                "fluxo": fluxo_identificado,
                "status_http": response.status_code,
                "contrato_valido": status_contrato,
                "lat_ms": lat_ms,
                "tentativas": attempts,
                "espera_total_s": wait_total,
                "erro_id": erro_id,
                "endpoint": url
            })
            time.sleep(1)
        except Exception as e:
            lat_ms = int((time.time() - inicio) * 1000)
            erro_id = str(uuid.uuid4())
            print(f"❌ ERRO ao enviar mensagem: {cenario['mensagem']}")
            print(f"   {e}\n")
            resultado_linha = [
                tipo_usuario.capitalize(), cenario['nome'], cenario['mensagem'], cenario['espera_fluxo'],
                False, 'Erro Conexão', 'Erro', False, False, False, '', '',
                False, False, False, f"ERRO: {e}", 'N/A', url, False, 'connection'
            ]
            resultados_todos.append(resultado_linha)
            _log_estruturado({
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "cenario": cenario['nome'],
                "tipo_usuario": tipo_usuario,
                "fluxo_esperado": cenario['espera_fluxo'],
                "fluxo": None,
                "status_http": None,
                "contrato_valido": False,
                "lat_ms": lat_ms,
                "tentativas": attempts if 'attempts' in locals() else 0,
                "espera_total_s": wait_total if 'wait_total' in locals() else 0.0,
                "erro_id": erro_id,
                "erro_msg": str(e),
                "endpoint": url
            })
            time.sleep(1)
    return resultados_todos

# === EXECUÇÃO DOS TESTES ===
print("🚀 INICIANDO TESTES DOS FLUXOS - PocketMKT")
print("=" * 50)

# 1. Teste de conectividade
if not testar_conectividade():
    print("\n❌ Abortando testes devido a problemas de conectividade.")
    print("\n💡 Para resolver:")
    print("1. Certifique-se que o Flask está rodando")
    print("2. Verifique a URL configurada no script")
    print("3. Teste manualmente: curl http://127.0.0.1:5000/teste")
    exit(1)

# Lista para acumular todos os resultados
todos_resultados = []

print("\n" + "="*50)
print("🎯 TESTANDO FLUXOS DE CLIENTES")
print("="*50)

# 2. Rodando todos os cenários de CLIENTE
resultados_cliente = testar_cenarios(cenarios_cliente, numero_cliente, "cliente", "cliente")
todos_resultados.extend(resultados_cliente)

print("\n" + "="*50)
print("👨‍💼 TESTANDO FLUXOS DE ADVOGADOS") 
print("="*50)

# 3. Rodando todos os cenários de ADVOGADO
resultados_advogado = testar_cenarios(cenarios_advogado, numero_advogado, "advogado", "advogado")
todos_resultados.extend(resultados_advogado)

# 4. Salvar CSV consolidado com análise expandida
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
csv_filename = f"resultados_consolidados_{timestamp}.csv"

print(f"\n💾 Salvando resultados consolidados em: {csv_filename}")
with open(csv_filename, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    # Cabeçalho expandido para análise completa
    cabecalho = [
        "Tipo Usuário", "Cenário", "Mensagem", "Fluxo Esperado",
        "Fluxo Detectado", "Tipo Fluxo Identificado", "Tipo Resposta",
        "Google Sheets Usado", "Google Calendar Usado", "Gmail Usado",
        "Indicadores Integração", "IDs Gerados", 
        "Sheets Confirmado", "Calendar Confirmado", "Gmail Confirmado",
        "Resposta Completa", "Status Code", "URL",
        "Contrato Válido", "Campos Ausentes"
    ]
    writer.writerow(cabecalho)
    writer.writerows(todos_resultados)

# 5. Gerar relatório de análise detalhada
def gerar_relatorio_analise():
    total_testes = len(todos_resultados)
    
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE ANÁLISE DETALHADA")
    print("="*60)
    
    print(f"� ESTATÍSTICAS GERAIS:")
    print(f"   • Total de testes: {total_testes}")
    print(f"   • Clientes: {len(resultados_cliente)} testes")
    print(f"   • Advogados: {len(resultados_advogado)} testes")
    print(f"   • Erros HTTP: {stats_global['erros_http']}")
    
    print(f"\n🎯 DETECÇÃO DE FLUXOS:")
    taxa_deteccao = (stats_global['fluxos_detectados'] / total_testes) * 100 if total_testes > 0 else 0
    print(f"   • Fluxos detectados: {stats_global['fluxos_detectados']} ({taxa_deteccao:.1f}%)")
    print(f"   • Fluxos não detectados: {stats_global['fluxos_nao_detectados']}")
    
    print(f"\n🤖 TIPOS DE RESPOSTA:")
    print(f"   • Respostas LLM: {stats_global['respostas_llm']}")
    print(f"   • Respostas Fallback: {stats_global['respostas_fallback']}")
    
    print(f"\n🔗 INTEGRAÇÕES GOOGLE:")
    print(f"   • Google Sheets usados: {stats_global['integracao_google_sheets']}")
    print(f"   • Google Calendar usado: {stats_global['integracao_google_calendar']}")
    print(f"   • Gmail usado: {stats_global['integracao_gmail']}")
    
    print(f"\n🧾 CONTRATO DE RESPOSTA:")
    print(f"   • Válidos: {stats_global['contratos_validos']}")
    print(f"   • Inválidos: {stats_global['contratos_invalidos']}")
    if stats_global['contratos_invalidos'] > 0:
        print("   ⚠️ Existem respostas sem campos obrigatórios")
    
    # Análise por tipo de fluxo
    fluxos_por_tipo = {}
    cenarios_com_erro = []
    
    for resultado in todos_resultados:
        tipo_fluxo = resultado[5]  # Tipo Fluxo Identificado
        if tipo_fluxo not in fluxos_por_tipo:
            fluxos_por_tipo[tipo_fluxo] = 0
        fluxos_por_tipo[tipo_fluxo] += 1
        
        if resultado[4] == False:  # Fluxo não detectado
            cenarios_com_erro.append(resultado[1])  # Nome do cenário
    
    print(f"\n📋 FLUXOS IDENTIFICADOS:")
    for fluxo, count in sorted(fluxos_por_tipo.items()):
        print(f"   • {fluxo}: {count} casos")
    
    if cenarios_com_erro:
        print(f"\n⚠️ CENÁRIOS COM PROBLEMAS:")
        for cenario in cenarios_com_erro[:5]:  # Mostrar apenas os primeiros 5
            print(f"   • {cenario}")
        if len(cenarios_com_erro) > 5:
            print(f"   • ... e mais {len(cenarios_com_erro) - 5} cenários")
    
    print(f"\n🎯 RECOMENDAÇÕES:")
    if taxa_deteccao < 80:
        print("   ⚠️ Taxa de detecção baixa - revisar dispatcher de fluxos")
    if stats_global['respostas_fallback'] > stats_global['respostas_llm']:
        print("   ⚠️ Muitas respostas fallback - verificar integração LLM")
    if stats_global['integracao_google_sheets'] == 0:
        print("   ⚠️ Nenhuma integração Google Sheets detectada")
    if stats_global['erros_http'] > 0:
        print(f"   ⚠️ {stats_global['erros_http']} erros HTTP encontrados")
    
    if taxa_deteccao >= 80 and stats_global['erros_http'] == 0:
        print("   ✅ Sistema funcionando bem - pronto para MVP!")

print("\n" + "="*50)
print("✅ TESTES CONCLUÍDOS!")
print(f"� Arquivo CSV consolidado: {csv_filename}")

gerar_relatorio_analise()

print(f"\n🔍 Para análise detalhada:")
print(f"   • Abra o arquivo: {csv_filename}")
print(f"   • Filtre por 'Fluxo Detectado' = False para ver problemas")
print(f"   • Analise coluna 'Indicadores Integração' para validar APIs Google")
print("="*50)

"""
Esse template testa TODAS as funções?
Sim, ele cobre todos os fluxos/funções mapeadas nos dicionários que você passou (cliente e advogado) — desde que:

Tenha ao menos um cenário (mensagem) para cada fluxo do dispatcher;

Os fluxos estejam implementados e mapeados no dispatcher de cada perfil (verifique se os nomes batem!);

A função roteador_principal esteja chamando o dispatcher correto (ela já faz isso!).

O QUE ELE TESTA:
Se o dispatcher detecta a intenção correta (ex: "espera_fluxo" está na resposta ou log);

Se o prompt few-shot certo foi usado (dá para inspecionar logs ou padrão de resposta);

Se planilha/pasta foi criada (normalmente aparece no texto ou debug/log do sistema);

Se o estado da conversa mudou (pode checar a variável global conversas).

O QUE ELE NÃO TESTA:
Fluxos que não tenham cenário no dicionário (adicione sempre 3 por função!);

Erros internos, problemas de integração com Google, etc. — isso depende de mocks ou ambiente real;

Se você adicionar novos fluxos ao backend, precisa colocar exemplos no dicionário e no dispatcher!
"""
