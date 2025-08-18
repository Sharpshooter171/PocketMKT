# Bootstrapping de path para execução local/AWS (antes de qualquer import de módulos do pacote)
import os, sys

_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_FILE_DIR, "..", ".."))  # .../PocketMKT
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from flask import Blueprint, request, jsonify, Response, g, redirect, url_for  # redirect/url_for
import threading
from app import prompt_config  # novo

# Blueprint deve ser definido antes de ser usado
atendimento_bp = Blueprint("atendimento_bp", __name__)
prompt_config_lock = threading.Lock()

# Remover imports Flask duplicados mais abaixo
# from flask import Blueprint, request, jsonify, Response
# ...
# from flask import Blueprint, request, jsonify

# Troque qualquer @app.route por @atendimento_bp.route (não havia no arquivo; apenas garantindo)
# @app.route('/processar_atendimento', methods=['POST'])
# def processar_atendimento():
#     ...
@atendimento_bp.route('/processar_atendimento', methods=['POST'])
def processar_atendimento():
    """Processa o atendimento: classifica intenção e extrai dados do caso."""
    dados = request.get_json() or {}
    texto = (dados.get("texto") or "").strip()

    # 1. Classificar intenção (pode falhar silenciosamente, fallback para relato_caso)
    with prompt_config_lock:
        rotulo = prompt_config.classify_intent_llm(texto)
    
    # 2. Extrair dados do caso (fallback robusto para dict vazio)
    with prompt_config_lock:
        dados_caso = prompt_config.extrair_dados_caso_llm(texto)

    # Montar payload de resposta unificado
    payload = {"intencao": rotulo, "dados_caso": dados_caso}

    # Resposta simplificada para testes
    return jsonify(payload), 200