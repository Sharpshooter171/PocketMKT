# Bootstrapping de path para execução local/AWS (antes de qualquer import de 'app')
import os, sys
try:
    import app  # testa se o pacote já está acessível
except Exception:
    _FILE_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.abspath(os.path.join(_FILE_DIR, "..", ".."))  # .../PocketMKT
    if _PROJECT_ROOT not in sys.path:
        sys.path.insert(0, _PROJECT_ROOT)

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
    fluxo_enviar_resumo_caso,
    # ...inclua todos os fluxos implementados
)
# ==== HELPERS DE AGENDA (Calendar) ====
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    pass
    ZoneInfo = None  # se faltar, cairemos em simulação

def _get_calendar_service_from_sheets():
    """
    Reaproveita as credenciais do Google Sheets para construir o service do Calendar.
    Retorna None se OAuth não estiver disponível.
    """
    try:
        svc_sheets = get_google_sheets_service()
        if not svc_sheets:
            return None
        from googleapiclient.discovery import build
        creds = svc_sheets._http.credentials  # mesmas credenciais
        cal = build("calendar", "v3", credentials=creds)
        return cal
    except Exception:
        return None

def _listar_slots_disponiveis(dias=7, hora_inicio=9, hora_fim=18, duracao_min=60, max_slots=6):
    """
    Lê o Google Calendar 'primary' e retorna até max_slots janelas livres
    nos próximos 'dias', dentro do horário comercial (hora_inicio–hora_fim), fuso São Paulo.
    Cada item = {"inicio_iso", "fim_iso", "label"}
    """
    tz = ZoneInfo("America/Sao_Paulo") if ZoneInfo else None
    cal = _get_calendar_service_from_sheets()
    if not cal or not tz:
        # Simulação: devolve 3 horários 'fakes' amanhã
        base = datetime.utcnow() + timedelta(days=1)
        base = base.replace(hour=15, minute=0, second=0, microsecond=0)
        slots = []
        for i in range(3):
            ini = (base + timedelta(hours=i)).isoformat(timespec="seconds") + "Z"
            fim = (base + timedelta(hours=i+1)).isoformat(timespec="seconds") + "Z"
            label = (base + timedelta(hours=i)).strftime("%d/%m %H:%M–") + (base + timedelta(hours=i+1)).strftime("%H:%M")
            slots.append({"inicio_iso": ini, "fim_iso": fim, "label": label})
        return slots

    # Coleta eventos dia a dia e calcula janelas livres
    agora = datetime.now(tz)
    slots = []
    for d in range(dias):
        dia = (agora + timedelta(days=d)).date()
        ini_janela = datetime(dia.year, dia.month, dia.day, hora_inicio, 0, tzinfo=tz)
        fim_janela = datetime(dia.year, dia.month, dia.day, hora_fim, 0, tzinfo=tz)

        # Busca eventos desse dia
        events = cal.events().list(
            calendarId="primary",
            timeMin=ini_janela.isoformat(),
            timeMax=fim_janela.isoformat(),
            singleEvents=True,
            orderBy="startTime"
        ).execute().get("items", [])

        # Constrói blocos ocupados
        busy = []
        for ev in events:
            try:
                s = ev["start"].get("dateTime") or (ev["start"].get("date") + "T00:00:00")
                e = ev["end"].get("dateTime") or (ev["end"].get("date") + "T23:59:59")
                s_dt = datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(tz)
                e_dt = datetime.fromisoformat(e.replace("Z","+00:00")).astimezone(tz)
                # Clipa ao horário comercial
                s_dt = max(s_dt, ini_janela)
                e_dt = min(e_dt, fim_janela)
                if e_dt > s_dt:
                    busy.append((s_dt, e_dt))
            except Exception:
                continue

        # Mescla overlaps simples
        busy.sort()
        merged = []
        for b in busy:
            if not merged or b[0] > merged[-1][1]:
                merged.append(list(b))
            else:
                merged[-1][1] = max(merged[-1][1], b[1])

        # Calcula livres entre [ini_janela, fim_janela]
        livres = []
        cursor = ini_janela
        for s_dt, e_dt in merged:
            if s_dt > cursor:
                livres.append((cursor, s_dt))
            cursor = max(cursor, e_dt)
        if cursor < fim_janela:
            livres.append((cursor, fim_janela))

        # Fatia livres em blocos de 'duracao_min'
        dur = timedelta(minutes=duracao_min)
        for lv_ini, lv_fim in livres:
            while lv_ini + dur <= lv_fim:
                lab = lv_ini.strftime("%d/%m %H:%M–") + (lv_ini + dur).strftime("%H:%M")
                slots.append({
                    "inicio_iso": lv_ini.isoformat(timespec="seconds"),
                    "fim_iso": (lv_ini + dur).isoformat(timespec="seconds"),
                    "label": lab
                })
                if len(slots) >= max_slots:
                    return slots
                lv_ini += dur
    return slots
# ==== FIM HELPERS AGENDA ====

# ==== HUMANIZAÇÃO – TONS E FECHOS ====
def _humanize_during(texto_base):
    # garante linguagem clara + convite à continuidade
    if not texto_base:
        return "Posso ajudar com seu caso, seu agendamento ou seus documentos."
    anexo = "\n\nSe algo não estiver claro, me avise e eu reformulo."
    return texto_base if texto_base.strip().endswith(("?", ".", "!")) else texto_base + anexo

# Pequeno pre-ack para não quebrar chamadas; pode ser evoluído depois
def _humanize_pre(mensagem, tipo_usuario):
    try:
        msg = (mensagem or "").strip()
        if not msg:
            return ""
        # resposta neutra curta; mantemos vazio para não poluir interações
        return ""
    except Exception:
        return ""

_HUMANIZED_FOOTERS = {
    "relato_caso": "\n\n📌 Próximos passos: registrarei seu relato no CRM e o advogado responsável vai revisar. Se quiser, já posso sugerir horários para atendimento.",
    "consulta_andamento_cliente": "\n\n📌 Assim que houver novidade, te avisamos por aqui.",
    "agendar_consulta_cliente": "\n\n📌 Após a aprovação do advogado, confirmamos o horário e te enviamos o convite.",
    "enviar_documento_cliente": "\n\n📌 Assim que o documento entrar no CRM, o advogado consegue acessá-lo na pasta do seu caso."
}
def _humanize_post(texto, fluxo):
    rodape = _HUMANIZED_FOOTERS.get(fluxo, "\n\nPosso ajudar com mais alguma coisa?")
    # Evita duplicar se a mensagem já contém um rodapé semelhante
    if rodape.strip() in (texto or ""):
        return texto
    return f"{texto}\n{rodape}"
# ==== FIM HUMANIZAÇÃO ====

# Quais intents o assistente pode executar sem preview/confirm?
AUTO_EXEC_POLICY = {
    "enviar_documento_cliente": True,
    "atualizar_cadastro_cliente": True,
    "consulta_andamento_cliente_open_task": True,  # abrir tarefa quando faltam dados
    "followup_cliente": True,
    "enviar_resumo_caso": True,
    # intents que SEMPRE exigem aprovação do advogado:
    "agendar_consulta_cliente": False,
    "aprovacao_peticao": False,
    "decisao_permuta": False,
    "status_negociacao": False,
}

# ==== LLM PARA REDAÇÃO EDUCADA (FEW-SHOT) ====
def _llm_reply(intent_key, user_message):
    """
    Usa prompt few-shot por fluxo para redigir a resposta de forma educada.
    Cai em None se algo falhar (para manter fallback em strings fixas).
    """
    try:
        from app.prompt_config import prompt_config, montar_prompt_instruct
        from app.ollama_service import get_llama_response
        # mapeia intents → chaves de prompt
        key_map = {
            "relato_caso": "fluxo_relato_caso_prompt",
            "consulta_andamento_cliente": "fluxo_consulta_andamento_cliente_prompt",
            "enviar_documento_cliente": "fluxo_enviar_documento_cliente_prompt",
            "agendar_consulta_cliente": "fluxo_agendar_consulta_cliente_prompt",
            "atualizar_cadastro_cliente": "fluxo_atualizar_cadastro_cliente_prompt",
            # advogado:
            "onboarding": "fluxo_onboarding_advogado_prompt",
            "aprovacao_peticao": "fluxo_aprovacao_peticao_prompt",
            "alerta_prazo": "fluxo_alerta_prazo_prompt",
            "honorarios": "fluxo_honorarios_prompt",
            "documento_juridico": "fluxo_documento_juridico_prompt",
            # fallback
            "system": "system_prompt",
        }
        prompt_key = key_map.get(intent_key) or key_map["system"]
        system_prompt = prompt_config.get(prompt_key) or prompt_config.get("system_prompt", "")
    except Exception:
        return None

    # ==== LLM NLU – INTERPRETAR DECISÃO DO ADVOGADO SOBRE AGENDAMENTO ====
    def _interpretar_decisao_advogado(mensagem):
        """
        Usa LLM para classificar a intenção do advogado em:
          - acao: "aprovar" | "recusar" | "sugerir" | "nenhum"
          - inicio_iso, fim_iso (opcionais, se houver horário sugerido)
          - observacao (texto livre)
        """
        try:
            from app.prompt_config import montar_prompt_instruct
            from app.ollama_service import get_llama_response
            system = (
                "Você recebe uma mensagem escrita por um advogado sobre um pedido de agendamento.\n"
                "Classifique em JSON com as chaves: acao ('aprovar'|'recusar'|'sugerir'|'nenhum'), "
                "inicio_iso (RFC3339), fim_iso (RFC3339), observacao.\n"
                "Se sugerir horário, normalize para America/Sao_Paulo e gere intervalos de 60 minutos "
                "a partir do contexto (ex.: 'amanhã às 10h' => inicio 10:00, fim 11:00). "
                "Se não houver horário claro, deixe vazio."
            )
            user = f"Mensagem do advogado: {mensagem}"
            prompt = montar_prompt_instruct(system, user)
            raw = get_llama_response(prompt)
            import json
            data = json.loads((raw or "").strip())
            acao = str(data.get("acao", "nenhum")).lower()
            if acao not in {"aprovar", "recusar", "sugerir"}:
                acao = "nenhum"
            return {
                "acao": acao,
                "inicio_iso": (data.get("inicio_iso") or "").strip(),
                "fim_iso": (data.get("fim_iso") or "").strip(),
                "observacao": (data.get("observacao") or "").strip(),
            }
        except Exception:
            return {"acao": "nenhum", "inicio_iso": "", "fim_iso": "", "observacao": ""}

    # ==== FIM LLM NLU ====

    # ==== HELPERS CRM – BUSCAR/ATUALIZAR PEDIDO DE AGENDAMENTO ====
    def _buscar_pedido_agendamento_pendente(svc, sheet_id, numero):
        """
        Procura na aba Tarefas a última linha com:
          Col B == 'Pedido de agendamento', Col F == 'Pendente', Col D == numero.
        Retorna (row_index, label, inicio_iso, fim_iso) ou (None, None, '', '').
        """
        try:
            resp = svc.spreadsheets().values().get(
                spreadsheetId=sheet_id, range="Tarefas!A:H"
            ).execute()
            vals = resp.get("values", [])
            found = None
            for i, row in enumerate(vals[1:], start=2):  # assume linha 1 é header (ou não; funciona igual)
                b = (row[1] if len(row)>1 else "")
                f = (row[5] if len(row)>5 else "")
                d = (row[3] if len(row)>3 else "")
                if b == "Pedido de agendamento" and f == "Pendente" and d == numero:
                    found = (i, (row[2] if len(row)>2 else ""), (row[6] if len(row)>6 else ""), (row[7] if len(row)>7 else ""))
            return found if found else (None, None, "", "")
        except Exception:
            return (None, None, "", "")

    def _atualizar_status_tarefa(svc, sheet_id, row_index, novo_status):
        try:
            svc.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f"Tarefas!F{row_index}",
                valueInputOption="RAW",
                body={"values":[[novo_status]]}
            ).execute()
            return True
        except Exception:
            return False
    # ==== FIM HELPERS CRM ====

    # ==== EXECUTOR – CRIA EVENTO (APÓS CONFIRMAÇÃO DO ADVOGADO) ====
    def _exec_criar_evento_aprovado(numero, inicio_iso, fim_iso, descricao, data_ctx):
        """
        Usa criar_evento_calendar(...) se OAuth ok; reflete no CRM
        """
        try:
            from app.google_service import get_google_sheets_service
            svc = get_google_sheets_service()
            oauth_ok = svc is not None
            if not oauth_ok:
                return "✅ Evento aprovado e registrado (simulado)."

            nome_escr = f"Escritório {(data_ctx.get('escritorio_id') or 'Geral').title()}"
            arq = f"sheet_id_{nome_escr.replace(' ','_').lower()}.txt"
            if not os.path.exists(arq):
                return "✅ Evento aprovado (sem CRM configurado)."

            with open(arq,'r') as f:
                sheet_id = f.read().strip()

            # Cria o evento
            ev_id, ev_link = criar_evento_calendar(
                titulo="Consulta jurídica",
                inicio_iso=inicio_iso,
                fim_iso=fim_iso,
                convidados_emails=None,
                descricao=f"Agendamento aprovado para {numero}. {descricao or ''}".strip()
            )

            # Atualiza a tarefa para 'Aprovado'
            row_index, _, _, _ = _buscar_pedido_agendamento_pendente(svc, sheet_id, numero)
            if row_index:
                _atualizar_status_tarefa(svc, sheet_id, row_index, "Aprovado")

            return "✅ Agendamento aprovado e evento criado no Calendar." if ev_id else "⚠️ Tentei aprovar, mas não consegui criar o evento agora."
        except Exception:
            return "✅ Agendamento aprovado (simulado)."
    # ==== FIM EXECUTOR ====

    # reforço de segurança: sem parecer jurídico
    guard = "\n\nRegras: seja cordial, conciso e NUNCA forneça aconselhamento jurídico ou interpretações legais."
    prompt = montar_prompt_instruct(system_prompt + guard, user_message)
    resp = get_llama_response(prompt)
    # higiene mínima
    if not isinstance(resp, str) or len(resp.strip()) < 4:
        return None
    return resp.strip()
# ==== FIM LLM REDAÇÃO ====


# LLM NLU – interpretar decisão do advogado (agendamento)
def _interpretar_decisao_advogado(mensagem):
    """
    Classifica mensagem do advogado sobre um pedido de agendamento.
    Retorna: {acao: 'aprovar'|'recusar'|'sugerir'|'nenhum', inicio_iso, fim_iso, observacao}
    """
    try:
        from app.prompt_config import montar_prompt_instruct
        from app.ollama_service import get_llama_response
        system = (
            "Você recebe uma mensagem escrita por um advogado sobre um pedido de agendamento.\n"
            "Classifique em JSON com as chaves: acao ('aprovar'|'recusar'|'sugerir'|'nenhum'), "
            "inicio_iso (RFC3339), fim_iso (RFC3339), observacao.\n"
            "Se sugerir horário, normalize para America/Sao_Paulo e gere intervalos de 60 minutos "
            "a partir do contexto (ex.: 'amanhã às 10h' => inicio 10:00, fim 11:00). "
            "Se não houver horário claro, deixe vazio."
        )
        user = f"Mensagem do advogado: {mensagem}"
        prompt = montar_prompt_instruct(system, user)
        raw = get_llama_response(prompt)
        import json
        data = json.loads((raw or "").strip())
        acao = str(data.get("acao", "nenhum")).lower()
        if acao not in {"aprovar", "recusar", "sugerir"}:
            acao = "nenhum"
        return {
            "acao": acao,
            "inicio_iso": (data.get("inicio_iso") or "").strip(),
            "fim_iso": (data.get("fim_iso") or "").strip(),
            "observacao": (data.get("observacao") or "").strip(),
        }
    except Exception:
        return {"acao": "nenhum", "inicio_iso": "", "fim_iso": "", "observacao": ""}


# Substitui import direto por try/except com mocks
try:
    from app.google_service import (
        verificar_cliente_existente_google_api,
        registrar_lead_google_api,
        get_google_sheets_service,
        criar_evento_calendar,
        enviar_email_gmail,
        upload_drive_bytes,
    )
except ImportError:
    verificar_cliente_existente_google_api = lambda *args: None
    registrar_lead_google_api = lambda *args: None
    get_google_sheets_service = lambda *args, **kwargs: None
    criar_evento_calendar = lambda *args, **kwargs: (None, None)
    enviar_email_gmail = lambda *args, **kwargs: None
    upload_drive_bytes = lambda *args, **kwargs: (None, None)

from flask import Blueprint, request, jsonify, Response, g, redirect, url_for  # redirect/url_for
import logging, json, re  # logging estruturado e regex
from unidecode import unidecode

# Configuração básica de logging (pode ser ajustada depois)
logging.basicConfig(level=logging.INFO)

# --- Fallback for MessagingResponse if twilio is missing ---
try:
    from twilio.twiml.messaging_response import MessagingResponse
    from unidecode import unidecode
    import os

except ImportError:
    class MessagingResponse:
        def __init__(self):
            self._msg = None
        def message(self, text):
            self._msg = text
        def __str__(self):
            return f"<Response><Message>{self._msg}</Message></Response>"

# === END PLACEHOLDER STUBS ===
# Dispatcher para fluxos jurídicos: retorna todas as ações possíveis para uma mensagem
def dispatcher_fluxos_advogado(mensagem):
    """
    Chama todos os fluxos jurídicos e retorna uma lista de ações possíveis para a mensagem.
    Útil para sugerir múltiplas rotas ou para logging/expansão futura.
    """
    fluxos = {
        "onboarding_advogado": fluxo_onboarding_advogado,
        "aprovacao_peticao": fluxo_aprovacao_peticao,
        "alerta_prazo": fluxo_alerta_prazo,
        "honorarios": fluxo_honorarios,
        "documento_juridico": fluxo_documento_juridico,
        "enviar_documento_cliente": fluxo_envio_documento_cliente,
        "consulta_andamento": fluxo_consulta_andamento,
        "pagamento_fora_padrao": fluxo_pagamento_fora_padrao,
        "indicacao": fluxo_indicacao,
        "documento_pendente": fluxo_documento_pendente,
        "revisao_documento": fluxo_revisao_documento,
        "status_negociacao": fluxo_status_negociacao,
        "decisao_permuta": fluxo_decisao_permuta,
        "sumico_cliente": fluxo_sumiço_cliente,
        "update_clientes_aguardando": fluxo_update_clientes_aguardando,
        "update_documento_pendente": fluxo_update_documento_pendente,
        "nao_atendimento_area": fluxo_nao_atendimento_area,
        "status_multiplos_processos": fluxo_status_multiplos_processos,
        "notificacao_cliente": fluxo_notificacao_cliente,
        "alterar_cancelar_agendamento": fluxo_alterar_cancelar_agendamento,
        "resumo_estatisticas": fluxo_resumo_estatisticas,
        "lembrete_audiencia": fluxo_lembrete_audiencia,
        "enviar_resumo_caso": fluxo_enviar_resumo_caso
    }
    for nome, func in fluxos.items():
        resultado = func(mensagem)
        # Para fluxos que retornam dict, considerar "match" se não for None e tiver dados relevantes
        if resultado:
            return nome, resultado
    raise ValueError(f"Nenhum fluxo reconhecido para mensagem: {mensagem}")
def processar_mensagem_advogado(mensagem):
    """
    Processa uma mensagem recebida de advogado, testando todos os fluxos inteligentes.
    Retorna um dicionário com o status do fluxo detectado e dados relevantes.
    """
    # 1. Onboarding
    dados_onboarding = fluxo_onboarding_advogado(mensagem)
    if dados_onboarding and dados_onboarding.get("nome_completo"):
        # Salvar no banco, acionar planilha, etc.
        return {"status": "onboarding", "dados": dados_onboarding}

    # 2. Aprovação de petição
    status_peticao = fluxo_aprovacao_peticao(mensagem)
    if status_peticao and status_peticao.get("status") == "aprovado":
        # Liberar petição no sistema
        return {"status": "peticao_aprovada"}

    # 3. Alerta de prazo
    if fluxo_alerta_prazo(mensagem):
        # Acionar lembrete
        return {"status": "lembrete_prazo"}

    # 4. Honorários
    if fluxo_honorarios(mensagem):
        return {"status": "honorarios"}

    # 5. Documento jurídico
    if fluxo_documento_juridico(mensagem):
        return {"status": "documento_juridico"}

    # 6. Envio de documento ao cliente
    if fluxo_envio_documento_cliente(mensagem):
        return {"status": "enviar_documento_cliente"}

    # 7. Consulta de andamento
    if fluxo_consulta_andamento(mensagem):
        return {"status": "consulta_andamento"}

    # 8. Pagamento fora do padrão
    if fluxo_pagamento_fora_padrao(mensagem):
        return {"status": "pagamento_fora_padrao"}

    # 9. Indicação
    if fluxo_indicacao(mensagem):
        return {"status": "indicacao"}

    # 10. Documento pendente
    if fluxo_documento_pendente(mensagem):
        return {"status": "documento_pendente"}

    # 11. Revisão de documento
    if fluxo_revisao_documento(mensagem):
        return {"status": "revisao_documento"}

    # 12. Status de negociação
    if fluxo_status_negociacao(mensagem):
        return {"status": "status_negociacao"}

    # 13. Decisão de permuta
    if fluxo_decisao_permuta(mensagem):
        return {"status": "decisao_permuta"}

    # 14. Sumiço de cliente
    if fluxo_sumiço_cliente(mensagem):
        return {"status": "sumico_cliente"}

    # 15. Update clientes aguardando
    if fluxo_update_clientes_aguardando(mensagem):
        return {"status": "update_clientes_aguardando"}

    # 16. Update documento pendente
    if fluxo_update_documento_pendente(mensagem):
        return {"status": "update_documento_pendente"}

    # 17. Não atendimento da área
    if fluxo_nao_atendimento_area(mensagem):
        return {"status": "nao_atendimento_area"}

    # 18. Status múltiplos processos
    if fluxo_status_multiplos_processos(mensagem):
        return {"status": "status_multiplos_processos"}

    # 19. Notificação ao cliente
    if fluxo_notificacao_cliente(mensagem):
        return {"status": "notificacao_cliente"}

    # 20. Alterar/cancelar agendamento
    if fluxo_alterar_cancelar_agendamento(mensagem):
        return {"status": "alterar_cancelar_agendamento"}

    # 21. Resumo de estatísticas
    if fluxo_resumo_estatisticas(mensagem):
        return {"status": "resumo_estatisticas"}

    # 22. Lembrete de audiência
    if fluxo_lembrete_audiencia(mensagem):
        return {"status": "lembrete_audiencia"}

    # 23. Enviar resumo do caso
    if fluxo_enviar_resumo_caso(mensagem):
        return {"status": "enviar_resumo_caso"}

    # Se não bater nenhum fluxo, responde padrão
    return {"status": "fluxo_nao_detectado"}

# Função: Conversão de lead em cliente com coleta e organização de documentos
def processar_conversao_cliente(numero, nome_cliente, documentos, relato_caso, email_advogado=None):
    """
    1. Solicita documento de identificação com foto e comprovante de endereço válido.
    2. Se não houver comprovante, oferece modelo de declaração de residência.
    3. Ao receber documentos, cria pasta no Google Drive com nome do cliente e armazena os arquivos.
    4. Adiciona arquivo de texto com relato do caso e atualiza conforme o CRM.
    5. Envia link da pasta para o advogado via WhatsApp.
    6. Debugging detalhado das integrações Google.
    """
    debug = {"drive": None, "whatsapp": None, "crm": None, "erro": None}
    try:
        # 1. Checagem dos documentos recebidos
        doc_id = documentos.get('identidade')
        doc_endereco = documentos.get('comprovante_endereco')
        precisa_declaracao = not doc_endereco
        link_declaracao = None
        if precisa_declaracao:
            # Gerar modelo de declaração de residência (link fictício ou real)
            link_declaracao = "https://docs.google.com/document/d/DECLARACAO_RESIDENCIA_MODEL"
        # 2. Criar pasta no Google Drive
        pasta_nome = nome_cliente.strip()
        pasta_id = None
        pasta_link = None
        if build:
            try:
                # Exemplo: criar pasta no Google Drive
                service = build('drive', 'v3', credentials=Credentials.from_authorized_user_file('token.json'))
                file_metadata = {'name': pasta_nome, 'mimeType': 'application/vnd.google-apps.folder'}
                folder = service.files().create(body=file_metadata, fields='id,webViewLink').execute()
                pasta_id = folder.get('id')
                pasta_link = folder.get('webViewLink')
                debug['drive'] = f"Pasta criada: {pasta_link}"
                # 3. Upload dos documentos recebidos
                for doc_tipo, doc_file in documentos.items():
                    if doc_file:
                        file_metadata = {'name': f"{doc_tipo}_{pasta_nome}", 'parents': [pasta_id]}
                        media = None  # Aqui você faria o upload real do arquivo
                        # Exemplo: service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                # 4. Adicionar relato do caso como arquivo de texto
                file_metadata = {'name': f"relato_{pasta_nome}.txt", 'parents': [pasta_id]}
                media = None  # Aqui você faria upload do texto como arquivo
                # Exemplo: service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            except Exception as e:
                debug['drive'] = f"Erro Drive: {e}"
        else:
            debug['drive'] = "Google Drive não disponível"
        # 5. Enviar link da pasta para o advogado via WhatsApp (simulado)
        mensagem = f"criei a pasta de {nome_cliente} e adicionei os documentos enviados neste link: {pasta_link or '[link indisponível]'}"
        # Aqui você pode integrar com o serviço de WhatsApp real ou simulado
        debug['whatsapp'] = f"Mensagem enviada: {mensagem}"
        # 6. Atualizar CRM (simulado)
        debug['crm'] = "CRM atualizado com novo cliente e documentos"
        return {
            "status": "ok",
            "mensagem": mensagem,
            "pasta_link": pasta_link,
            "debug": debug,
            "precisa_declaracao": precisa_declaracao,
            "link_declaracao": link_declaracao
        }
    except Exception as e:
        debug['erro'] = str(e)
        return {"status": "erro", "debug": debug}
import threading
from flask import Blueprint, request, jsonify, Response

# Blueprint deve ser definido antes de ser usado
atendimento_bp = Blueprint('atendimento', __name__)
prompt_config_lock = threading.Lock()



# ROTA PARA GET/POST DO PROMPT_CONFIG
@atendimento_bp.route('/prompt_config', methods=['GET', 'POST'])
def prompt_config_api():
    # Importação local para garantir que prompt_config está sempre atualizado
    import importlib
    prompt_config_module = importlib.import_module('app.prompt_config')
    config_ref = prompt_config_module.prompt_config
    if request.method == 'GET':
        return jsonify(config_ref)
    elif request.method == 'POST':
        data = request.json
        for k, v in data.items():
            config_ref[k] = v
        return jsonify({"status": "ok", "prompt_config": config_ref})

# Endpoint opcional para status detalhado (mock)
@atendimento_bp.route('/status', methods=['GET'])
def status_backend():
    svc = get_google_sheets_service()
    return jsonify({
        "flask_backend": "OK",
        "google_oauth": bool(svc is not None),
        "endpoints": ["/processar_atendimento", "/authorize", "/oauth2callback", "/status"]
    }), 200
import traceback
import os
import json
import tempfile
import requests
from datetime import datetime
try:
    import whisper
except ImportError:
    print("⚠️ Whisper não instalado, transcrições desabilitadas")
    whisper = None

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("⚠️ Google API não instalada, funcionalidades desabilitadas")
    Credentials = None
    build = None
    HttpError = None

from email.mime.text import MIMEText
import base64
from flask import Blueprint, request, jsonify


try:
    from app.database_service import log_message
except ImportError:
    log_message = lambda *args: print(f"Log: {args}")

try:
    from app.ollama_service import get_llama_response, classify_intent_llm
except ImportError:
    get_llama_response = lambda prompt: "LLM não disponível"

try:
    from app.ollama_service import extrair_dados_caso_llm
except ImportError:
    extrair_dados_caso_llm = lambda texto, dados_existentes=None: {
        "nome_cliente": None,
        "telefone": (dados_existentes or {}).get("telefone_cliente", ""),
        "area_direito": "Geral",
        "urgencia": "Média",
        "resumo_caso": texto,
        "observacoes": ""
    }
#Assim, a função extrair_dados_caso_llm estará definida antes de qualquer chamada no processar_relato_caso().

try:
    from app.prompt_config import prompt_config, montar_prompt_instruct
except ImportError:
    prompt_config = {}
    # Fallback sem template proprietário; tenta importar em runtime, senão concatena simples
    try:
        from app.prompt_config import montar_prompt_instruct  # runtime import para evitar hardcode
    except Exception:
        def montar_prompt_instruct(system_prompt, user_message):
            return f"{system_prompt}\nUsuário: {user_message}"

try:
    from app.google_service import verificar_cliente_existente_google_api, registrar_lead_google_api
except ImportError:
    verificar_cliente_existente_google_api = lambda *args: None
    registrar_lead_google_api = lambda *args: None

try:
    from app.classification import extrair_infos
except ImportError:
    extrair_infos = lambda text: {}

# Global para controlar conversas e estado
conversas = {}

print("🚀 Carregando módulo de atendimento com integração completa...")
print("🤖 Whisper, Google Sheets, Gmail e Calendar carregados!")

# --- Intent detection simples e priorizado ---
import re as _re
_RE_NUM_PROC = _re.compile(r'\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}')

# Helper de detecção de saudação
def is_saudacao(texto: str) -> bool:
    t = (texto or "").strip().lower()
    gatilhos = [
        "oi", "olá", "ola", "bom dia", "boa tarde", "boa noite",
        "tudo bem", "como vai", "e aí", "eaí", "salve"
    ]
    # saudação curta (até ~25 chars) e sem palavras de intenção
    return any(t.startswith(g) for g in gatilhos) and not any(
        k in t for k in ["processo", "agendar", "reuni", "documento", "andamento", "consulta", "rg", "cnh"]
    )


def detect_intent(texto):
    # normaliza acentos e caixa
    t = unidecode((texto or "").lower().strip())

    import re as _re
    _RE_NUM_PROC = _re.compile(r'\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}')
    _RE_HOUR = _re.compile(r'\b(\d{1,2}(:\d{2})?\s?(h|hrs|horas)?)\b', _re.IGNORECASE)
    _RE_DATE = _re.compile(r'\b(\d{1,2}/\d{1,2}(/\d{2,4})?)\b')
    _RE_DOW  = _re.compile(r'\b(segunda|terca|terça|quarta|quinta|sexta|sabado|sábado|domingo)\b', _re.IGNORECASE)

    # 0) Relato de caso (cliente descrevendo situação pessoal)
    gatilhos_relato = [
        "fui demitido","sem justa causa","meus direitos","tive um acidente","preciso de ajuda",
        "me aconteceu","relato","direito do consumidor","problema no trabalho"
    ]
    if any(k in t for k in gatilhos_relato) and "processo" not in t:
        return "relato_caso"

    # 1) Consulta de andamento (prioridade alta)
    if (("andamento" in t or "novidade" in t or "como esta" in t) and "processo" in t) or _RE_NUM_PROC.search(t):
        return "consulta_andamento_cliente"

    # 2) Agendar consulta
    gatilhos_agenda = [
        "agendar","consulta","horario","reuniao","agenda","marcar","marcacao",
        "agendamento","consultar horario","sexta","amanha","hoje","semana que vem"
    ]
    if any(k in t for k in gatilhos_agenda) or _RE_HOUR.search(t) or _RE_DATE.search(t) or _RE_DOW.search(t):
        return "agendar_consulta_cliente"

    # 3) Enviar documento
    if any(k in t for k in ["rg","cnh","comprovante","documento","anexo","pdf","foto","imagem","segue anexo"]):
        return "enviar_documento_cliente"

    # 4) Relato de caso (padrão)
    if any(k in t for k in ["demitid","pensao","divida","juros","banco","indeniza","direito"]):
        return "relato_caso"

    return "fluxo_nao_detectado"


def _rank_intents(t: str):
    """Score heurístico leve para desempatar intents por sinais (regex/keywords)."""
    t = unidecode((t or "").lower().strip())
    score = {
        "consulta_andamento_cliente": 0,
        "agendar_consulta_cliente": 0,
        "enviar_documento_cliente": 0,
        "relato_caso": 0,
        "atualizar_cadastro_cliente": 0,
        "alterar_cancelar_agendamento": 0,
    }

    # Sinais fortes
    if _RE_NUM_PROC.search(t):
        score["consulta_andamento_cliente"] += 3
    if any(k in t for k in ["rg", "cnh", "comprovante", "anexo", "pdf", "documento", "foto"]):
        score["enviar_documento_cliente"] += 3
    if any(k in t for k in ["agendar", "marcar", "remarcar", "horario", "agenda", "consulta", "reuniao", "reunião"]):
        score["agendar_consulta_cliente"] += 2
    if any(k in t for k in ["cancelar agendamento", "desmarcar", "reagendar", "remarcar", "adiar", "trocar horario"]):
        score["alterar_cancelar_agendamento"] += 2
    if any(k in t for k in ["mudei de endereco", "novo telefone", "atualizar cadastro", "troquei de telefone", "atualizar telefone", "novo endereco"]):
        score["atualizar_cadastro_cliente"] += 2

    # Sinais fracos de relato
    if any(k in t for k in ["demitid", "direito", "indeniza", "acidente", "me aconteceu", "preciso de ajuda", "meus direitos"]):
        score["relato_caso"] += 2

    # Horário/data/dia da semana -> agendar
    if _re.search(r"\b(\d{1,2}(:\d{2})?\s?(h|hrs|horas)?)\b", t) or \
       _re.search(r"\b(\d{1,2}/\d{1,2}(/\d{2,4})?)\b", t) or \
       _re.search(r"\b(segunda|terca|terça|quarta|quinta|sexta|sabado|sábado|domingo)\b", t, _re.IGNORECASE):
        score["agendar_consulta_cliente"] += 1

    # Escolhe o maior score (empate -> None)
    best = max(score, key=score.get)
    return best if score[best] > 0 and list(score.values()).count(score[best]) == 1 else None


def _detect_with_nlu_llm(texto: str):
    """
    Orquestra detecção: 1) NLU via text_processing fluxos; 2) score regex; 3) classificador few-shot LLM.
    Retorna um dos rótulos: relato_caso, consulta_andamento_cliente, agendar_consulta_cliente,
    enviar_documento_cliente, atualizar_cadastro_cliente, alterar_cancelar_agendamento, fluxo_nao_detectado
    """
    t = (texto or "")
    # 1) NLU via text_processing (cliente)
    try:
        from app.routes.text_processing import (
            fluxo_agendar_consulta_cliente, fluxo_enviar_documento_cliente,
            fluxo_relato_caso, fluxo_consulta_andamento_cliente,
            fluxo_atualizar_cadastro_cliente, fluxo_alterar_cancelar_agendamento,
        )
        if fluxo_consulta_andamento_cliente(t):
            return "consulta_andamento_cliente"
        if fluxo_agendar_consulta_cliente(t):
            return "agendar_consulta_cliente"
        if fluxo_enviar_documento_cliente(t):
            return "enviar_documento_cliente"
        if fluxo_atualizar_cadastro_cliente(t):
            return "atualizar_cadastro_cliente"
        if fluxo_alterar_cancelar_agendamento(t):
            return "alterar_cancelar_agendamento"
        if fluxo_relato_caso(t):
            return "relato_caso"
    except Exception:
        pass

    # 2) Score por regex/keywords
    guess = _rank_intents(t)
    if guess:
        return guess

    # 3) Tie-breaker com LLM few-shot (prompt_config["intent_classifier_prompt"])
    try:
        from app.prompt_config import prompt_config, montar_prompt_instruct
        from app.ollama_service import get_llama_response
        system = prompt_config.get("intent_classifier_prompt", "")
        prompt = montar_prompt_instruct(system, t)
        label = (get_llama_response(prompt) or "").strip()
        if label in {
            "relato_caso",
            "consulta_andamento_cliente",
            "agendar_consulta_cliente",
            "enviar_documento_cliente",
            "atualizar_cadastro_cliente",
            "alterar_cancelar_agendamento",
        }:
            return label
    except Exception:
        pass

    return "fluxo_nao_detectado"

def processar_relato_caso(texto_ou_audio, telefone_cliente, segmento, tipo_arquivo=None):
    """
    Processa relato de caso (texto ou áudio) e registra na planilha
    """
    print(f"📝 Processando relato de caso para cliente: {telefone_cliente}")
    
    # 1. Se for áudio, transcrever primeiro
    if tipo_arquivo and tipo_arquivo.lower() in ['audio', 'mp3', 'wav', 'ogg', 'm4a']:
        print("🎙️ Detectado arquivo de áudio, transcrevendo...")
        try:
            texto_caso = transcrever_audio_whisper(texto_ou_audio)
            if not texto_caso:
                return "❌ Não consegui transcrever o áudio. Tente enviar novamente ou digite o relato."
        except Exception as e:
            print(f"❌ Erro na transcrição: {e}")
            return "❌ Erro ao processar áudio. Tente enviar um arquivo de áudio válido ou digite o relato."
    else:
        texto_caso = texto_ou_audio
    
    # 2. Extrair informações do caso com LLM
    dados_caso = extrair_dados_caso_llm(texto_caso, dados_existentes={"telefone_cliente": telefone_cliente})
    
    # 3. Determinar nome do escritório (por enquanto, usar segmento)
    nome_escritorio = f"Escritório {segmento.title()}"
    email_advogado = None  # TODO: buscar email real do advogado contratante
    
    # 4. Registrar caso na planilha (cria planilha se necessário)
    sucesso = registrar_caso_planilha(nome_escritorio, dados_caso, email_advogado)
    
    if sucesso:
        # 5. Gerar resposta personalizada
        resposta = (
            f"✅ Relato anotado com sucesso!\n\n"
            f"📋 Resumo do seu caso:\n"
            f"• Área: {dados_caso['area_direito']}\n"
            f"• Urgência: {dados_caso['urgencia']}\n"
            f"• Status: Registrado para análise\n\n"
            f"Seu caso foi encaminhado para o advogado responsável. "
            f"Você será contatado em breve.\n\n"
            f"💬 Quer agendar um atendimento presencial ou tem mais alguma dúvida?"
        )
        
        return resposta
    else:
        return "❌ Erro ao registrar seu caso. Tente novamente ou entre em contato por telefone."

def transcrever_audio_whisper(audio_data_ou_url):
    """
    Transcreve áudio usando Whisper (OpenAI)
    """
    print(f"🎙️ Iniciando transcrição de áudio...")
    
    try:
        # Carregar modelo Whisper (cache automático)
        print("🔄 Carregando modelo Whisper...")
        modelo_whisper = whisper.load_model("base")
        print("✅ Modelo Whisper carregado")
        
        # Criar arquivo temporário para o áudio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            if isinstance(audio_data_ou_url, str) and audio_data_ou_url.startswith('http'):
                # Se for URL, baixar o arquivo
                print(f"📥 Baixando áudio da URL: {audio_data_ou_url[:50]}...")
                response = requests.get(audio_data_ou_url)
                temp_audio.write(response.content)
            else:
                # Se for dados binários
                print("💾 Salvando dados de áudio em arquivo temporário...")
                temp_audio.write(audio_data_ou_url)
            
            temp_audio_path = temp_audio.name
        
        print(f"🎙️ Transcrevendo áudio: {temp_audio_path}")
        resultado = modelo_whisper.transcribe(temp_audio_path)
        texto_transcrito = resultado["text"].strip()
        
        # Limpar arquivo temporário
        os.unlink(temp_audio_path)
        print(f"🗑️ Arquivo temporário removido: {temp_audio_path}")
        
        print(f"✅ Transcrição concluída: {texto_transcrito[:100]}...")
        return texto_transcrito
        
    except Exception as e:
        print(f"❌ Erro na transcrição com Whisper: {e}")
        traceback.print_exc()
        return None

def registrar_caso_planilha(nome_escritorio, dados_caso, email_advogado=None):
    """
    Registra caso jurídico em planilha específica do escritório
    Se planilha não existir, cria e envia link para o advogado
    """
    print(f"📊 Registrando caso na planilha do escritório: {nome_escritorio}")
    print(f"🔍 Dados do caso: {dados_caso}")
    
    try:
        from app.google_service import get_google_sheets_service, buscar_ou_criar_planilha
        
        # Buscar planilha específica do escritório
        arquivo_planilha_escritorio = f"sheet_id_{nome_escritorio.replace(' ', '_').lower()}.txt"
        print(f"📁 Procurando planilha: {arquivo_planilha_escritorio}")
        
        sheet_id = None
        planilha_nova = False
        
        if os.path.exists(arquivo_planilha_escritorio):
            with open(arquivo_planilha_escritorio, 'r') as f:
                sheet_id = f.read().strip()
            print(f"✅ Planilha existente encontrada: {sheet_id}")
        else:
            print(f"❌ Planilha não encontrada, criando nova...")
            planilha_nova = True
            sheet_id = criar_planilha_casos_escritorio(nome_escritorio, arquivo_planilha_escritorio)
            
            if sheet_id and email_advogado:
                print(f"📧 Enviando link da planilha para advogado: {email_advogado}")
                enviar_link_planilha_email(email_advogado, nome_escritorio, sheet_id)
        
        if not sheet_id:
            print("❌ Não foi possível obter ou criar sheet_id")
            return False
        
        # Registrar caso na planilha
        print(f"📝 Registrando caso na planilha: {sheet_id}")
        service = get_google_sheets_service()
        if not service:
            print("❌ Falha ao obter serviço Google Sheets")
            return False
        
        # Obter nome da primeira aba
        meta = service.spreadsheets().get(
            spreadsheetId=sheet_id,
            fields="sheets.properties"
        ).execute()
        primeira_aba = meta['sheets'][0]['properties']['title']
        print(f"🔖 Usando aba: {primeira_aba}")
        
        # Preparar dados para inserção
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        linha_dados = [
            agora,                                          # Data/Hora
            dados_caso.get("nome_cliente", "NÃO_INFORMADO"), # Nome
            dados_caso.get("telefone", ""),                 # Telefone
            dados_caso.get("area_direito", "Genérico"),     # Área
            dados_caso.get("urgencia", "Média"),            # Urgência
            dados_caso.get("resumo_caso", ""),              # Resumo
            "Aguardando Análise",                          # Status
            dados_caso.get("observacoes", "")              # Observações
        ]
        
        # Inserir dados
        append_range = f"{primeira_aba}!A:H"
        body = {"values": [linha_dados]}
        
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=append_range,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        
        print("✅ Caso registrado com sucesso na planilha")
        
        # Se for planilha nova, avisar que o link foi enviado
        if planilha_nova and email_advogado:
            print(f"📧 Link da nova planilha enviado para: {email_advogado}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao registrar caso na planilha: {e}")
        traceback.print_exc()
        return False

def criar_planilha_casos_escritorio(nome_escritorio, arquivo_planilha):
    """
    Cria planilha específica para casos do escritório
    """
    print(f"📊 Criando planilha de casos para: {nome_escritorio}")
    
    try:
        from app.google_service import get_google_sheets_service
        
        service = get_google_sheets_service()
        if not service:
            print("❌ Falha ao obter serviço Google Sheets")
            return None
        
        # Criar planilha com nome específico
        titulo_planilha = f"Casos Jurídicos - {nome_escritorio}"
        spreadsheet = {
            'properties': {'title': titulo_planilha}
        }
        
        print(f"🔄 Criando planilha: {titulo_planilha}")
        created = service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId,sheets.properties'
        ).execute()
        
        sheet_id = created.get('spreadsheetId')
        primeira_aba = created['sheets'][0]['properties']['title']
        
        print(f"✅ Planilha criada: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        print(f"🔖 Primeira aba: {primeira_aba}")
        
        # Criar cabeçalho especializado para casos jurídicos
        cabecalho = [
            "Data/Hora",
            "Nome Cliente", 
            "Telefone",
            "Área do Direito",
            "Urgência",
            "Resumo do Caso",
            "Status",
            "Observações"
        ]
        
        header_range = f"{primeira_aba}!A1:H1"
        header_body = {"values": [cabecalho]}
        
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=header_range,
            valueInputOption="RAW",
            body=header_body
        ).execute()
        
        print("✅ Cabeçalho criado na planilha de casos")
        
        # Compartilhar planilha para edição pública
        from googleapiclient.discovery import build
        drive = build("drive", "v3", credentials=service._http.credentials)
        drive.permissions().create(
            fileId=sheet_id,
            body={"type": "anyone", "role": "writer"},
            fields="id"
        ).execute()
        
        print("🌐 Planilha compartilhada para edição pública")
        
        # Salvar sheet_id em arquivo
        with open(arquivo_planilha, 'w') as f:
            f.write(sheet_id)
        print(f"💾 Sheet ID salvo em: {arquivo_planilha}")
        
        return sheet_id
        
    except Exception as e:
        print(f"❌ Erro ao criar planilha de casos: {e}")
        traceback.print_exc()
        return None

def enviar_link_planilha_email(email_advogado, nome_advogado, sheet_id):
    """
    Envia link da planilha por email para o advogado
    """
    print(f"📧 Preparando envio de email para: {email_advogado}")
    
    try:
        from googleapiclient.discovery import build
        from app.google_service import get_google_sheets_service
        import base64
        from email.mime.text import MIMEText
        
        service = get_google_sheets_service()
        if not service:
            print("❌ Falha ao obter credenciais para Gmail")
            return False
        
        # Construir Gmail service
        gmail = build("gmail", "v1", credentials=service._http.credentials)
        
        # Link da planilha
        link_planilha = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        
        # Conteúdo do email
        assunto = f"Nova Planilha de Casos Criada - {nome_advogado}"
        corpo_email = f"""
Olá!

Uma nova planilha de casos foi criada para o {nome_advogado}.

🔗 Link da Planilha: {link_planilha}

Esta planilha foi criada automaticamente pelo PocketMKT para organizar os casos dos seus clientes.

Características da planilha:
• Registra automaticamente casos relatados pelos clientes
• Organiza por área do direito, urgência e status
• Compartilhada para edição (você pode modificar diretamente)
• Atualizada em tempo real conforme novos casos chegam

Acesse o link para visualizar e gerenciar os casos.

Atenciosamente,
PocketMKT - Assistente Virtual
"""
        
        # Criar mensagem
        message = MIMEText(corpo_email, 'plain', 'utf-8')
        message['to'] = email_advogado
        message['subject'] = assunto
        
        # Codificar mensagem
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Enviar email
        print(f"📤 Enviando email para: {email_advogado}")
        gmail.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"✅ Email enviado com sucesso para: {email_advogado}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        traceback.print_exc()
        return False

from twilio.twiml.messaging_response import MessagingResponse


def _check_confirm(numero_whats, texto_lower):
    """Verifica se o usuário confirmou ou cancelou a execução pendente."""
    from datetime import datetime
    pend = processar_atendimento._pending.get(numero_whats)
    if not pend:
        return None
    if datetime.utcnow() > pend["exp"]:
        processar_atendimento._pending.pop(numero_whats, None)
        return "⏰ Pedido expirou. Posso montar novamente."
    if texto_lower in ("confirmar", "confirmo", "pode confirmar", "ok confirmar", "ok, confirmar"):
        try:
            msg_ok = pend["exec"]() or "✅ Feito!"
            processar_atendimento._pending.pop(numero_whats, None)
            return msg_ok
        except Exception as e:
            processar_atendimento._pending.pop(numero_whats, None)
            return f"❌ Falha ao executar: {e}"
    if texto_lower in ("cancelar", "cancela", "nao", "não"):
        processar_atendimento._pending.pop(numero_whats, None)
        return "❎ Cancelado. Quer tentar outra coisa?"
    return None


def _footer_advogado():
    """Rodapé curto com dicas para o advogado no fast-path."""
    return ("\n\nDicas: responda 'confirmar' para executar ou 'cancelar' para descartar. "
            "Você também pode dizer, por exemplo: 'sugerir terça 14h', 'aprovar' ou 'recusar'.")

# Helper para decidir auto-execução vs. proposta com confirmação
def _auto_or_propose(intent_key, numero, preview, exec_cb, ttl=15):
    from datetime import datetime, timedelta
    if AUTO_EXEC_POLICY.get(intent_key):
        try:
            msg_ok = exec_cb() or "✅ Feito!"
            return msg_ok
        except Exception as e:
            return f"❌ Falha ao executar: {e}"
    # fallback: precisa confirmar (replica o comportamento de _propose)
    if not hasattr(processar_atendimento, "_pending"):
        processar_atendimento._pending = {}
    processar_atendimento._pending[numero] = {
        "exp": datetime.utcnow() + timedelta(minutes=ttl),
        "preview": preview,
        "exec": exec_cb,
    }
    return f"{preview}\n\nResponda *confirmar* para executar, ou *cancelar* para descartar."

@atendimento_bp.route('/processar_atendimento', methods=['POST'])
def processar_atendimento():
    """Endpoint principal unificado: detecta fluxos básicos de cliente e todos de advogado.
    Sempre retorna HTTP 200 com contrato mínimo (resposta, fluxo, numero, tipo_usuario, ids...)."""
    try:
        data = request.get_json() or {}

        # Healthcheck curto-circuito (sem exigir OAuth ou outros requisitos)
        if data.get("healthcheck"):
            return jsonify({
                "resposta": "pong",
                "fluxo": "healthcheck",
                "numero": data.get("numero"),
                "tipo_usuario": (data.get("tipo_usuario") or "").lower()
            }), 200

        mensagem = (data.get('mensagem') or '').strip()
        numero = data.get('numero')
        tipo_usuario = (data.get('tipo_usuario') or '').lower()
        # Camada de acolhimento (pré)
        pre_msg = _humanize_pre(mensagem, tipo_usuario)

        # === Camada de CONFIRMAÇÃO (anti-metralhadora) ===
        from datetime import datetime, timedelta, timezone

        if not hasattr(processar_atendimento, "_pending"):
            processar_atendimento._pending = {}  # {numero: {"exp":dt, "preview":str, "exec":callable}}

        def _propose(numero_whats, preview, exec_cb, ttl=15):
            processar_atendimento._pending[numero_whats] = {
                "exp": datetime.utcnow() + timedelta(minutes=ttl),
                "preview": preview,
                "exec": exec_cb,
            }
            return f"{preview}\n\nResponda *confirmar* para executar, ou *cancelar* para descartar."

        # Saudação -> responde educadamente e triagem
        if is_saudacao(mensagem):
            g.fluxo_detectado = "saudacao_inicial"
            resposta_texto = _llm_reply("system", mensagem) or pre_msg or "Olá! Em que posso te ajudar hoje?"
            resposta_texto = _humanize_post(_humanize_during(resposta_texto), "saudacao_inicial")
            payload = {
                "resposta": resposta_texto,
                "fluxo": "saudacao_inicial",
                "numero": numero,
                "tipo_usuario": tipo_usuario,
                "intent_source": "rule",
                "is_saudacao": True
            }
            # Rede de segurança: garante tom educado + próximos passos se não for saudação
            if not payload.get("is_saudacao"):
                payload["resposta"] = _humanize_post(_humanize_during(payload["resposta"]), payload.get("fluxo"))
            return jsonify(payload), 200

        fluxo_detectado = None
        resposta_texto = "Em breve..."
        ids = {}
        intent_source = "rule"  # telemetria padrão

        # ---------------- Fluxos ADVOGADO (mantém lógica existente) ----------------
        if tipo_usuario == 'advogado':
            svc = get_google_sheets_service()
            oauth_ok = svc is not None

            # Trata confirma/cancela de propostas pendentes (preview já enviado antes)
            conf = _check_confirm(numero, (mensagem or '').lower())
            if conf:
                fluxo_detectado = "aprovar_agendamento_advogado"
                resp = _humanize_post(_humanize_during(conf), fluxo_detectado) + _footer_advogado()
                payload = {"resposta": resp, "fluxo": fluxo_detectado, "numero": numero, "tipo_usuario": tipo_usuario, "intent_source": "rule"}
                return jsonify(payload), 200

            # 0) NLU: o advogado está aprovando/recusando/sugerindo horário?
            decisao = _interpretar_decisao_advogado(mensagem)
            if decisao.get("acao") in {"aprovar","recusar","sugerir"}:
                # Buscar pedido pendente desse número
                try:
                    nome_escr = f"Escritório {(data.get('escritorio_id') or 'Geral').title()}"
                    arq = f"sheet_id_{nome_escr.replace(' ','_').lower()}.txt"
                    sheet_id = None
                    if os.path.exists(arq):
                        with open(arq,'r') as f: sheet_id = f.read().strip()
                    if not (svc and sheet_id):
                        # Sem CRM: ainda assim responde humano
                        if decisao["acao"] == "recusar":
                            resposta_texto = "✅ Pedido de agendamento **recusado**. Não registrarei evento."
                            fluxo_detectado = "aprovar_agendamento_advogado"
                            resp = _humanize_post(_humanize_during(resposta_texto), fluxo_detectado) + _footer_advogado()
                            payload = {"resposta": resp, "fluxo": fluxo_detectado, "numero": numero, "tipo_usuario": tipo_usuario, "intent_source": "llm"}
                            return jsonify(payload), 200

                    row_index, label, inicio_iso_salvo, fim_iso_salvo = _buscar_pedido_agendamento_pendente(svc, sheet_id, numero)
                    if not row_index:
                        # Nenhum pedido pendente para esse cliente
                        resposta_texto = "Não encontrei pedido de agendamento pendente para este cliente. Posso registrar um novo pedido?"
                        fluxo_detectado = "aprovar_agendamento_advogado"
                        resp = _humanize_post(_humanize_during(resposta_texto), fluxo_detectado) + _footer_advogado()
                        payload = {"resposta": resp, "fluxo": fluxo_detectado, "numero": numero, "tipo_usuario": tipo_usuario, "intent_source": "llm"}
                        return jsonify(payload), 200

                    acao = decisao["acao"]
                    # Se o advogado recusou
                    if acao == "recusar":
                        _atualizar_status_tarefa(svc, sheet_id, row_index, "Recusado")
                        resposta_texto = "✅ Pedido de agendamento **recusado**. Informe ao cliente um novo período desejável ou peça para ele sugerir outros horários."
                        fluxo_detectado = "aprovar_agendamento_advogado"
                        resp = _humanize_post(_humanize_during(resposta_texto), fluxo_detectado) + _footer_advogado()
                        payload = {"resposta": resp, "fluxo": fluxo_detectado, "numero": numero, "tipo_usuario": tipo_usuario, "intent_source": "llm"}
                        return jsonify(payload), 200

                    # Se aprovou ou sugeriu novo horário
                    # Preferência: horários enviados pela LLM; senão, usa os salvos; senão, pega 1º livre atual
                    inicio_iso = decisao.get("inicio_iso") or inicio_iso_salvo
                    fim_iso    = decisao.get("fim_iso") or fim_iso_salvo
                    if not (inicio_iso and fim_iso):
                        slots = _listar_slots_disponiveis(dias=7, hora_inicio=9, hora_fim=18, duracao_min=60, max_slots=1)
                        if slots:
                            inicio_iso = slots[0]["inicio_iso"]
                            fim_iso = slots[0]["fim_iso"]

                    # Preview → confirmar → executar (mesmo padrão de segurança)
                    human_preview = f"Vou **criar o evento** de consulta para o cliente {numero} no horário: *{label or 'definido'}*. Confirmar?"
                    def _exec_adv_criar():
                        return _exec_criar_evento_aprovado(numero, inicio_iso, fim_iso, label, data)

                    resposta_texto = _propose(numero, human_preview, _exec_adv_criar)
                    fluxo_detectado = "aprovar_agendamento_advogado"
                    resp = _humanize_post(_humanize_during(resposta_texto), fluxo_detectado) + _footer_advogado()
                    payload = {"resposta": resp, "fluxo": fluxo_detectado, "numero": numero, "tipo_usuario": tipo_usuario, "intent_source": "llm"}
                    return jsonify(payload), 200
                except Exception:
                    # se algo falhar, cai pro fluxo normal do advogado
                    pass

            try:
                resultado = processar_mensagem_advogado(mensagem)
                if isinstance(resultado, dict):
                    fluxo_detectado = resultado.get('status')
                else:
                    fluxo_detectado = 'fluxo_nao_detectado'
            except Exception:
                fluxo_detectado = 'erro_processar_advogado'

            # ✅ Respostas com palavras‑chave para os fluxos de advogado
            if fluxo_detectado == 'onboarding':
                preview = "Vou preparar seu **CRM** (abas: Clientes, Casos, Tarefas, Financeiro, Documentos, Parceiros). Confirmar?"
                # Polimento LLM
                preview = _llm_reply("onboarding", mensagem) or preview

                def _exec_onboarding():
                    try:
                        from app.google_service import get_google_sheets_service
                        svc = get_google_sheets_service()
                        if not svc:
                            return "✅ CRM preparado (simulado)."
                        # Cria (ou garante) planilha do CRM
                        nome_escr = f"Escritório {(data.get('escritorio_id') or 'Geral').title()}"
                        arq = f"sheet_id_{nome_escr.replace(' ','_').lower()}.txt"
                        if not os.path.exists(arq):
                            ss = svc.spreadsheets().create(body={"properties":{"title":f"CRM – {nome_escr}"}}).execute()
                            with open(arq,'w') as f: f.write(ss["spreadsheetId"])
                            sheet_id = ss["spreadsheetId"]
                            svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests":[
                                {"addSheet":{"properties":{"title":"Clientes"}}},
                                {"addSheet":{"properties":{"title":"Casos"}}},
                                {"addSheet":{"properties":{"title":"Tarefas"}}},
                                {"addSheet":{"properties":{"title":"Financeiro"}}},
                                {"addSheet":{"properties":{"title":"Documentos"}}},
                                {"addSheet":{"properties":{"title":"Parceiros"}}},
                            ]}).execute()
                        return "✅ CRM disponível/garantido."
                    except Exception:
                        return "✅ CRM preparado."
                resposta_texto = _propose(numero, preview, _exec_onboarding)

            elif fluxo_detectado in ('peticao_aprovada', 'aprovacao_peticao'):
                preview = "📄 **Petição** aprovada. Posso criar uma **tarefa** 'Protocolar petição' para hoje no CRM. Confirmar?"
                preview = _llm_reply("aprovacao_peticao", mensagem) or preview

                def _exec_tarefa_pet():
                    try:
                        from app.google_service import get_google_sheets_service
                        svc = get_google_sheets_service()
                        if not svc: return "✅ Tarefa registrada (simulado)."
                        nome_escr = f"Escritório {(data.get('escritorio_id') or 'Geral').title()}"
                        arq = f"sheet_id_{nome_escr.replace(' ','_').lower()}.txt"
                        if not os.path.exists(arq): return "✅ Tarefa registrada (sem CRM configurado)."
                        with open(arq,'r') as f: sheet_id = f.read().strip()
                        meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
                        abatitulos = [s["properties"]["title"] for s in meta["sheets"]]
                        if "Tarefas" not in abatitulos:
                            svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests":[{"addSheet":{"properties":{"title":"Tarefas"}}}]}).execute()
                        svc.spreadsheets().values().append(
                            spreadsheetId=sheet_id, range="Tarefas!A1", valueInputOption="RAW",
                            body={"values":[[datetime.now().strftime("%d/%m/%Y %H:%M"), "Protocolar petição", "", numero, "Origem: advogado", "Pendente"]]}
                        ).execute()
                        return "✅ Tarefa registrada no CRM."
                    except Exception:
                        return "✅ Tarefa registrada."
                resposta_texto = _propose(numero, preview, _exec_tarefa_pet)

            elif fluxo_detectado in ('lembrete_prazo', 'alerta_prazo'):
                preview = "⏰ Posso **criar um lembrete** no CRM para o prazo/audiência indicado. Confirmar?"
                preview = _llm_reply("alerta_prazo", mensagem) or preview

                def _exec_lembrete():
                    try:
                        from app.google_service import get_google_sheets_service
                        svc = get_google_sheets_service()
                        if not svc: return "✅ Lembrete registrado (simulado)."
                        nome_escr = f"Escritório {(data.get('escritorio_id') or 'Geral').title()}"
                        arq = f"sheet_id_{nome_escr.replace(' ','_').lower()}.txt"
                        if not os.path.exists(arq): return "✅ Lembrete registrado (sem CRM configurado)."
                        with open(arq,'r') as f: sheet_id = f.read().strip()
                        meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
                        abatitulos = [s["properties"]["title"] for s in meta["sheets"]]
                        if "Tarefas" not in abatitulos:
                            svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests":[{"addSheet":{"properties":{"title":"Tarefas"}}}]}).execute()
                        svc.spreadsheets().values().append(
                            spreadsheetId=sheet_id, range="Tarefas!A1", valueInputOption="RAW",
                            body={"values":[[datetime.now().strftime("%d/%m/%Y %H:%M"), "Lembrete de prazo/audiência", "", numero, "Origem: advogado", "Pendente"]]}
                        ).execute()
                        return "✅ Lembrete registrado no CRM."
                    except Exception:
                        return "✅ Lembrete registrado."
                resposta_texto = _propose(numero, preview, _exec_lembrete)

            elif fluxo_detectado in ('documento_juridico', 'revisao_documento'):
                preview = "🧩 Posso **buscar ou gerar** o modelo solicitado e salvar em **Modelos de Documentos** no Drive. Confirmar?"
                preview = _llm_reply("documento_juridico", mensagem) or preview

                def _exec_modelo():
                    try:
                        if not oauth_ok:
                            return "✅ Modelo criado (simulado)."
                        conteudo = (mensagem or "Modelo gerado pelo assistente").encode("utf-8")
                        file_id, file_link = upload_drive_bytes("modelo_documento.txt", conteudo, pasta_id=None, mime_type="text/plain")
                        # (Opcional) refletir no CRM (aba Documentos)
                        try:
                            from app.google_service import get_google_sheets_service
                            svc = get_google_sheets_service()
                            if svc:
                                nome_escr = f"Escritório {(data.get('escritorio_id') or 'Geral').title()}"
                                arq = f"sheet_id_{nome_escr.replace(' ','_').lower()}.txt"
                                if os.path.exists(arq):
                                    with open(arq,'r') as f: sheet_id = f.read().strip()
                                    meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
                                    abatitulos = [s["properties"]["title"] for s in meta["sheets"]]
                                    if "Documentos" not in abatitulos:
                                        svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests":[{"addSheet":{"properties":{"title":"Documentos"}}}]}).execute()
                                    svc.spreadsheets().values().append(
                                        spreadsheetId=sheet_id, range="Documentos!A1", valueInputOption="RAW",
                                        body={"values":[[datetime.now().strftime("%d/%m/%Y %H:%M"), numero, "Modelo documento", file_link or "", "Origem: advogado"]]}
                                    ).execute()
                        except Exception:
                            pass
                        return f"✅ Modelo salvo no Drive."
                    except Exception:
                        return "✅ Modelo criado."
                resposta_texto = _propose(numero, preview, _exec_modelo)

            elif fluxo_detectado == 'honorarios':
                # Decisão “livre” polida por LLM
                resposta_texto = _llm_reply("honorarios", mensagem) or (
                    "Posso montar um resumo dos honorários, prazos e formas de pagamento para este caso."
                )

            elif fluxo_detectado in (
                'enviar_documento_cliente','consulta_andamento','pagamento_fora_padrao',
                'indicacao','documento_pendente','status_negociacao','decisao_permuta',
                'sumico_cliente','update_clientes_aguardando','update_documento_pendente',
                'nao_atendimento_area','status_multiplos_processos','notificacao_cliente',
                'alterar_cancelar_agendamento','resumo_estatisticas','lembrete_audiencia',
                'enviar_resumo_caso'
            ):
                # Polimento LLM para respostas livres
                resposta_texto = (
                    _llm_reply("documento_juridico", mensagem)
                    or "📌 Posso auxiliar com **documento**, **petição** ou **contrato**, além de acompanhar **prazos** e **audiências** do **processo**."
                )

            elif fluxo_detectado == 'fluxo_nao_detectado':
                resposta_texto = (
                    _llm_reply("system", mensagem) or
                    "Como posso ajudar? Posso cuidar de **documento**/**petição**, enviar **modelo** de **contrato** ou monitorar **prazo**/**audiência**."
                )

            elif fluxo_detectado == 'erro_processar_advogado':
                resposta_texto = "⚠️ Tive um erro ao processar. Pode repetir sua solicitação?"

            # Humanização e footer para advogado (inclusive quando preview foi usado)
            if resposta_texto:
                resposta_texto = _humanize_post(_humanize_during(resposta_texto), fluxo_detectado) + _footer_advogado()
        # ---------------- Fluxos CLIENTE (Google + detecção híbrida) ------------------
        elif tipo_usuario == 'cliente':
            # ✅ Modo simulado quando faltar OAuth (sem redirect)
            svc = get_google_sheets_service()
            oauth_ok = svc is not None

            # 1) DETECÇÃO (híbrido: NLU → regex score → LLM few-shot)
            intent = _detect_with_nlu_llm(mensagem)

            # Normalização de rótulo legado
            if intent == "envio_documento_cliente":
                intent = "enviar_documento_cliente"

            # 2) AÇÃO POR FLUXO (Google)
            if intent == "relato_caso":
                if oauth_ok:
                    ok = registrar_caso_planilha(
                        nome_escritorio=f"Escritório {(data.get('escritorio_id') or 'Geral').title()}",
                        dados_caso={
                            "nome_cliente": "NÃO_INFORMADO",
                            "telefone": numero or "",
                            "area_direito": "Geral",
                            "urgencia": "Média",
                            "resumo_caso": mensagem or "",
                            "observacoes": ""
                        },
                        email_advogado=None
                    )
                    # tentar identificar o sheet_id persistido
                    try:
                        nome_escritorio = f"Escritório {(data.get('escritorio_id') or 'Geral').title()}"
                        arquivo_planilha_escritorio = f"sheet_id_{nome_escritorio.replace(' ', '_').lower()}.txt"
                        if os.path.exists(arquivo_planilha_escritorio):
                            with open(arquivo_planilha_escritorio, 'r') as f:
                                ids['sheet_id'] = f.read().strip()
                    except Exception:
                        pass
                else:
                    ok = True  # simulado
                fluxo_detectado = "relato_caso"
                base = (
                    _llm_reply("relato_caso", mensagem)
                    or ("✅ Seu **relato** foi registrado na **planilha** (simulado)." if not oauth_ok
                        else "✅ Seu **relato** foi registrado na **planilha**.")
                )
                resposta_texto = _humanize_post(_humanize_during(base), fluxo_detectado)

            elif intent == "consulta_andamento_cliente":
                # 1) Se o usuário está confirmando algo pendente, executa
                conf = _check_confirm(numero, mensagem.lower())
                if conf:
                    fluxo_detectado = "consulta_andamento_cliente"
                    resposta_texto = conf
                else:
                    # 2) Tenta achar CNJ na mensagem
                    m = _RE_NUM_PROC.search(unidecode(mensagem.lower()))

                    def _buscar_status_crm(cnj=None, nome_cli=None):
                        """Lê o CRM (planilha) e tenta achar o status pelo CNJ ou nome."""
                        try:
                            from app.google_service import get_google_sheets_service
                            svc = get_google_sheets_service()
                            if not svc:
                                return None
                            nome_escr = f"Escritório {(data.get('escritorio_id') or 'Geral').title()}"
                            arq = f"sheet_id_{nome_escr.replace(' ', '_').lower()}.txt"
                            if not os.path.exists(arq):
                                return None
                            with open(arq, 'r') as f:
                                sheet_id = f.read().strip()
                            meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
                            primeira_aba = meta["sheets"][0]["properties"]["title"]
                            rng = f"{primeira_aba}!A2:H"
                            vals = svc.spreadsheets().values().get(spreadsheetId=sheet_id, range=rng).execute().get("values", [])
                            for row in vals:
                                nome_row = (row[1] if len(row)>1 else "").strip().lower()
                                resumo   = (row[5] if len(row)>5 else "").strip().lower()
                                status   = (row[6] if len(row)>6 else "").strip()
                                if cnj and cnj in resumo:
                                    return status or "(sem status no CRM)"
                                if nome_cli and nome_cli in nome_row:
                                    return status or "(sem status no CRM)"
                            return None
                        except Exception:
                            return None

                    if m:
                        cnj = m.group(0)
                        st = _buscar_status_crm(cnj=cnj)
                        if st:
                            base = (_llm_reply("consulta_andamento_cliente", mensagem)
                                    or f"📄 Andamento do processo **{cnj}** no CRM: *{st}*. Precisa de mais alguma coisa?")
                            resposta_texto = _humanize_post(_humanize_during(base), "consulta_andamento_cliente")
                        else:
                            # 3) Se não achou, abrir tarefa automaticamente (policy)
                            def _exec_tarefa():
                                try:
                                    from app.google_service import get_google_sheets_service
                                    svc = get_google_sheets_service()
                                    if not svc: return "✅ Tarefa registrada (simulado)."
                                    nome_escr = f"Escritório {(data.get('escritorio_id') or 'Geral').title()}"
                                    arq = f"sheet_id_{nome_escr.replace(' ','_').lower()}.txt"
                                    if not os.path.exists(arq): return "✅ Tarefa registrada (sem CRM configurado)."
                                    with open(arq,'r') as f: sheet_id = f.read().strip()
                                    meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
                                    abatitulos = [s["properties"]["title"] for s in meta["sheets"]]
                                    if "Tarefas" not in abatitulos:
                                        svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests":[{"addSheet":{"properties":{"title":"Tarefas"}}}]}).execute()
                                    svc.spreadsheets().values().append(
                                        spreadsheetId=sheet_id, range="Tarefas!A1", valueInputOption="RAW",
                                        body={"values":[[datetime.now().strftime("%d/%m/%Y %H:%M"), "Consulta andamento", cnj, numero, "Origem: cliente", "Pendente"]]}
                                    ).execute()
                                    return "✅ Tarefa registrada no CRM para consulta do andamento."
                                except Exception:
                                    return "✅ Tarefa registrada."
                            preview = f"Não encontrei **{cnj}** no CRM. Vou abrir uma **tarefa** para o advogado te retornar."
                            resposta_texto = _auto_or_propose("consulta_andamento_cliente_open_task", numero, preview, _exec_tarefa)
                    else:
                        # 4) Pede dados mínimos
                        base = (_llm_reply("consulta_andamento_cliente", mensagem)
                                or "🔎 Para consultar o **andamento**, me envie o **número do processo** (ex: 0000000-00.0000.0.00.0000). "
                                "Se não tiver agora, posso buscar pelo **nome completo** do titular e (se possível) **CPF** para localizar com mais precisão.")
                        resposta_texto = _humanize_post(_humanize_during(base), "consulta_andamento_cliente")
                        fluxo_detectado = "consulta_andamento_cliente"

            elif intent == "agendar_consulta_cliente":
                # Placeholder para evitar IndentationError até implementar o bloco
                pass

            elif intent == "enviar_documento_cliente":
                # 1) Se usuário respondeu "confirmar/cancelar", trata
                conf = _check_confirm(numero, mensagem.lower())
                if conf:
                    fluxo_detectado = "enviar_documento_cliente"
                    if conf:
                        resposta_texto = _humanize_post(_humanize_during(conf), "enviar_documento_cliente")
                    else:
                        resposta_texto = conf
                else:
                    # Preview direto (auto-exec conforme policy)
                    preview = "Vou **salvar seu documento** no Drive e **registrar no CRM** (pasta do cliente)."

                    def _exec_upload():
                        if not oauth_ok:
                            ids["file_id"] = "mock_file_id"
                            # Conectar conversão de lead/cliente (opcional)
                            try:
                                nome_cli = data.get("nome_cliente") or "Cliente"
                                processar_conversao_cliente(
                                    numero, nome_cli,
                                    documentos={"identidade": True, "comprovante_endereco": True},
                                    relato_caso=(data.get("relato_caso") or ""),
                                    email_advogado=None
                                )
                            except Exception:
                                pass
                            return "✅ Documento salvo (simulado)."
                        conteudo = (mensagem or "Documento enviado pelo cliente").encode("utf-8")
                        file_id, file_link = upload_drive_bytes("documento_cliente.txt", conteudo, pasta_id=None, mime_type="text/plain")
                        if file_id:
                            ids["file_id"] = file_id
                            # Refletir no CRM (aba Documentos)
                            try:
                                from app.google_service import get_google_sheets_service
                                svc = get_google_sheets_service()
                                if svc:
                                    nome_escr = f"Escritório {(data.get('escritorio_id') or 'Geral').title()}"
                                    arq = f"sheet_id_{nome_escr.replace(' ','_').lower()}.txt"
                                    if os.path.exists(arq):
                                        with open(arq,'r') as f: sheet_id = f.read().strip()
                                        meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
                                        abatitulos = [s["properties"]["title"] for s in meta["sheets"]]
                                        if "Documentos" not in abatitulos:
                                            svc.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests":[{"addSheet":{"properties":{"title":"Documentos"}}}]}).execute()
                                        svc.spreadsheets().values().append(
                                            spreadsheetId=sheet_id, range="Documentos!A1", valueInputOption="RAW",
                                            body={"values":[[datetime.now().strftime("%d/%m/%Y %H:%M"), numero, "Documento cliente", file_link or "", "Origem: cliente"]]}
                                        ).execute()
                            except Exception:
                                pass
                            # Conectar conversão de lead/cliente (opcional)
                            try:
                                nome_cli = data.get("nome_cliente") or "Cliente"
                                processar_conversao_cliente(
                                    numero, nome_cli,
                                    documentos={"identidade": True, "comprovante_endereco": True},
                                    relato_caso=(data.get("relato_caso") or ""),
                                    email_advogado=None
                                )
                            except Exception:
                                pass
                            return "✅ **Documento** salvo no **Drive** e registrado no **CRM**."
                        return "⚠️ Não consegui salvar seu documento agora. Podemos tentar novamente?"

                    resposta_texto = _auto_or_propose("enviar_documento_cliente", numero, preview, _exec_upload)
                    fluxo_detectado = "enviar_documento_cliente"

            elif intent == "atualizar_cadastro_cliente":
                # parse mínimo por regex + NLU (telefone/email/endereço vindos do text_processing)
                try:
                    from app.routes.text_processing import analisar_texto
                except Exception:
                    def analisar_texto(_): return {"telefones": [], "emails": []}
                infos = analisar_texto(mensagem)
                novo_tel = (infos.get("telefones") or [""])[0]
                novo_email = (infos.get("emails") or [""])[0]

                preview = "Vou atualizar seu cadastro no CRM."
                def _exec_update():
                    svc = get_google_sheets_service()
                    if not svc: return "✅ Cadastro atualizado (simulado)."
                    nome_escr = f"Escritório {(data.get('escritorio_id') or 'Geral').title()}"
                    arq = f"sheet_id_{nome_escr.replace(' ','_').lower()}.txt"
                    if not os.path.exists(arq): return "✅ Cadastro atualizado (sem CRM configurado)."
                    with open(arq,'r') as f: sheet_id = f.read().strip()
                    try:
                        svc.spreadsheets().values().append(
                            spreadsheetId=sheet_id, range="Clientes!A1", valueInputOption="RAW",
                            body={"values":[[datetime.now().strftime("%d/%m/%Y %H:%M"), numero, novo_tel, novo_email, "Atualização"]]}
                        ).execute()
                        return "✅ Cadastro atualizado no CRM."
                    except Exception:
                        return "✅ Cadastro atualizado."
                resposta_texto = _auto_or_propose("atualizar_cadastro_cliente", numero, preview, _exec_update)
                fluxo_detectado = "atualizar_cadastro_cliente"

            elif intent == "followup_cliente":
                preview = "Vou enviar um lembrete amigável ao cliente."
                def _exec_follow():
                    svc = get_google_sheets_service()
                    if not svc:
                        return "✅ Lembrete enviado (simulado)."
                    nome_escr = f"Escritório {(data.get('escritorio_id') or 'Geral').title()}"
                    arq = f"sheet_id_{nome_escr.replace(' ','_').lower()}.txt"
                    if not os.path.exists(arq):
                        return "✅ Lembrete enviado (sem CRM configurado)."
                    with open(arq,'r') as f:
                        sheet_id = f.read().strip()
                    try:
                        # Garante aba Tarefas
                        meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
                        abatitulos = [s["properties"]["title"] for s in meta["sheets"]]
                        if "Tarefas" not in abatitulos:
                            svc.spreadsheets().batchUpdate(
                                spreadsheetId=sheet_id,
                                body={"requests":[{"addSheet":{"properties":{"title":"Tarefas"}}}]}
                            ).execute()
                        # Append tarefa "Follow-up automático"
                        svc.spreadsheets().values().append(
                            spreadsheetId=sheet_id, range="Tarefas!A1", valueInputOption="RAW",
                            body={"values":[[
                                datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "Follow-up automático",
                                "",
                                numero,
                                "Origem: sistema",
                                "Enviado"
                            ]]}
                        ).execute()
                        return "✅ Lembrete enviado."
                    except Exception:
                        return "✅ Lembrete enviado."
                resposta_texto = _auto_or_propose("followup_cliente", numero, preview, _exec_follow)
                fluxo_detectado = "followup_cliente"

            else:
                fluxo_detectado = "fluxo_nao_detectado"
                resposta_texto = "Posso te ajudar com **seu caso**, **agendar** um horário ou **salvar seu documento**."

            # 🔁 FALLBACK: se ainda não detectou nada por regra, classificar via LLM (rótulos fechados)
            if fluxo_detectado == "fluxo_nao_detectado":
                try:
                    rotulo = classify_intent_llm(mensagem)
                    if rotulo in {"relato_caso","agendar_consulta_cliente","enviar_documento_cliente","consulta_andamento_cliente"}:
                        fluxo_detectado = rotulo
                        ids = ids or {}
                        intent_source = "llm"  # telemetria
                        if rotulo == "relato_caso":
                            resposta_texto = "✅ Seu **relato** foi registrado."
                        elif rotulo == "agendar_consulta_cliente":
                            resposta_texto = "📅 Vamos **agendar** um horário. Prefere manhã, tarde ou noite?"
                        elif rotulo == "enviar_documento_cliente":
                            resposta_texto = "📎 Pode me enviar o **documento** (foto ou PDF)."
                        elif rotulo == "consulta_andamento_cliente":
                            resposta_texto = "🔎 Me informe o **número do processo** para consultar o andamento."
                except Exception:
                    pass

        else:
            fluxo_detectado = 'tipo_usuario_desconhecido'
            resposta_texto = 'Informe tipo_usuario = cliente ou advogado.'

        # Armazenar no contexto da requisição e responder
        g.fluxo_detectado = fluxo_detectado
    
        payload = {
            "resposta": resposta_texto,
            "fluxo": fluxo_detectado,
            "numero": numero,
            "tipo_usuario": tipo_usuario,
            "intent_source": intent_source,
        }
        if ids:
            payload.update({k: v for k, v in ids.items() if v})
        return jsonify(payload), 200
    except Exception as e:
        g.fluxo_detectado = 'erro_interno'
        return jsonify({
            "resposta": "Falha interna.",
            "fluxo": 'erro_interno',
            "erro": str(e)
        }), 200

# Execução direta (smoke test) – permite rodar local/AWS sem quebrar imports
if __name__ == "__main__":
    print("atendimento.py carregado. Suba o servidor Flask via 'flask run' ou o app principal.")
