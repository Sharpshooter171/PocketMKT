# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, jsonify, redirect
import requests
import os
from pathlib import Path

# .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ===== Instrução longa para o painel (será injetada no HTML) =====
INSTRUCAO_TESTE_ASSISTENTE = """
📚 GUIA DE TESTES DO ASSISTENTE (MVP)

Este guia resume os principais fluxos implementados no backend (atendimento.py) e como validar cada um antes do MVP com os advogados.

Conecte seu Google (Sheets/Drive/Calendar/Gmail) pelo botão “Conectar Google”. Depois, use o WhatsApp (Twilio Sandbox) para conversar com o assistente. O painel mostra status e logs no Debug.

O que o assistente faz por trás (quando Google está conectado):
• CRM (Google Sheets): cria/garante planilhas por escritório e registra Casos, Tarefas, Clientes e Documentos.
• Drive: cria pastas por cliente (ex.: “Jorge Caldas”) e salva documentos na pasta correta; registra na aba Documentos do CRM.
• Calendar: cria eventos de consulta após aprovação do advogado.
• Gmail: envia emails (quando implementado em certos fluxos).
• Twilio (Sandbox): recebe mensagens do WhatsApp; webhook do backend processa o fluxo.

FLUXOS DO CLIENTE (tipo_usuario=cliente)
1) Saudação inicial
   - Ex.: “Olá, tudo bem?”
   - Esperado: resposta cordial e convite à triagem (“nome completo” e motivo).

2) Relato de caso (registra no CRM)
   - Ex.: “Fui demitido sem justa causa e preciso entender meus direitos.”
   - Esperado: registra o relato na planilha do escritório, aba principal (com data, nome, telefone, área, urgência, resumo).

3) Consulta de andamento do processo
   - Com número: “Quero o andamento do processo 0000000-00.0000.0.00.0000”
     • Tenta encontrar no CRM e retorna o status.
   - Sem número: “Quero saber o andamento do meu processo”
     • Abre automaticamente uma tarefa no CRM para o advogado retornar.

4) Enviar documento (Drive + CRM)
   - Ex.: “Segue anexo meu RG e comprovante de endereço.”
   - Esperado: cria/usa a pasta do cliente no Drive e salva o documento; registra na aba Documentos da planilha.
   - Observação: o backend também aceita upload binário via campo arquivo_base64/media_url no JSON (para testes automatizados/E2E).

5) Atualizar cadastro (Clientes)
   - Ex.: “Troquei de telefone: (11) 99999-1234 e meu e-mail é teste@exemplo.com”
   - Esperado: insere/atualiza linha na aba Clientes (telefone/email e marcação “Atualização”).

6) Follow-up automático (quando disponível)
   - Ex.: “Poderia me lembrar amanhã?”
   - Esperado: registra uma tarefa “Follow-up automático” no CRM.

FLUXOS DO ADVOGADO (tipo_usuario=advogado)
A) Aprovar/Recusar/Sugerir horário de agendamento
   - Ex.: “Pode aprovar o pedido do cliente C5”
     • Esperado: o assistente prepara preview e, após “confirmar”, cria evento no Calendar e marca a tarefa como “Aprovado”.
   - Ex.: “Sem agenda essa semana, melhor recusar”
     • Esperado: marca como “Recusado”.
   - Ex.: “Prefiro amanhã às 10h”
     • Esperado: sugere horário; ao confirmar, cria evento.

B) Onboarding e preparação de CRM
   - Ex.: “Quero configurar meu CRM (onboarding)”
     • Esperado: prepara/garante planilha CRM com abas (Clientes, Casos, Tarefas, Financeiro, Documentos, Parceiros).

C) Lembretes de prazos/audiências (Tarefas)
   - Ex.: “Preciso registrar um lembrete de prazo para amanhã às 14h”
     • Esperado: cria tarefa no CRM (“Lembrete de prazo/audiência”).

D) Documento/Modelo jurídico
   - Ex.: “Preciso de um modelo de contrato de prestação de serviços”
     • Esperado: cria arquivo no Drive e registra na aba Documentos (quando aplicável).

E) Outros fluxos suportados
   - Honorários, revisão de documento, documento pendente, sumiço de cliente, notificação ao cliente, alterar/cancelar agendamento, resumo/estatísticas etc. (respostas polidas; quando aplicável, registram Tarefas/Documentos).

Como testar
1) Conecte o Google e valide o status no painel (Debug → Atualizar).
2) Envie mensagens pelo WhatsApp (Twilio Sandbox) simulando os exemplos acima.
3) Verifique efeitos no CRM (Sheets), arquivos no Drive (pasta do cliente) e eventos no Calendar.
4) Exporte o JSON de debug pelo painel ao final e envie para a equipe.

Observações
• O assistente evita aconselhamento jurídico. Ele organiza, agenda e encaminha.
• Upload binário real pode ser feito via arquivo_base64/media_url (testes automáticos/integração).
• Se algo não funcionar, verifique as permissões do Google e o status do backend no painel.
"""

app = Flask(__name__)

# ===== Config via .env =====
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
PANEL_HOST = os.getenv("PANEL_HOST", "0.0.0.0")
PANEL_PORT = int(os.getenv("PANEL_PORT", os.getenv("PORT", "8000")))

# Endpoints do backend
PROMPT_CONFIG_URL = f"{BACKEND_BASE_URL}/prompt_config"
STATUS_URL        = f"{BACKEND_BASE_URL}/status"
PROCESSAR_URL     = f"{BACKEND_BASE_URL}/processar_atendimento"

# Carrega o HTML e injeta variáveis via render_template_string
BASE_DIR = Path(__file__).resolve().parent
PAINEL_HTML_PATH = BASE_DIR / "painel.html"
PANEL_HTML = PAINEL_HTML_PATH.read_text(encoding="utf-8")

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
    return render_template_string(
        PANEL_HTML,
        BACKEND_BASE_URL=BACKEND_BASE_URL,
        INSTRUCAO_TESTE_ASSISTENTE=INSTRUCAO_TESTE_ASSISTENTE
    )

@app.route("/prompt_config", methods=["GET", "POST"])
def prompt_config_route():
    try:
        if request.method == "GET":
            r = requests.get(PROMPT_CONFIG_URL, timeout=10)
        else:
            r = requests.post(PROMPT_CONFIG_URL, json=(request.get_json() or {}), timeout=15)
        return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type", "application/json")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
