import os, requests
from flask import Blueprint, request, Response
from twilio.twiml.messaging_response import MessagingResponse

twilio_bp = Blueprint("twilio", __name__)

BACKEND_INTERNAL_URL = os.getenv("BACKEND_INTERNAL_URL", "http://127.0.0.1:5000").rstrip("/")
PROCESSAR_URL = f"{BACKEND_INTERNAL_URL}/processar_atendimento"

@twilio_bp.route("/twilio/webhook", methods=["POST"])
def webhook():
    body = (request.values.get("Body") or "").strip()
    from_number = request.values.get("From") or ""
    payload = {"mensagem": body, "numero": from_number, "tipo_usuario": "cliente"}
    try:
        r = requests.post(PROCESSAR_URL, json=payload, timeout=25)
        resposta = r.json().get("resposta") if r.ok else None
    except Exception:
        resposta = None
    texto = resposta or "Tive um problema agora. Pode repetir em instantes?"
    resp = MessagingResponse()
    resp.message(texto)
    return Response(str(resp), mimetype="application/xml")
