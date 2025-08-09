import os
import json
from flask import Blueprint, redirect, url_for, session, request

# Handle optional Google API dependencies
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import Flow
    GOOGLE_APIS_AVAILABLE = True
    print("✅ Google APIs disponíveis")
except ImportError:
    print("⚠️ Google APIs não instaladas, funcionalidades simuladas")
    Credentials = None
    build = None
    Flow = None
    GOOGLE_APIS_AVAILABLE = False

# Cria um Blueprint para o serviço do Google
google_bp = Blueprint('google', __name__)

# ⚠️ MESMO SCOPES E REDIRECT_URI do PocketMKT.py
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar"
]
REDIRECT_URI = "http://127.0.0.1:5000/oauth2callback"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

print("📊 Carregando serviço de integração com Google Sheets...")

def get_google_sheets_service():
    print("📊 Chamando get_google_sheets_service()...")
    
    if not GOOGLE_APIS_AVAILABLE:
        print("⚠️ Google APIs não disponíveis, retornando serviço simulado")
        return None
    # ⚠️ Helpers não devem redirecionar. Se faltar credencial, devolve None.
    if not os.path.exists("oauth_credentials.json"):
        print("🔐 Primeira autenticação necessária (oauth_credentials.json ausente)")
        return None  # nunca redirecionar em helpers

    with open("oauth_credentials.json", "r") as f:
        creds_data = json.load(f)
    creds = Credentials(**creds_data)

    if creds.expired and creds.refresh_token:
        try:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        except ImportError:
            print("⚠️ Google auth transport não disponível")
            return None
        with open("oauth_credentials.json", "w") as f:
            json.dump({
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
            }, f)

    return build("sheets", "v4", credentials=creds)

# --- Novos helpers reutilizando as mesmas credenciais (não altera fluxo OAuth existente) ---
def _load_creds_or_redirect():
    # Ajustado: nunca retornar redirect aqui; helpers devem retornar None quando faltar credenciais
    if not GOOGLE_APIS_AVAILABLE:
        return None
    if not os.path.exists("oauth_credentials.json"):
        return None
    try:
        with open("oauth_credentials.json", "r") as f:
            creds_data = json.load(f)
        creds = Credentials(**creds_data)
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            with open("oauth_credentials.json", "w") as f:
                json.dump({
                    "token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "token_uri": creds.token_uri,
                    "client_id": creds.client_id,
                    "client_secret": creds.client_secret,
                    "scopes": creds.scopes,
                }, f)
        return creds
    except Exception as e:
        print(f"⚠️ Falha ao carregar/atualizar credenciais: {e}")
        return None

def get_google_calendar_service():
    """Retorna service Calendar v3 usando as mesmas credenciais do Sheets."""
    creds = _load_creds_or_redirect()
    if not creds:
        return None
    try:
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Erro ao criar serviço Calendar: {e}")
        return None

def get_gmail_service():
    """Retorna service Gmail v1 (envio de emails)."""
    creds = _load_creds_or_redirect()
    if not creds:
        return None
    try:
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        print(f"❌ Erro ao criar serviço Gmail: {e}")
        return None

def get_google_drive_service():
    """Retorna service Drive v3 limitado ao escopo drive.file."""
    creds = _load_creds_or_redirect()
    if not creds:
        return None
    try:
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Erro ao criar serviço Drive: {e}")
        return None

def buscar_ou_criar_planilha():
    print("📊 Buscando ou criando planilha...")
    if not GOOGLE_APIS_AVAILABLE:
        print("⚠️ Google APIs não disponíveis, simulando planilha")
        return "mock_sheet_id_12345"
        
    if os.path.exists("sheet_id.txt"):
        return open("sheet_id.txt").read().strip()
    sheet_id = criar_planilha_google_api()
    if sheet_id:
        with open("sheet_id.txt", "w") as f:
            f.write(sheet_id)
    return sheet_id

def criar_planilha_google_api():
    print("📊 Criando nova planilha no Google Sheets...")
    
    if not GOOGLE_APIS_AVAILABLE:
        print("⚠️ Google APIs não disponíveis, simulando criação de planilha")
        return "mock_sheet_id_12345"
    
    service = get_google_sheets_service()
    if not service:
        return None
    try:
        spreadsheet = {'properties': {'title': 'Leads'}}
        created = service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId,sheets.properties'
        ).execute()

        sheet_id = created.get('spreadsheetId')
        first_sheet = created['sheets'][0]['properties']['title']
        print(f"✅ Planilha criada: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
        print(f"🔖 Aba padrão detectada: {first_sheet}")

        header_range = f"{first_sheet}!A1:F1"
        header_body = {
            "values": [["Nome", "Telefone", "Mensagem", "Classificação", "Necessidade", "Status"]]
        }
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=header_range,
            valueInputOption="RAW",
            body=header_body
        ).execute()
        print("✅ Cabeçalho criado na planilha.")

        drive = build("drive", "v3", credentials=service._http.credentials) if GOOGLE_APIS_AVAILABLE else None
        if drive:
            drive.permissions().create(
                fileId=sheet_id,
                body={"type": "anyone", "role": "writer"},
                fields="id"
            ).execute()
            print("🌐 Planilha compartilhada para edição pública.")
        else:
            print("⚠️ Drive API não disponível, não foi possível compartilhar planilha")

        return sheet_id

    except Exception as e:
        print(f"❌ Erro ao criar planilha: {e}")
        return None

def verificar_cliente_existente_google_api(telefone):
    print(f"📊 Verificando se cliente com telefone {telefone} já existe...")
    
    if not GOOGLE_APIS_AVAILABLE:
        print("⚠️ Google APIs não disponíveis, simulando verificação")
        return False
    
    service = get_google_sheets_service()
    if not service:
        print("🔐 Sem serviço Sheets. Autentique em /authorize.")
        return False  # nunca retornar redirect em helpers

    sheet_id = buscar_ou_criar_planilha()
    if not sheet_id:
        print("❌ Não foi possível obter sheet_id")
        return False

    try:
        meta = service.spreadsheets().get(
            spreadsheetId=sheet_id,
            fields="sheets.properties"
        ).execute()
        first_sheet = meta['sheets'][0]['properties']['title']
        print(f"🔖 Verificando na aba: {first_sheet}")

        range_ = f"{first_sheet}!A:F"
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_
        ).execute()
        values = result.get('values', [])
        for row in values:
            if len(row) > 1 and str(row[1]).strip() == telefone:
                return True
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar cliente via API oficial: {e}")
        return False

def registrar_lead_google_api(nome, telefone, mensagem, classificacao, necessidade, status):
    print("📊 Registrando lead via Google Sheets API...")
    
    if not GOOGLE_APIS_AVAILABLE:
        print("⚠️ Google APIs não disponíveis, simulando registro")
        print(f"📝 MOCK: Registrando lead: {nome} ({telefone}) - {necessidade}")
        return True
    
    service = get_google_sheets_service()
    if not service:
        print("🔐 Sem serviço Sheets. Autentique em /authorize.")
        return False  # nunca retornar redirect em helpers

    sheet_id = buscar_ou_criar_planilha()
    if not sheet_id:
        print("❌ Não foi possível obter sheet_id")
        return

    meta = service.spreadsheets().get(
        spreadsheetId=sheet_id,
        fields="sheets.properties"
    ).execute()
    first_sheet = meta['sheets'][0]['properties']['title']
    print(f"🔖 Usando aba: {first_sheet}")

    append_range = f"{first_sheet}!A:F"
    body = {"values": [[nome, telefone, mensagem, classificacao, necessidade, status]]}

    try:
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=append_range,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        print("✅ Lead registrado via Google Sheets API.")
    except Exception as e:
        print(f"❌ Erro ao registrar lead via API: {e}")

# === Helpers adicionais reutilizando mesmas credenciais (Sheets) ===

def _creds_from_sheets_service():
    """Reaproveita as mesmas credenciais usadas pelo Sheets."""
    try:
        s = get_google_sheets_service()
        return getattr(s._http, "credentials", None) if s else None
    except Exception:
        return None

def criar_evento_calendar(titulo, inicio_iso, fim_iso, convidados_emails=None, descricao=None, timezone="America/Sao_Paulo"):
    if not GOOGLE_APIS_AVAILABLE:
        print("⚠️ Calendar não disponível, simulando evento")
        return "mock_event_id", "https://calendar.google.com"
    creds = _creds_from_sheets_service()
    if not creds:
        print("❌ Sem credenciais para Calendar")
        return None, None
    service = build("calendar", "v3", credentials=creds)
    body = {
        "summary": titulo,
        "description": descricao or "",
        "start": {"dateTime": inicio_iso, "timeZone": timezone},
        "end": {"dateTime": fim_iso, "timeZone": timezone},
        "reminders": {"useDefault": True}
    }
    if convidados_emails:
        body["attendees"] = [{"email": e} for e in convidados_emails]
    ev = service.events().insert(calendarId="primary", body=body).execute()
    return ev.get("id"), ev.get("htmlLink")

def enviar_email_gmail(para, assunto, texto):
    if not GOOGLE_APIS_AVAILABLE:
        print(f"⚠️ Gmail não disponível, simulando envio para {para}")
        return "mock_email_id"
    from email.mime.text import MIMEText
    import base64
    creds = _creds_from_sheets_service()
    if not creds:
        print("❌ Sem credenciais para Gmail")
        return None
    gmail = build("gmail", "v1", credentials=creds)
    msg = MIMEText(texto, "plain", "utf-8")
    msg["to"] = para
    msg["subject"] = assunto
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    sent = gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
    return sent.get("id")

def upload_drive_bytes(nome_arquivo, conteudo_bytes, pasta_id=None, mime_type="application/octet-stream"):
    if not GOOGLE_APIS_AVAILABLE:
        print(f"⚠️ Drive não disponível, simulando upload: {nome_arquivo}")
        return "mock_file_id", "https://drive.google.com"
    from googleapiclient.http import MediaIoBaseUpload
    import io
    creds = _creds_from_sheets_service()
    if not creds:
        print("❌ Sem credenciais para Drive")
        return None, None
    drive = build("drive", "v3", credentials=creds)
    metadata = {"name": nome_arquivo}
    if pasta_id:
        metadata["parents"] = [pasta_id]
    media = MediaIoBaseUpload(io.BytesIO(conteudo_bytes), mimetype=mime_type, resumable=False)
    f = drive.files().create(body=metadata, media_body=media, fields="id,webViewLink").execute()
    return f.get("id"), f.get("webViewLink")

# Rotas 
@google_bp.route("/authorize")
def authorize():
    if not GOOGLE_APIS_AVAILABLE:
        return "⚠️ Google APIs não disponíveis. Instale as dependências: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
    
    flow = Flow.from_client_secrets_file(
        "credentials.json", scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    # Forçar nova tela de consentimento e não unir escopos previamente concedidos
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="false",  # evita união automática de escopos antigos com novos
        prompt="consent",                # força tela de consentimento
    )
    session["state"] = state
    print("🔗 Redirecionando para:", authorization_url)
    return redirect(authorization_url)

@google_bp.route("/oauth2callback")
def oauth2callback():
    if not GOOGLE_APIS_AVAILABLE:
        return "⚠️ Google APIs não disponíveis. Instale as dependências: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
    
    state = session.get("state")
    flow = Flow.from_client_secrets_file(
        "credentials.json", scopes=SCOPES, state=state, redirect_uri=REDIRECT_URI
    )
    # Passa escopos explicitamente para ajudar oauthlib a validar/normalizar
    flow.fetch_token(
        authorization_response=request.url,
        scope=" ".join(SCOPES)
    )

    creds = flow.credentials
    session["credentials"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    with open("oauth_credentials.json", "w") as f:
        json.dump(session["credentials"], f)
    print("✅ Autenticação concluída com sucesso!")
    return "Autenticação concluída. Pode voltar ao app."