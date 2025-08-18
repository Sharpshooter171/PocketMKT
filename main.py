from flask import Flask
from flask_cors import CORS
import os

# ==== Auto-start do painel (app/painel/painel.py) ====
import subprocess, sys, time, socket, os
from pathlib import Path

def _port_open(host, port):
    try:
        with socket.socket() as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def start_painel_if_needed():
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
    # Backend padrão: 127.0.0.1:5000 (ajuste se seu backend usa outra porta)
    env.setdefault("BACKEND_BASE_URL", f"http://127.0.0.1:{int(env.get('FLASK_PORT', '5000'))}")
    log_dir = project_root / "logs"; log_dir.mkdir(exist_ok=True)
    log_fp = open(log_dir / "painel.log", "a", buffering=1)
    print(f"[painel] iniciando {painel_script} ...")
    subprocess.Popen([sys.executable, str(painel_script)], cwd=str(project_root), env=env,
                     stdout=log_fp, stderr=log_fp)
    # espera até subir
    for _ in range(40):
        if _port_open(host, port):
            print(f"[painel] ON em http://{host}:{port}/painel")
            break
        time.sleep(0.25)
# ==== FIM bloco painel ====


from dotenv import load_dotenv
load_dotenv()  # antes dos imports que usam as envs

# Imports dos blueprints/serviços
from app.routes.atendimento import atendimento_bp  # import explícito do blueprint

try:
    from app.google_service import google_bp
except ImportError:
    google_bp = None  # blueprint opcional

try:
    from app.database_service import init_db
except ImportError:
    def init_db():
        print("⚠️ init_db não disponível (import falhou)")

# Importa integração Twilio (Webhook)
try:
    from app.twilio_webhook import twilio_bp
except ImportError:
    twilio_bp = None  # blueprint opcional


print("🚀 Iniciando main.py do PocketMKT...")


def create_app():
    """Factory para criar a aplicação Flask (permite testes e múltiplas instâncias)."""
    app = Flask(__name__)

    # Chave secreta: usar variável de ambiente em produção
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "mude-para-uma-chave-segura")

    # CORS global
    CORS(app)

    # Inicialização do banco (idempotente)
    init_db()

    # Registro dos blueprints
    app.register_blueprint(atendimento_bp)  # opcional: url_prefix="/api"
    if google_bp:
        app.register_blueprint(google_bp)
    if twilio_bp:
        app.register_blueprint(twilio_bp)


    @app.route("/")
    def home():  # noqa: D401
        return "Servidor Flask do PocketMKT está rodando (application factory)!"

    return app



# Execução direta
if __name__ == "__main__":
    app = create_app()
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    print(f"🔄 Inicializando servidor Flask em {host}:{port} (debug={debug_mode})...")
    start_painel_if_needed()
    app.run(host=host, port=port, debug=debug_mode)
    print("🛑 Servidor Flask finalizado.")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    print(f"🔄 Inicializando servidor Flask em {host}:{port} (debug={debug_mode})...")
    start_painel_if_needed()
    app.run(host=host, port=port, debug=debug_mode)
    print("🛑 Servidor Flask finalizado.")
