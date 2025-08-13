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
📚 GUIA DE TESTES DO ASSISTENTE MODULAR

Este guia explica o que cada função faz, como testar e também o que o assistente modular realiza nos bastidores para automatizar o seu trabalho. 
O objetivo é que você, como advogado(a), valide todos os fluxos e nos envie o arquivo JSON do debugger ao final para que possamos corrigir e otimizar o sistema.

⚙️ O que o Assistente Modular faz “por trás”:
• 📊 Cria e atualiza planilhas no Google Sheets para funcionar como CRM do escritório.
• 📁 Cria pastas e salva documentos no Google Drive, organizando por nome do cliente.
• 📧 Envia e-mails pelo Gmail para confirmações e envio de links.
• 📅 Cria eventos no Google Calendar e envia convites.
• 💬 Envia mensagens automáticas via WhatsApp (versão final).
• 🗂 Atualiza listas de clientes aguardando retorno ou com documentos pendentes.
• 📢 Envia notificações de prazo ou audiência.

⚖️ Fluxos do Advogado (`tipo_usuario = advogado`):
1. fluxo_onboarding_advogado → Coleta dados para configurar CRM: nome, OAB, especialidade, escritório e como organiza seus clientes (por área, urgência, data etc.). 
   Teste: "Meu nome é João Silva, OAB 12345, especialista em direito trabalhista, organizo meus clientes por área e urgência."
2. fluxo_aprovacao_peticao → Registra petição aprovada. 
   Teste: "A petição está aprovada, pode protocolar."
3. fluxo_alerta_prazo → Gera lembrete de prazo/audiência.
   Teste: "Prazo do recurso vence amanhã."
4. fluxo_honorarios → Registra valores de honorários.
   Teste: "Os honorários são de R$ 5.000,00."
5. fluxo_documento_juridico → Envia ou armazena modelo de documento.
   Teste: "Preciso de um modelo de contrato de prestação de serviços."
6. fluxo_envio_documento_cliente → Salva documento para cliente.
   Teste: "Enviar cópia da petição ao cliente."
7. fluxo_consulta_andamento → Consulta andamento processual.
   Teste: "Verificar andamento do processo 0000000-00.0000.0.00.0000."
8. fluxo_pagamento_fora_padrao → Registra pagamento fora do combinado.
   Teste: "O cliente pagou um valor menor que o acordado."
9. fluxo_indicacao → Registra cliente indicado.
   Teste: "O João me indicou a Maria como cliente."
10. fluxo_documento_pendente → Marca documento pendente.
    Teste: "Falta o comprovante de endereço."
11. fluxo_revisao_documento → Solicita revisão.
    Teste: "Preciso que revise essa contestação."
12. fluxo_status_negociacao → Registra status de negociação.
    Teste: "Negociação está em fase final."
13. fluxo_decisao_permuta → Atualiza decisão sobre permuta.
    Teste: "Cliente aceitou a permuta."
14. fluxo_sumiço_cliente → Marca cliente inativo.
    Teste: "Cliente sumiu desde semana passada."
15. fluxo_update_clientes_aguardando → Atualiza clientes aguardando.
    Teste: "Atualizar lista de clientes aguardando retorno."
16. fluxo_update_documento_pendente → Atualiza status de documentos.
    Teste: "Atualizar situação do RG do cliente."
17. fluxo_nao_atendimento_area → Marca caso como não atendido por área.
    Teste: "Não atuo em direito criminal."
18. fluxo_status_multiplos_processos → Registra status de múltiplos processos.
    Teste: "Verificar processos 123 e 456."
19. fluxo_notificacao_cliente → Envia notificação ao cliente.
    Teste: "Avisar cliente que audiência foi marcada."
20. fluxo_alterar_cancelar_agendamento → Atualiza/cancela compromisso.
    Teste: "Cancelar reunião de amanhã."
21. fluxo_resumo_estatisticas → Gera relatório.
    Teste: "Quantos casos foram fechados este mês?"
22. fluxo_lembrete_audiencia → Cria lembrete de audiência.
    Teste: "Me lembrar da audiência dia 20."
23. fluxo_enviar_resumo_caso → Envia resumo de caso.
    Teste: "Me envie o resumo do caso do cliente João."

👤 Fluxos do Cliente (`tipo_usuario = cliente`):
1. relato_caso → Registra relato e salva no CRM.
   Cliente: "Fui demitido sem justa causa e quero meus direitos."
2. consulta_andamento_cliente → Solicita dados para consulta processual.
   Cliente: "Quero saber o andamento do meu processo."
3. agendar_consulta_cliente → Cria evento no Calendar.
   Cliente: "Quero agendar reunião amanhã às 15h."
4. enviar_documento_cliente → Salva documento no Drive e CRM.
   Cliente: Envia arquivo ou foto.
5. fluxo_nao_detectado → Resposta padrão.
   Cliente: Mensagem fora dos fluxos acima.

🛠 Como Testar:
1. No painel, envie mensagens simulando cada fluxo, alternando tipo_usuario entre advogado e cliente.
2. Observe a resposta e, quando aplicável, verifique se houve ação por trás (planilha criada, documento salvo, evento gerado).
3. Teste todos os fluxos ao menos uma vez.
4. Baixe o arquivo JSON do debugger no final.
5. Envie para nossa equipe para análise e depuração.
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
