from flask import Flask
from flask_cors import CORS
import os

from dotenv import load_dotenv
load_dotenv()  # antes dos imports que usam as envs


# Imports dos blueprints/serviços
try:
    from app.routes.atendimento import atendimento_bp  # caminho atual do blueprint
except ImportError:
    # fallback caso o usuário mova para app.atendimento no futuro
    from app.atendimento import atendimento_bp  # type: ignore

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
    app.register_blueprint(atendimento_bp)
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
    app.run(host=host, port=port, debug=debug_mode)
    print("🛑 Servidor Flask finalizado.")
