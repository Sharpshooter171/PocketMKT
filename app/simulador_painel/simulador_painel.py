from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import requests
import random
import json
from datetime import datetime

prompt_config_cache = {}

app = Flask(__name__)

# Endpoint para visualizar e atualizar o prompt_config do backend principal
@app.route("/prompt_config", methods=["GET", "POST"])
def prompt_config_route():
    """Permite visualizar e atualizar o prompt_config do backend principal"""
    if request.method == "GET":
        # Busca o prompt_config atual do backend
        try:
            resp = requests.get("http://13.218.132.81:8000/prompt_config", timeout=5)
            return jsonify(resp.json())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "POST":
        # Envia novo prompt_config para o backend
        data = request.json
        try:
            resp = requests.post("http://13.218.132.81:8000/prompt_config", json=data, timeout=5)
            return jsonify(resp.json())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# 🚀 URL do servidor Flask principal
FLASK_LOCAL_URL = "http://44.223.0.187:5000/atendimento"

print("⚖️ PocketMKT - Painel do Advogado MVP")
print("=" * 50)
print("🔗 Conectando ao Backend Principal: http://127.0.0.1:5000")
print("🌐 Painel disponível em: http://127.0.0.1:8000/painel")
print("=" * 50)

# 🔧 Carrega o HTML do painel a partir do arquivo
try:
    with open("painel.html", "r", encoding="utf-8") as f:
        CHAT_HTML = f.read()
    print("✅ Interface do Painel carregada com sucesso.")
except FileNotFoundError:
    print("❌ Erro crítico: Arquivo painel.html não encontrado!")
    CHAT_HTML = "<h1>Erro: painel.html não foi encontrado.</h1>"

@app.route("/")
def index():
    """Redireciona a rota raiz para /painel."""
    return redirect(url_for("painel"))

@app.route("/painel")
def painel():
    """Exibe a página principal do painel do advogado."""
    return render_template_string(CHAT_HTML)

# Rota para receber mensagens do frontend do painel e enviar ao backend
@app.route("/mensagem", methods=["POST"])
def enviar():
    dados = request.json
    mensagem_usuario = dados.get("mensagem", "")
    # O padrão agora é 'advogado', mas o frontend ainda pode alternar
    tipo_usuario = dados.get("tipo_usuario", "advogado")
    funcoes = dados.get("funcoes", {})
    # Simula um ID de usuário autenticado do painel
    usuario_id = "painel_advogado_1234"

    if not mensagem_usuario.strip():
        return jsonify({"resposta": "Digite algo para conversar."})

    # Contar funções ativas
    funcoes_ativas = sum(1 for f in funcoes.values() if f)
    
    payload = {
        "telefone": usuario_id,
        "mensagem": mensagem_usuario,
        "tipo": tipo_usuario,
        "segmento": "advocacia",
        "funcoes_habilitadas": funcoes,
        # Adiciona informações de autenticação simulada
        "usuario_autenticado": True,
        "email_advogado": "advogado.simulado@example.com",
        "debug_info": {
            "funcoes_ativas": funcoes_ativas,
            "timestamp": dados.get("timestamp"),
            "interface": "painel_advogado_mvp"
        }
    }

    try:
        print(f"🚀 Enviando do Painel para o Backend: {tipo_usuario} | {funcoes_ativas} funções ativas")
        print(f"📝 Mensagem: {mensagem_usuario[:50]}...")
        
        resposta = requests.post(FLASK_LOCAL_URL, json=payload, timeout=30)
        print("🔄 Status code do Backend:", resposta.status_code)
        
        if resposta.status_code == 200:
            resposta_json = resposta.json()
            resposta_texto = resposta_json.get("reply", "Não entendi.")
            return jsonify({
                "resposta": resposta_texto,
                "debug": {
                    "tipo_usuario": tipo_usuario,
                    "funcoes_ativas": funcoes_ativas,
                    "status": "sucesso"
                }
            })
        else:
            print(f"❌ Erro HTTP: {resposta.status_code}")
            return jsonify({
                "resposta": f"❌ Erro do servidor ({resposta.status_code}): {resposta.text[:100]}",
                "debug": {
                    "error": True,
                    "status_code": resposta.status_code
                }
            })
    except Exception as e:
        print(f"❌ Erro na comunicação com o backend: {e}")
        return jsonify({
            "resposta": f"❌ Erro de conexão: Verifique se o servidor do backend está rodando na porta 5000",
            "debug": {
                "error": True,
                "exception": str(e)
            }
        })

@app.route("/enviar", methods=["POST"])
def enviar_alias():
    return enviar()

@app.route("/status", methods=["GET"])
def status():
    """Endpoint de status do painel"""
    try:
        # Testar conexão com o Flask principal
        test_response = requests.get("http://127.0.0.1:5000/teste", timeout=5)
        flask_status = "OK" if test_response.status_code == 200 else f"Error {test_response.status_code}"
    except:
        flask_status = "Desconectado"
    
    return jsonify({
        "painel_status": "OK",
        "timestamp": datetime.now().isoformat(),
        "backend_connection": flask_status,
        "versao": "MVP 2.0",
        "interface": "Painel do Advogado"
    })

@app.route("/test_functions", methods=["POST"])
def test_functions():
    """Endpoint para testar funções específicas"""
    data = request.json
    funcao = data.get("funcao", "")
    
    mensagens_teste = {
        "onboarding": "Olá, sou Dr. João Silva, OAB/SP 123456, do Escritório Silva & Associados",
        "prazos": "verificar prazos urgentes",
        "resumo": "gerar resumo do escritório",
        "documento": "revisar minuta de contrato",
        "diario": "consultar diário oficial",
        "honorarios": "verificar pagamentos pendentes"
    }
    
    if funcao in mensagens_teste:
        # Simular envio automático
        payload = {
            "mensagem": mensagens_teste[funcao],
            "tipo_usuario": "advogado",
            "funcoes": {funcao: True}
        }
        
        return jsonify({
            "status": "teste_enviado",
            "funcao": funcao,
            "mensagem": mensagens_teste[funcao]
        })
    
    return jsonify({
        "status": "erro",
        "funcoes_disponiveis": list(mensagens_teste.keys())
    })


if __name__ == "__main__":
    print("\n🚀 Iniciando Painel do Advogado PocketMKT MVP...")
    print("📊 Funcionalidades disponíveis:")
    print("   • Interface avançada com controles")
    print("   • Toggle de funções em tempo real") 
    print("   • Modo Cliente/Advogado")
    print("   • Botões de ação rápida")
    print("   • Status de conexão em tempo real")
    print("   • Debug avançado")
    print(f"\n🌐 Acesse o painel: http://127.0.0.1:8000/painel")
    print(f"🔧 Endpoint de status: http://127.0.0.1:8000/status")
    print("=" * 50)
    
    app.run(port=8000, debug=True)

