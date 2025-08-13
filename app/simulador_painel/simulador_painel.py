from flask import Flask, render_template_string, request, jsonify, redirect
import requests
import os
from datetime import datetime

# .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = Flask(__name__)

# ===== Config via .env =====
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
PANEL_HOST = os.getenv("PANEL_HOST", "0.0.0.0")
PANEL_PORT = int(os.getenv("PANEL_PORT", os.getenv("PORT", "8000")))

# Endpoints do backend
PROMPT_CONFIG_URL = f"{BACKEND_BASE_URL}/prompt_config"
PROCESSAR_URL     = f"{BACKEND_BASE_URL}/processar_atendimento"
STATUS_URL        = f"{BACKEND_BASE_URL}/status"

# Carrega o HTML do painel
BASE_DIR = os.path.dirname(__file__)
PAINEL_HTML_PATH = os.path.join(BASE_DIR, "painel.html")
with open(PAINEL_HTML_PATH, "r", encoding="utf-8") as f:
    PANEL_HTML = f.read()

print("⚖️ PocketMKT - Painel do Advogado MVP")
print("=" * 50)
print(f"🔗 Conectando ao Backend: {BACKEND_BASE_URL}")
print(f"🌐 Painel: http://{PANEL_HOST}:{PANEL_PORT}/painel")
print("=" * 50)

@app.route("/painel")
def painel():
    # injeta BACKEND_BASE_URL no HTML (para botão de login Google etc.)
    return render_template_string(PANEL_HTML, BACKEND_BASE_URL=BACKEND_BASE_URL)

# (Opcional) rota de conveniência: redireciona para o authorize do backend
@app.route("/google/auth")
def google_auth():
    return redirect(f"{BACKEND_BASE_URL}/authorize", code=302)

# Proxy de prompt_config (GET/POST) para o backend
@app.route("/prompt_config", methods=["GET", "POST"])
def prompt_config_route():
    try:
        if request.method == "GET":
            r = requests.get(PROMPT_CONFIG_URL, timeout=10)
        else:
            r = requests.post(PROMPT_CONFIG_URL, json=(request.get_json() or {}), timeout=10)
        return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type", "application/json")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Envia mensagem para o backend central (rota oficial /processar_atendimento)
@app.route("/enviar", methods=["POST"])
def enviar():
    data = request.get_json(force=True) or {}
    payload = {
        "mensagem": data.get("mensagem", ""),
        "numero": data.get("numero"),
        "tipo_usuario": data.get("tipo_usuario", "cliente"),
        "escritorio_id": data.get("escritorio_id"),
    }
    try:
        r = requests.post(PROCESSAR_URL, json=payload, timeout=30)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"erro": "backend_offline", "detalhe": str(e)}), 502

# Status do painel + ping no backend /status
@app.route("/status", methods=["GET"])
def status():
    try:
        r = requests.get(STATUS_URL, timeout=5)
        ok = r.status_code == 200
        body = r.json() if ok else {"code": r.status_code}
        return jsonify({
            "panel": "OK",
            "backend_url": BACKEND_BASE_URL,
            "backend_status": body
        }), 200
    except Exception as e:
        return jsonify({
            "panel": "OK",
            "backend_url": BACKEND_BASE_URL,
            "backend_status": "Desconectado",
            "erro": str(e)
        }), 200

if __name__ == "__main__":
    print("\n🚀 Iniciando Painel do Advogado PocketMKT MVP...")
    print(f"🌐 Acesse o painel: http://{PANEL_HOST}:{PANEL_PORT}/painel")
    print(f"🔧 Endpoint de status: http://{PANEL_HOST}:{PANEL_PORT}/status")
    print("=" * 50)
    app.run(host=PANEL_HOST, port=PANEL_PORT, debug=True)
