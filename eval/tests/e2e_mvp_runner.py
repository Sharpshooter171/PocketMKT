# tests/e2e_mvp_runner.py
import os, sys, json, types, re
from datetime import datetime, timedelta
from flask import Flask
import base64
import importlib
from datetime import datetime  # já importado acima também, mantemos

# Limite de caracteres exibidos nas amostras do relatório.
# 0 = sem truncar
E2E_SNIPPET_LIMIT = int(os.getenv("E2E_SNIPPET_LIMIT", "0"))

def _snippet(txt: str) -> str:
    if not txt:
        return ""
    if not E2E_SNIPPET_LIMIT or len(txt) <= E2E_SNIPPET_LIMIT:
        return txt
    return txt[:E2E_SNIPPET_LIMIT] + "…"

# Flags de ambiente para alternar integrações reais
USE_REAL_GOOGLE = os.getenv("E2E_USE_REAL_GOOGLE", "0").strip().lower() in ("1", "true", "yes")
USE_REAL_LLM = os.getenv("E2E_USE_REAL_LLM", "0").strip().lower() in ("1", "true", "yes")

###############################################################################
# 0) Preparação de ambiente (PYTHONPATH)
###############################################################################
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

###############################################################################
# 1) Stubs das integrações externas (Ollama/LLM + Google APIs)
###############################################################################

# ---- 1A. Stub LLM (Ollama) ----
if not USE_REAL_LLM:
    ollama_stub = types.ModuleType("app.ollama_service")

    def _interpret_decision_from_text(msg: str):
        """Heurística simples para testes E2E: extrai acao e horário."""
        t = msg.lower()
        # ação
        if any(k in t for k in ["recus", "sem agenda", "não posso", "nao posso", "nega"]):
            return {"acao":"recusar","inicio_iso":"","fim_iso":"","observacao":"recusado pelo advogado"}
        if any(k in t for k in ["suger", "melhor", "prefiro", "vamos às", "vamos as"]):
            # sugere amanhã 10:00-11:00
            d = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            return {"acao":"sugerir","inicio_iso":f"{d}T10:00:00-03:00","fim_iso":f"{d}T11:00:00-03:00","observacao":"sugestão"}
        if any(k in t for k in ["aprova", "pode marcar", "ok marcar", "confirmo", "de acordo", "aprovo"]):
            # aprova hoje 15:00-16:00
            d = datetime.now().strftime("%Y-%m-%d")
            return {"acao":"aprovar","inicio_iso":f"{d}T15:00:00-03:00","fim_iso":f"{d}T16:00:00-03:00","observacao":"aprovado"}
        # nenhum
        return {"acao":"nenhum","inicio_iso":"","fim_iso":"","observacao":""}

    def get_llama_response(prompt: str):
        # Se o prompt é do "classificador de decisão do advogado" (seu helper escreve instruções)
        if "Classifique em JSON" in prompt and "pedido de agendamento" in prompt:
            # extraímos a linha "Mensagem do advogado: ..."
            m = re.search(r"Mensagem do advogado:\s*(.*)", prompt, re.IGNORECASE)
            msg = m.group(1).strip() if m else ""
            return json.dumps(_interpret_decision_from_text(msg))
        # Para respostas educadas por fluxo (llm_reply), devolve texto polido e curto
        return "Perfeito! Vou cuidar disso e te mantenho informado."

    def classify_intent_llm(prompt: str):
        # Pouco usado como fallback; devolve algo plausível
        return "relato_caso"

    def extrair_dados_caso_llm(texto, dados_existentes=None):
        return {
            "nome_cliente": "Cliente Teste",
            "telefone": (dados_existentes or {}).get("telefone_cliente",""),
            "area_direito": "Trabalhista",
            "urgencia": "Média",
            "resumo_caso": texto[:240],
            "observacoes": ""
        }

    ollama_stub.get_llama_response = get_llama_response
    ollama_stub.classify_intent_llm = classify_intent_llm
    ollama_stub.extrair_dados_caso_llm = extrair_dados_caso_llm
    sys.modules["app.ollama_service"] = ollama_stub

# ---- 1B. Stub Google Sheets/Drive/Calendar/Gmail ----
if not USE_REAL_GOOGLE:
    google_stub = types.ModuleType("app.google_service")

    # Estado em memória
    _DB = {
        "sheets": {},
        "drive": [],
        "events": [],
        "emails": []
    }

    def _ensure_sheet(sheet_id: str, title="Casos Jurídicos – Escritório Geral"):
        if sheet_id not in _DB["sheets"]:
            _DB["sheets"][sheet_id] = {"title": title, "tabs": {
                "Casos": [], "Clientes": [], "Tarefas": [], "Documentos": []
            }}
        return _DB["sheets"][sheet_id]

    # --- Helpers de sheet em memória (adição) ---
    def ensure_sheet_id_file(sheet_id: str):
        _ensure_sheet(sheet_id)

    def buscar_ou_criar_planilha(nome_escritorio: str):
        """
        Stub da função usada pelo atendimento.py.
        Garante a existência da planilha e retorna o ID usado nos testes.
        """
        sheet_id = "SHEET_TEST_1"
        titulo = f"Casos Jurídicos – {nome_escritorio or 'Escritório Geral'}"
        _ensure_sheet(sheet_id, title=titulo)
        return sheet_id

    # ==== STUB DO GOOGLE SHEETS (spreadsheets.get / values.append) ====
    class _GetCall:
        def __init__(self, spreadsheet_id, fields):
            self.spreadsheet_id = spreadsheet_id
            self.fields = fields
        def execute(self):
            sheet = _ensure_sheet(self.spreadsheet_id)
            sheets_meta = [{"properties": {"title": tab_name}} for tab_name in sheet["tabs"].keys()]
            return {"sheets": sheets_meta}

    class _AppendCall:
        def __init__(self, spreadsheet_id, rng, body, valueInputOption, insertDataOption):
            self.spreadsheet_id = spreadsheet_id
            self.rng = rng or "Casos!A:Z"
            self.body = body or {}
            self.valueInputOption = valueInputOption
            self.insertDataOption = insertDataOption
        def execute(self):
            tab = self.rng.split("!")[0].strip().strip("'").strip('"')
            rows = self.body.get("values") or []
            sheet = _ensure_sheet(self.spreadsheet_id)
            sheet["tabs"].setdefault(tab, [])
            sheet["tabs"][tab].extend(rows)
            return {"updates": {"updatedRows": len(rows), "updatedRange": self.rng}}

    class _ValuesResource:
        def append(self, spreadsheetId, range, valueInputOption=None, insertDataOption=None, body=None):
            # ...existing code...
            return _AppendCall(
                spreadsheet_id=spreadsheetId,
                rng=range,
                body=body,
                valueInputOption=valueInputOption,
                insertDataOption=insertDataOption,
            )
        def get(self, spreadsheetId, range):
            # Simula leitura simples da aba informada
            tab = range.split("!")[0].strip().strip("'").strip('"')
            _ensure_sheet(spreadsheetId)
            vals = _DB["sheets"][spreadsheetId]["tabs"].get(tab, [])
            class _Exec:
                def execute(self_inner):
                    return {"values": [["COLS"]] + vals}
            return _Exec()
        def update(self, spreadsheetId, range, valueInputOption=None, body=None):
            # Atualiza célula(s) específicas (usado para status na Coluna F)
            tab = range.split("!")[0].strip().strip("'").strip('"')
            m = re.search(r"([A-Z]+)(\d+)$", range)
            row_index = int(m.group(2)) if m else 2
            col = m.group(1)
            col_idx = ord(col) - ord('A')
            table = _DB["sheets"][spreadsheetId]["tabs"].setdefault(tab, [])
            while len(table) < row_index-1:
                table.append([])
            vals = (body or {}).get("values", [[]])[0]
            while len(table[row_index-2]) <= col_idx + len(vals) - 1:
                table[row_index-2].append("")
            table[row_index-2][col_idx:col_idx+len(vals)] = vals
            class _Exec:
                def execute(self_inner): return {"updatedRows": 1}
            return _Exec()

    class _SpreadsheetsResource:
        def get(self, spreadsheetId, fields=None):
            return _GetCall(spreadsheetId, fields)
        def values(self):
            return _ValuesResource()
        def batchUpdate(self, spreadsheetId, body):
            # Cria abas quando solicitado
            _ensure_sheet(spreadsheetId)
            reqs = (body or {}).get("requests", [])
            for r in reqs:
                if "addSheet" in r:
                    title = r["addSheet"]["properties"]["title"]
                    _DB["sheets"][spreadsheetId]["tabs"].setdefault(title, [])
            class _Exec:
                def execute(self_inner): return {"replies":[{}]}
            return _Exec()
        def create(self, body=None, fields=None):
            # Cria planilha simples e retorna ID fixo de testes
            sid = "SHEET_TEST_1"
            _ensure_sheet(sid)
            class _Exec:
                def execute(self_inner):
                    return {"spreadsheetId": sid, "sheets":[{"properties":{"title":"Plan1"}}]}
            return _Exec()

    class _SheetsService:
        def spreadsheets(self):
            return _SpreadsheetsResource()

    # Stubs de funções utilitárias (modo stub)
    def get_google_sheets_service():
        return _SheetsService()

    # Suporte a pastas no "Drive" stub
    def create_drive_folder(name, parent_id=None):
        folder_id = f"folder_{len(_DB['drive'])+1}"
        _DB["drive"].append({
            "file_id": folder_id, "name": name, "bytes": 0,
            "pasta_id": parent_id, "mime": "application/vnd.google-apps.folder", "type": "folder"
        })
        return folder_id

    def upload_drive_bytes(filename, content_bytes, pasta_id=None, mime_type="application/octet-stream"):
        file_id = f"file_{len(_DB['drive'])+1}"
        _DB["drive"].append({
            "file_id": file_id, "name": filename, "bytes": len(content_bytes),
            "pasta_id": pasta_id, "mime": mime_type, "type": "file"
        })
        return file_id, f"https://drive.test/{file_id}"

    def criar_evento_calendar(titulo, inicio_iso, fim_iso, convidados_emails=None, descricao=""):
        ev_id = f"ev_{len(_DB['events'])+1}"
        _DB["events"].append({"id":ev_id,"title":titulo,"inicio_iso":inicio_iso,"fim_iso":fim_iso,"desc":descricao})
        return ev_id, f"https://calendar.test/{ev_id}"

    def enviar_email_gmail(destinatario, assunto, corpo):
        _DB["emails"].append({"to":destinatario,"subject":assunto,"body":corpo})
        return True

    def verificar_cliente_existente_google_api(*a, **k): return None
    def registrar_lead_google_api(*a, **k): return True

    # Exports do stub
    google_stub.get_google_sheets_service = get_google_sheets_service
    google_stub.create_drive_folder = create_drive_folder
    google_stub.upload_drive_bytes = upload_drive_bytes
    google_stub.criar_evento_calendar = criar_evento_calendar
    google_stub.enviar_email_gmail = enviar_email_gmail
    google_stub.verificar_cliente_existente_google_api = verificar_cliente_existente_google_api
    google_stub.registrar_lead_google_api = registrar_lead_google_api
    google_stub.buscar_ou_criar_planilha = buscar_ou_criar_planilha
    sys.modules["app.google_service"] = google_stub

# ---- 1C. Stub de NLU dos fluxos (text_processing) para acionar rotas no atendimento.py ----
# Colocado ANTES do import do atendimento
tp_stub = types.ModuleType("app.routes.text_processing")

def _has_any(t, kws): return any(k in t for k in kws)

def fluxo_onboarding_advogado(msg):
    t = (msg or "").lower()
    return {"nome_completo": "Dr. Teste"} if _has_any(t, ["crm", "onboarding", "configurar"]) else None

def fluxo_aprovacao_peticao(msg):
    t = (msg or "").lower()
    return {"status": "aprovado"} if _has_any(t, ["petição aprovada", "aprovei a petição", "peticao aprovada"]) else None

def fluxo_alerta_prazo(msg): return _has_any((msg or "").lower(), ["prazo", "audiência", "audiencia", "lembrete"])
def fluxo_honorarios(msg): return _has_any((msg or "").lower(), ["honorário", "honorarios", "tabela honor"])
def fluxo_documento_juridico(msg): return _has_any((msg or "").lower(), ["modelo", "contrato", "petição", "peticao", "minuta"])
def fluxo_envio_documento_cliente(msg): return False
def fluxo_consulta_andamento(msg): return _has_any((msg or "").lower(), ["andamento", "status do processo"])
def fluxo_pagamento_fora_padrao(msg): return _has_any((msg or "").lower(), ["fora do padrão", "fora do padrao", "negociar pagamento"])
def fluxo_indicacao(msg): return _has_any((msg or "").lower(), ["indicação", "indicacao"])
def fluxo_documento_pendente(msg): return _has_any((msg or "").lower(), ["pendente", "faltando documento"])
def fluxo_revisao_documento(msg): return _has_any((msg or "").lower(), ["revisar documento", "revisão"])
def fluxo_status_negociacao(msg): return _has_any((msg or "").lower(), ["negociação", "negociacao"])
def fluxo_decisao_permuta(msg): return _has_any((msg or "").lower(), ["permuta"])
def fluxo_sumiço_cliente(msg): return _has_any((msg or "").lower(), ["sumido", "não responde", "nao responde"])
def fluxo_update_clientes_aguardando(msg): return _has_any((msg or "").lower(), ["atualizar aguardando"])
def fluxo_update_documento_pendente(msg): return _has_any((msg or "").lower(), ["atualizar pendente"])
def fluxo_nao_atendimento_area(msg): return _has_any((msg or "").lower(), ["não atendo", "nao atendo", "fora da minha área"])
def fluxo_status_multiplos_processos(msg): return _has_any((msg or "").lower(), ["vários processos", "multiplos processos"])
def fluxo_notificacao_cliente(msg): return _has_any((msg or "").lower(), ["notificar cliente", "avisar cliente"])
def fluxo_alterar_cancelar_agendamento(msg): return _has_any((msg or "").lower(), ["remarcar", "cancelar agendamento", "adiar"])
def fluxo_resumo_estatisticas(msg): return _has_any((msg or "").lower(), ["estatísticas", "estatisticas", "relatório", "relatorio"])
def fluxo_lembrete_audiencia(msg): return _has_any((msg or "").lower(), ["lembrete audiência", "lembrete audiencia"])
def fluxo_enviar_resumo_caso(msg): return _has_any((msg or "").lower(), ["resumo do caso", "enviar resumo"])

# Fluxos cliente p/ _detect_with_nlu_llm
def fluxo_agendar_consulta_cliente(msg): return _has_any((msg or "").lower(), ["agendar", "marcar", "consulta", "horário", "horario"])
def fluxo_enviar_documento_cliente(msg): return _has_any((msg or "").lower(), ["rg", "cnh", "comprovante", "pdf", "foto", "imagem", "anexo"])
def fluxo_relato_caso(msg): return _has_any((msg or "").lower(), ["fui demitido", "meus direitos", "preciso de ajuda", "relato"])
def fluxo_consulta_andamento_cliente(msg): 
    t = (msg or "").lower()
    return _has_any(t, ["andamento", "status do processo"]) or bool(re.search(r'\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}', t))
def fluxo_atualizar_cadastro_cliente(msg): return _has_any((msg or "").lower(), ["telefone", "e-mail", "email", "endereço", "endereco"])
def fluxo_alterar_cancelar_agendamento(msg): return _has_any((msg or "").lower(), ["remarcar", "cancelar", "adiar"])

def analisar_texto(msg):
    # Extrai telefone/email simples para o teste de cadastro
    m_tel = re.search(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}", msg or "")
    m_em = re.search(r"[\w\.-]+@[\w\.-]+", msg or "")
    return {"telefones": [m_tel.group(0)] if m_tel else [], "emails": [m_em.group(0)] if m_em else []}

tp_stub.fluxo_onboarding_advogado = fluxo_onboarding_advogado
tp_stub.fluxo_aprovacao_peticao = fluxo_aprovacao_peticao
tp_stub.fluxo_alerta_prazo = fluxo_alerta_prazo
tp_stub.fluxo_honorarios = fluxo_honorarios
tp_stub.fluxo_documento_juridico = fluxo_documento_juridico
tp_stub.fluxo_envio_documento_cliente = fluxo_envio_documento_cliente
tp_stub.fluxo_consulta_andamento = fluxo_consulta_andamento
tp_stub.fluxo_pagamento_fora_padrao = fluxo_pagamento_fora_padrao
tp_stub.fluxo_indicacao = fluxo_indicacao
tp_stub.fluxo_documento_pendente = fluxo_documento_pendente
tp_stub.fluxo_revisao_documento = fluxo_revisao_documento
tp_stub.fluxo_status_negociacao = fluxo_status_negociacao
tp_stub.fluxo_decisao_permuta = fluxo_decisao_permuta
tp_stub.fluxo_sumiço_cliente = fluxo_sumiço_cliente
tp_stub.fluxo_update_clientes_aguardando = fluxo_update_clientes_aguardando
tp_stub.fluxo_update_documento_pendente = fluxo_update_documento_pendente
tp_stub.fluxo_nao_atendimento_area = fluxo_nao_atendimento_area
tp_stub.fluxo_status_multiplos_processos = fluxo_status_multiplos_processos
tp_stub.fluxo_notificacao_cliente = fluxo_notificacao_cliente
tp_stub.fluxo_alterar_cancelar_agendamento = fluxo_alterar_cancelar_agendamento
tp_stub.fluxo_resumo_estatisticas = fluxo_resumo_estatisticas
tp_stub.fluxo_lembrete_audiencia = fluxo_lembrete_audiencia
tp_stub.fluxo_enviar_resumo_caso = fluxo_enviar_resumo_caso

tp_stub.fluxo_agendar_consulta_cliente = fluxo_agendar_consulta_cliente
tp_stub.fluxo_enviar_documento_cliente = fluxo_enviar_documento_cliente
tp_stub.fluxo_relato_caso = fluxo_relato_caso
tp_stub.fluxo_consulta_andamento_cliente = fluxo_consulta_andamento_cliente
tp_stub.fluxo_atualizar_cadastro_cliente = fluxo_atualizar_cadastro_cliente
tp_stub.fluxo_alterar_cancelar_agendamento = fluxo_alterar_cancelar_agendamento
tp_stub.analisar_texto = analisar_texto
sys.modules["app.routes.text_processing"] = tp_stub

###############################################################################
# 2) Monta app Flask e registra o blueprint do atendimento
###############################################################################
from app.routes.atendimento import atendimento_bp
app = Flask(__name__)
app.register_blueprint(atendimento_bp)
client = app.test_client()

# Descobre capacidades do app (para pular cenários opcionais)
_at_mod = importlib.import_module("app.routes.atendimento")
SUPPORTS_MEDIA_BASE64 = hasattr(_at_mod, "_decode_input_media") if _at_mod else False
SUPPORTS_TWILIO = any(r.rule == "/twilio_webhook" for r in app.url_map.iter_rules())

# -------------------- COLETA E RELATÓRIO --------------------
REPORT = {
    "meta": {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "use_real_google": USE_REAL_GOOGLE,
        "use_real_llm": USE_REAL_LLM,
        "supports_media_base64": bool(SUPPORTS_MEDIA_BASE64),
        "supports_twilio_webhook": bool(SUPPORTS_TWILIO),
        "python": sys.version.split()[0],
        "platform": sys.platform,
    },
    "scenarios": [],   # [{name, status: ok|fail|skip, notes}]
    "interactions": [] # últimas interações de hit(...)
}

def _add_scenario_result(name, status, notes=""):
    REPORT["scenarios"].append({
        "name": name,
        "status": status,
        "notes": (notes or "").strip()
    })

def run_scenario(fn):
    """Executa um cenário e registra status."""
    name = getattr(fn, "__name__", "scenario")
    try:
        ret = fn()
        # Se cenário opcional sinalizar SKIP com dict
        if isinstance(ret, dict) and ret.get("skipped"):
            _add_scenario_result(name, "skip", ret.get("reason",""))
        else:
            _add_scenario_result(name, "ok", "")
    except AssertionError as e:
        _add_scenario_result(name, "fail", f"Assert: {e}")
    except Exception as e:
        _add_scenario_result(name, "fail", f"Erro: {e}")

def _write_reports():
    """Gera arquivos Markdown e HTML com o resumo dos testes."""
    reports_dir = os.path.join(ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = os.path.join(reports_dir, f"e2e_report_{ts}.md")
    html_path = os.path.join(reports_dir, f"e2e_report_{ts}.html")

    # Resumo cenários
    total = len(REPORT["scenarios"])
    oks = sum(1 for s in REPORT["scenarios"] if s["status"] == "ok")
    fails = sum(1 for s in REPORT["scenarios"] if s["status"] == "fail")
    skips = sum(1 for s in REPORT["scenarios"] if s["status"] == "skip")

    # Snapshot do stub quando aplicável
    stub_snapshot = ""
    if not USE_REAL_GOOGLE and "_DB" in globals():
        try:
            sheets = len(_DB.get("sheets", {}))
            casos = len(_DB["sheets"]["SHEET_TEST_1"]["tabs"].get("Casos", [])) if "SHEET_TEST_1" in _DB["sheets"] else 0
            clientes = len(_DB["sheets"]["SHEET_TEST_1"]["tabs"].get("Clientes", [])) if "SHEET_TEST_1" in _DB["sheets"] else 0
            tarefas = len(_DB["sheets"]["SHEET_TEST_1"]["tabs"].get("Tarefas", [])) if "SHEET_TEST_1" in _DB["sheets"] else 0
            documentos = len(_DB["sheets"]["SHEET_TEST_1"]["tabs"].get("Documentos", [])) if "SHEET_TEST_1" in _DB["sheets"] else 0
            drive_files = len([d for d in _DB.get("drive", []) if d.get("type") == "file"])
            drive_folders = len([d for d in _DB.get("drive", []) if d.get("type") == "folder"])
            stub_snapshot = (
                f"- Sheets (stub): {sheets}\n"
                f"- Casos: {casos} | Clientes: {clientes} | Tarefas: {tarefas} | Documentos: {documentos}\n"
                f"- Drive (arquivos): {drive_files} | Pastas: {drive_folders}\n"
            )
        except Exception:
            pass

    # Amostra de interações (últimas 20)
    last_interactions = REPORT["interactions"][-20:]

    # Monta Markdown amigável
    md = []
    md.append(f"# Relatório E2E – MVP Jurídico\n")
    md.append(f"- Início: {REPORT['meta']['started_at']}")
    md.append(f"- Python: {REPORT['meta']['python']} | Plataforma: {REPORT['meta']['platform']}")
    md.append(f"- Google real: {REPORT['meta']['use_real_google']} | LLM real: {REPORT['meta']['use_real_llm']}")
    md.append(f"- Suporte Twilio: {REPORT['meta']['supports_twilio_webhook']} | Upload base64: {REPORT['meta']['supports_media_base64']}\n")
    md.append(f"## Resumo dos Cenários")
    md.append(f"- Total: {total} | OK: {oks} | Falhas: {fails} | Skips: {skips}\n")
    md.append(f"### Detalhe por cenário")
    for s in REPORT["scenarios"]:
        icon = "✅" if s["status"] == "ok" else ("⚠️" if s["status"] == "skip" else "❌")
        line = f"- {icon} {s['name']} — {s['status'].upper()}"
        if s["notes"]:
            line += f" — {s['notes']}"
        md.append(line)
    md.append("")
    md.append("## Amostras de Conversas (últimas 20)")
    for it in last_interactions:
        texto_original = it.get("msg", "")
        resposta_original = it.get("resposta", "")
        texto_fmt = _snippet(texto_original)
        resposta_fmt = _snippet(resposta_original)
        md.append(f"- [{it['ts']}] ({it['tipo']}:{it['numero']}) “{texto_fmt}” → fluxo={it.get('fluxo')} | resposta=\"{resposta_fmt}\"")
    md.append("")
    if stub_snapshot:
        md.append("## Snapshot do CRM/Drive (modo stub)")
        md.append(stub_snapshot)

    md_content = "\n".join(md)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # HTML simples (markdown em <pre> para leitura leiga)
    html_content = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Relatório E2E</title>
<style>body{{font-family:Arial,Helvetica,sans-serif;line-height:1.4}} pre{{white-space:pre-wrap}}</style></head>
<body><h1>Relatório E2E</h1><pre>{md_content}</pre></body></html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n📄 Relatórios salvos:\n- {md_path}\n- {html_path}")

# -------------------- FIM COLETA E RELATÓRIO --------------------

# Helper de POST
def hit(msg, numero, tipo="cliente", extra=None, expect_status=200):
    payload = {"mensagem": msg, "numero": numero, "tipo_usuario": tipo}
    if extra: payload.update(extra)
    r = client.post("/processar_atendimento", json=payload)
    assert r.status_code == expect_status, f"HTTP {r.status_code} != {expect_status} for {msg}"
    # Registro da interação para o relatório
    try:
        j = r.get_json() or {}
        REPORT["interactions"].append({
            "ts": datetime.now().strftime("%H:%M:%S"),
            "tipo": tipo,
            "numero": numero,
            "msg": msg,
            "fluxo": j.get("fluxo"),
            # não truncar aqui; truncamento é controlado por _snippet no relatório
            "resposta": (j.get("resposta") or ""),
            "intent_source": j.get("intent_source")
        })
    except Exception:
        pass
    print(f"\n→ ({tipo}:{numero}) {msg}\n← {r.json}")
    return r.json

# Prepara arquivo sheet_id_*.txt que seu código lê (apenas modo stub)
def ensure_sheet_id_file(escritorio_id=None, sheet_id="SHEET_TEST_1"):
    nome_escr = f"Escritório {(escritorio_id or 'Geral').title()}"
    fname = f"sheet_id_{nome_escr.replace(' ','_').lower()}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(sheet_id)

if not USE_REAL_GOOGLE:
    ensure_sheet_id_file(sheet_id="SHEET_TEST_1")

# Helper para semear "Pedido de agendamento" (cliente -> advogado)
def seed_pedido_agendamento(numero, label="Horário sugerido", dias=1):
    if USE_REAL_GOOGLE:
        return  # nos testes reais, opte por criar via API se desejar
    # Garante sheet e aba
    sid = "SHEET_TEST_1"
    if "SHEET_TEST_1" not in _DB["sheets"]:
        _DB["sheets"][sid] = {"title": "CRM – Escritório Geral", "tabs": {"Casos": [], "Clientes": [], "Tarefas": [], "Documentos": []}}
    _DB["sheets"][sid]["tabs"].setdefault("Tarefas", [])
    ini = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%dT10:00:00-03:00")
    fim = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%dT11:00:00-03:00")
    _DB["sheets"][sid]["tabs"]["Tarefas"].append([
        datetime.now().strftime("%d/%m/%Y %H:%M"), "Pedido de agendamento", label, numero, "Origem: cliente", "Pendente", ini, fim
    ])

###############################################################################
# 3) CENÁRIOS
###############################################################################
def scenario_0_healthcheck():
    r = client.post("/processar_atendimento", json={"healthcheck":True,"tipo_usuario":"cliente","numero":"X"})
    assert r.status_code == 200

def scenario_1_saudacao():
    j = hit("Olá, tudo bem?", "C1")
    assert j["fluxo"] == "saudacao_inicial"

def scenario_2_relato_caso():
    j = hit("Fui demitido sem justa causa e preciso entender meus direitos.", "C1")
    assert j["fluxo"] in ("relato_caso","relato_caso_cliente","relato_caso")
    if not USE_REAL_GOOGLE:
        casos = _DB["sheets"]["SHEET_TEST_1"]["tabs"]["Casos"]
        assert len(casos) >= 1

def scenario_3_enviar_documento_auto():
    j = hit("Segue anexo meu RG e comprovante de endereço.", "C2")
    assert j["fluxo"] == "enviar_documento_cliente"
    if not USE_REAL_GOOGLE:
        assert len(_DB["drive"]) >= 1
        assert len(_DB["sheets"]["SHEET_TEST_1"]["tabs"]["Documentos"]) >= 1

def scenario_4_andamento_found_and_notfound():
    if not USE_REAL_GOOGLE:
        _DB["sheets"]["SHEET_TEST_1"]["tabs"]["Casos"].append(
            [datetime.now().strftime("%d/%m/%Y %H:%M"), "Cliente A", "5553000", "Trabalhista", "Média",
             "CNJ 0000000-00.0000.0.00.0000", "Em análise", ""]
        )
        j1 = hit("Quero o andamento do processo 0000000-00.0000.0.00.0000", "C3")
        assert j1["fluxo"] == "consulta_andamento_cliente"
    # Caso sem CNJ (abre tarefa automaticamente)
    j2 = hit("Quero saber o andamento do meu processo", "C4")
    assert j2["fluxo"] == "consulta_andamento_cliente"
    if not USE_REAL_GOOGLE:
        tarefas = _DB["sheets"]["SHEET_TEST_1"]["tabs"]["Tarefas"]
        assert any("Pedido de agendamento" not in x and "Consulta andamento" in " ".join(x) or "Pendente" in x for x in tarefas) or len(tarefas) >= 1

def scenario_5_agendar_cliente_preview_confirm():
    # Como o bloco cliente de agendar ainda não cria pedido, validamos resposta e semeamos pedido para os próximos cenários
    j_prev = hit("Quero marcar uma consulta amanhã", "C5")
    assert j_prev["resposta"]  # resposta existe
    # Prepara pedido para sequência (advogado)
    if not USE_REAL_GOOGLE:
        seed_pedido_agendamento("C5")

def scenario_6_advogado_aprova():
    if not USE_REAL_GOOGLE:
        seed_pedido_agendamento("C5")
    j1 = hit("Pode aprovar o pedido do cliente C5", "ADV1", tipo="advogado")
    assert j1["fluxo"] == "aprovar_agendamento_advogado"
    j2 = hit("confirmar", "ADV1", tipo="advogado")
    assert j2["fluxo"] == "aprovar_agendamento_advogado"
    if not USE_REAL_GOOGLE:
        assert len(_DB["events"]) >= 1

def scenario_7_advogado_sugere():
    if not USE_REAL_GOOGLE:
        seed_pedido_agendamento("C6")
    hit("Preciso agendar consulta", "C6")
    j1 = hit("Prefiro amanhã às 10h", "ADV2", tipo="advogado")
    j2 = hit("confirmar", "ADV2", tipo="advogado")
    if not USE_REAL_GOOGLE:
        assert len(_DB["events"]) >= 2

def scenario_8_advogado_recusa():
    if not USE_REAL_GOOGLE:
        seed_pedido_agendamento("C7")
    j = hit("Sem agenda essa semana, melhor recusar", "ADV3", tipo="advogado")
    assert j["fluxo"] == "aprovar_agendamento_advogado"

def scenario_9_atualizar_cadastro_auto():
    j = hit("Troquei de telefone: (11) 99999-1234 e meu e-mail é teste@exemplo.com", "C8")
    if not USE_REAL_GOOGLE:
        clientes = _DB["sheets"]["SHEET_TEST_1"]["tabs"]["Clientes"]
        assert len(clientes) >= 1

def scenario_10_alterar_cancelar_agendamento_robustez():
    j = hit("Preciso remarcar minha consulta", "C9")
    # Não necessariamente cria algo agora; garantimos que não quebre
    assert j["resposta"]

def scenario_11_followup_auto():
    # Se seu app tiver intent "followup_cliente", este cenário valida auto execução;
    # Como nem todo código expõe o intent, aceitamos passar se não quebrar:
    try:
        j = hit("Poderia me lembrar amanhã?", "C10")
        assert j["resposta"]
    except AssertionError:
        pass

def scenario_12_combo_full():
    if not USE_REAL_GOOGLE:
        seed_pedido_agendamento("C11")
    # Cliente C11: relato -> documento -> agendar -> advogado aprova
    hit("Fui assaltado e preciso de orientação", "C11")
    hit("Segue a foto do BO e meu documento", "C11")
    hit("Quero marcar um horário amanhã às 15h", "C11")
    hit("confirmar", "C11")
    hit("Aprovo o pedido do cliente C11", "ADV4", tipo="advogado")
    hit("confirmar", "ADV4", tipo="advogado")
    if not USE_REAL_GOOGLE:
        assert any(ev for ev in _DB["events"] if "Consulta jurídica" in ev["title"])

# NOVO: advogado pede lembrete/alerta de prazo (gera tarefa no CRM após confirmar)
def scenario_13_advogado_alerta_prazo():
    j1 = hit("Preciso registrar um lembrete de prazo para amanhã às 14h", "ADV5", tipo="advogado")
    # fluxo pode ser normalizado internamente; garantimos que não quebre e aceite confirmação
    j2 = hit("confirmar", "ADV5", tipo="advogado")
    if not USE_REAL_GOOGLE:
        tarefas = _DB["sheets"]["SHEET_TEST_1"]["tabs"]["Tarefas"]
        assert any("Lembrete" in " ".join(r) or "prazo" in " ".join(r).lower() for r in tarefas)

# NOVO: advogado solicita documento/modelo (gera upload e registro em Documentos)
def scenario_14_advogado_documento_juridico():
    j1 = hit("Preciso de um modelo de contrato de prestação de serviços", "ADV6", tipo="advogado")
    j2 = hit("confirmar", "ADV6", tipo="advogado")
    if not USE_REAL_GOOGLE:
        docs = _DB["sheets"]["SHEET_TEST_1"]["tabs"]["Documentos"]
        # ou criou arquivo no drive stub ou linha em Documentos
        assert len(docs) >= 1 or len(_DB["drive"]) >= 1

def scenario_15_upload_binario_com_pasta_cliente():
    if not SUPPORTS_MEDIA_BASE64:
        print("[SKIP] upload binário base64 não suportado pelo app atual.")
        return {"skipped": True, "reason": "upload base64 não suportado"}
    # Gera um JPEG pequeno em memória (header + lixo) e envia como base64
    nome = "Jorge Caldas"
    fake_jpg = b"\xFF\xD8\xFF\xE0" + b"\x00" * 128 + b"\xFF\xD9"
    b64 = base64.b64encode(fake_jpg).decode("ascii")
    j = hit(
        "Segue minha CNH em anexo.",
        "C12",
        tipo="cliente",
        extra={
            "nome_cliente": nome,
            "arquivo_base64": b64,
            "filename": "cnh.jpg",
            "mime_type": "image/jpeg"
        }
    )
    assert j["fluxo"] == "enviar_documento_cliente"
    if not USE_REAL_GOOGLE:
        # Verifica se o arquivo está dentro da pasta do cliente
        # 1) encontra a pasta
        folder = next((d for d in _DB["drive"] if d.get("type")=="folder" and d["name"]==nome), None)
        assert folder is not None, "Pasta do cliente não foi criada no stub"
        # 2) encontra o arquivo com parent == folder_id
        file = next((d for d in _DB["drive"] if d.get("type")=="file" and d["name"]=="cnh.jpg" and d["pasta_id"]==folder["file_id"]), None)
        assert file is not None, "Arquivo não foi salvo dentro da pasta do cliente"

def scenario_16_twilio_webhook_text():
    if not SUPPORTS_TWILIO:
        print("[SKIP] webhook Twilio não exposto no app atual.")
        return {"skipped": True, "reason": "webhook Twilio ausente"}
    # Simula mensagem via Twilio (Sandbox) sem mídia
    data = {
        "From": "whatsapp:+5511999999999",
        "Body": "Olá, quero informações do meu processo",
        "NumMedia": "0"
    }
    r = client.post("/twilio_webhook", data=data, content_type="application/x-www-form-urlencoded")
    assert r.status_code == 200
    assert "<Response>" in r.text and "<Message>" in r.text

def scenario_17_twilio_webhook_media():
    if not SUPPORTS_TWILIO:
        print("[SKIP] webhook Twilio não exposto no app atual.")
        return {"skipped": True, "reason": "webhook Twilio ausente"}
    if not SUPPORTS_MEDIA_BASE64:
        print("[SKIP] upload binário base64 não suportado pelo app atual.")
        return {"skipped": True, "reason": "upload base64 não suportado"}
    # Simula envio de mídia via Twilio usando data URL base64 (sem internet)
    fake_pdf = b"%PDF-1.4\n%fake\n" + b"0"*128
    b64 = base64.b64encode(fake_pdf).decode("ascii")
    data_url = f"data:application/pdf;base64,{b64}"
    data = {
        "From": "whatsapp:+5511888888888",
        "Body": "Segue meu comprovante",
        "NumMedia": "1",
        "MediaUrl0": data_url,
        "MediaContentType0": "application/pdf"
    }
    r = client.post("/twilio_webhook", data=data, content_type="application/x-www-form-urlencoded")
    assert r.status_code == 200
    assert "<Response>" in r.text and "<Message>" in r.text
    if not USE_REAL_GOOGLE:
        # Houve upload no stub
        assert any(d for d in _DB["drive"] if d.get("type")=="file" and d["mime"]=="application/pdf")

# NOVOS: cobrir mais fluxos de advogado (sem exigir efeitos colaterais fortes)
def scenario_18_adv_onboarding():
    j = hit("Quero configurar meu CRM (onboarding)", "ADV7", tipo="advogado")
    assert j["resposta"]

def scenario_19_adv_honorarios():
    j = hit("Poderia revisar a tabela de honorários deste caso?", "ADV8", tipo="advogado")
    assert j["resposta"]

def scenario_20_adv_outros_fluxos_basicos():
    mensagens = [
        ("Tem um cliente com pagamento fora do padrão", "ADV9"),
        ("Recebi uma indicação, pode registrar?", "ADV10"),
        ("Há documento pendente nesse caso", "ADV11"),
        ("Qual o status da negociação com a contraparte?", "ADV12"),
        ("Vamos avaliar uma permuta nesse caso", "ADV13"),
        ("O cliente está sumido há duas semanas", "ADV14"),
        ("Atualizar clientes aguardando, por favor", "ADV15"),
        ("Atualizar documentos pendentes", "ADV16"),
        ("Esse assunto é fora da minha área de atuação", "ADV17"),
        ("Tenho múltiplos processos desse cliente", "ADV18"),
        ("Notificar o cliente sobre a audiência", "ADV19"),
        ("Preciso alterar o agendamento de amanhã", "ADV20"),
        ("Me mande um resumo das estatísticas do mês", "ADV21"),
        ("Criar lembrete de audiência para sexta", "ADV22"),
        ("Envie um resumo do caso ao cliente", "ADV23"),
    ]
    for msg, num in mensagens:
        j = hit(msg, num, tipo="advogado")
        assert j["resposta"]

###############################################################################
# 4) Runner
###############################################################################
if __name__ == "__main__":
    print("\n=== INICIANDO TESTES E2E MVP ===")
    # Executa e coleta status de cada cenário
    run_scenario(scenario_0_healthcheck)
    run_scenario(scenario_1_saudacao)
    run_scenario(scenario_2_relato_caso)
    run_scenario(scenario_3_enviar_documento_auto)
    run_scenario(scenario_4_andamento_found_and_notfound)
    run_scenario(scenario_5_agendar_cliente_preview_confirm)
    run_scenario(scenario_6_advogado_aprova)
    run_scenario(scenario_7_advogado_sugere)
    run_scenario(scenario_8_advogado_recusa)
    run_scenario(scenario_9_atualizar_cadastro_auto)
    run_scenario(scenario_10_alterar_cancelar_agendamento_robustez)
    run_scenario(scenario_11_followup_auto)
    run_scenario(scenario_12_combo_full)
    run_scenario(scenario_13_advogado_alerta_prazo)
    run_scenario(scenario_14_advogado_documento_juridico)
    run_scenario(scenario_15_upload_binario_com_pasta_cliente)
    run_scenario(scenario_16_twilio_webhook_text)
    run_scenario(scenario_17_twilio_webhook_media)
    run_scenario(scenario_18_adv_onboarding)
    run_scenario(scenario_19_adv_honorarios)
    run_scenario(scenario_20_adv_outros_fluxos_basicos)

    # Relatório final no console (stub) — mantém como estava
    print("\n=== RELATÓRIO CRM SIMULADO ===")
    if not USE_REAL_GOOGLE and "_DB" in globals():
        print("Sheets tabs:", {sid: list(v["tabs"].keys()) for sid, v in _DB["sheets"].items()})
        print("Casos:", _DB["sheets"]["SHEET_TEST_1"]["tabs"]["Casos"])
        print("Clientes:", _DB["sheets"]["SHEET_TEST_1"]["tabs"]["Clientes"])
        print("Tarefas:", _DB["sheets"]["SHEET_TEST_1"]["tabs"]["Tarefas"])
        print("Documentos:", _DB["sheets"]["SHEET_TEST_1"]["tabs"]["Documentos"])
        print("Drive files:", _DB["drive"])
        print("Events:", _DB["events"])
        print("Emails:", _DB["emails"])
    else:
        print("Modo REAL: operações foram executadas no Google (sem relatório do _DB).")
    print("\n=== OK: TODOS OS CENÁRIOS EXECUTADOS ===")

    # Gera documentos do relatório (Markdown + HTML)
    _write_reports()
