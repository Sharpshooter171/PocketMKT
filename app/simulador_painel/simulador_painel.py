from flask import Flask, render_template_string, request, jsonify, redirect
import requests
import os

# .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = Flask(__name__)

# ===== Config via .env =====
# Ex.: BACKEND_BASE_URL="http://127.0.0.1:5000"  (seu backend principal)
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
PANEL_HOST = os.getenv("PANEL_HOST", "0.0.0.0")
PANEL_PORT = int(os.getenv("PANEL_PORT", os.getenv("PORT", "8000")))

# Endpoints do backend
PROMPT_CONFIG_URL = f"{BACKEND_BASE_URL}/prompt_config"
STATUS_URL        = f"{BACKEND_BASE_URL}/status"

# Carrega o HTML do painel
BASE_DIR = os.path.dirname(__file__)
PAINEL_HTML_PATH = os.path.join(BASE_DIR, "painel.html")
with open(PAINEL_HTML_PATH, "r", encoding="utf-8") as f:
    PANEL_HTML = f.read()

print("⚖️ PocketMKT - Painel MVP (WhatsApp/Twilio)")
print("=" * 60)
print(f"🔗 Backend: {BACKEND_BASE_URL}")
print(f"🌐 Painel:  http://{PANEL_HOST}:{PANEL_PORT}/painel")
print("=" * 60)

@app.route("/")
def root():
    return redirect("/painel", code=302)

@app.route("/painel")
def painel():
    # injeta BACKEND_BASE_URL no HTML (para status e debug)
    return render_template_string(PANEL_HTML, BACKEND_BASE_URL=BACKEND_BASE_URL)

# Proxy de prompt_config (GET/POST) para o backend (mantido p/ compatibilidade)
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

# Status do painel + ping no backend /status (usado pelo front p/ Debug)
@app.route("/status", methods=["GET"])
def status():
    try:
        r = requests.get(STATUS_URL, timeout=8)
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
    print("\n🚀 Iniciando Painel PocketMKT (MVP WhatsApp/Twilio)...")
    print(f"   Acesse: http://{PANEL_HOST}:{PANEL_PORT}/painel")
    app.run(host=PANEL_HOST, port=PANEL_PORT, debug=True)
