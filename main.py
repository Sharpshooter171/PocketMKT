import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from flask import Flask

# Blueprints principais (sem prefixos)
from app.routes.atendimento import atendimento_bp
try:
    from app.google_service import google_bp  # /authorize, /oauth2callback
except Exception:
    google_bp = None  # opcional

# Twilio (Webhook) opcional
try:
    from app.twilio_webhook import twilio_bp
except Exception:
    twilio_bp = None  # opcional

# CORS opcional (não adiciona dependências; habilita se instalado)
try:
    from flask_cors import CORS
except Exception:
    CORS = None

# init_db opcional; não logar erro se indisponível
try:
    from app.db import init_db  # se existir
except Exception:
    init_db = None


def _port_open(host, port):
    try:
        with socket.socket() as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def start_painel_if_needed():
    """Inicia o painel localmente apenas em execução direta (simplifica DX)."""
    host = "127.0.0.1"
    port = int(os.getenv("PANEL_PORT", "8000"))
    if _port_open(host, port):
        print(f"[painel] já está rodando em {host}:{port}")
        return
    project_root = Path(__file__).resolve().parent
    painel_script = project_root / "app" / "painel" / "painel.py"
    if not painel_script.exists():
        print(f"[painel] ERRO: {painel_script} não encontrado"); return
    env = os.environ.copy()
    env.setdefault("BACKEND_BASE_URL", f"http://127.0.0.1:{os.getenv('FLASK_RUN_PORT','5000')}")
    log_dir = project_root / "logs"; log_dir.mkdir(exist_ok=True)
    log_fp = open(log_dir / "painel.log", "a", buffering=1)
    print(f"[painel] iniciando {painel_script} ...")
    subprocess.Popen([sys.executable, str(painel_script)], cwd=str(project_root), env=env,
                     stdout=log_fp, stderr=log_fp)
    for _ in range(40):
        if _port_open(host, port):
            print(f"[painel] ON em http://{host}:{port}/painel")
            break
        time.sleep(0.25)


def create_app():
    """Factory para criar a aplicação Flask (permite testes e múltiplas instâncias)."""
    app = Flask(__name__)

    # Secret por ambiente (segurança)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "mude-para-uma-chave-segura")

    # CORS global opcional
    if CORS:
        CORS(app)

    # Inicialização do banco (idempotente), se disponível
    if init_db:
        try:
            init_db()
        except Exception:
            pass  # não interromper bootstrap

    # Registro dos blueprints (sem prefixo)
    app.register_blueprint(atendimento_bp)  # /processar_atendimento
    if google_bp:
        app.register_blueprint(google_bp)   # /authorize, /oauth2callback
    if twilio_bp:
        app.register_blueprint(twilio_bp)   # Webhook WhatsApp (opcional)

    @app.route("/")
    def home():
        return "Servidor Flask do PocketMKT está rodando!"

    return app


# ✅ app disponível no escopo do módulo (importável por gunicorn/testes/snippets)
app = create_app()


# Execução direta: inicia painel e Flask
if __name__ == "__main__":
    print("🚀 Iniciando main.py do PocketMKT...")
    start_painel_if_needed()  # só em execução direta
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    app.run(host=host, port=port, debug=debug_mode)
    print("🛑 Servidor Flask finalizado.")
