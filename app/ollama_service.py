# app/ollama_service.py
"""
Cliente HTTP para chamar a LLM no servidor da GPU.
- Produção (CPU->GPU na VPC): use IP PRIVADO 172.31.18.20
- Testes do notebook (internet -> GPU): use IP PÚBLICO 98.87.41.241 (libere 8000 para seu IP)
Config por ambiente:
  LLM_HOST (default: 172.31.18.20)
  LLM_PORT (default: 8000)
  LLM_ROUTE (default: /infer)
  LLM_BASE_URL (opcional: substitui host:port de uma vez, ex.: http://98.87.41.241:8000)
"""

import os
import requests
from typing import Any, Dict, Optional
import json

# Carrega host/porta/rota
HOST = os.getenv("LLM_HOST", "172.31.18.20")   # PRIVADO (produção)
PORT = os.getenv("LLM_PORT", "8000")
ROUTE = os.getenv("LLM_ROUTE", "/infer")

# Se LLM_BASE_URL estiver definido, ele prevalece sobre HOST/PORT
BASE = os.getenv("LLM_BASE_URL", f"http://{HOST}:{PORT}")
OLLAMA_API_URL = f"{BASE}{ROUTE}"

# Sessão com keep-alive
SESSION = requests.Session()
SESSION.headers.update({"Content-Type": "application/json"})

def health(timeout: tuple[int, int] = (2, 5)) -> Dict[str, Any]:
    """Ping simples do servidor (espera /health; se não existir, retorna ok pelo status)."""
    url = f"{BASE}/health"
    try:
        r = SESSION.get(url, timeout=timeout)
        if r.ok:
            try:
                return r.json()
            except Exception:
                return {"ok": True, "status_code": r.status_code}
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Falha no healthcheck em {url}: {e}") from e

def infer_llm(
    prompt: str,
    system: str = "",
    max_tokens: int = 256,
    temperature: float = 0.2,
    extra: Optional[Dict[str, Any]] = None,
    timeout_connect: int = 5,
    timeout_read: int = 60,
    max_new_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """Chama a rota /infer da LLM."""
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "system": system,
        # Compatível com llm_server.py: envia max_new_tokens (e mantém max_tokens, não atrapalha)
        "max_new_tokens": max_new_tokens if max_new_tokens is not None else max_tokens,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if extra:
        payload.update(extra)

    try:
        r = SESSION.post(OLLAMA_API_URL, json=payload, timeout=(timeout_connect, timeout_read))
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectTimeout as e:
        raise RuntimeError(
            f"Timeout ao conectar em {OLLAMA_API_URL}. "
            f"Verifique SG da GPU (porta 8000), HOST={HOST}, se o serviço está em 0.0.0.0:{PORT}."
        ) from e
    except requests.exceptions.ReadTimeout as e:
        raise RuntimeError(
            f"Conectou mas não respondeu a tempo (read timeout) em {OLLAMA_API_URL}. "
            f"Verifique logs da LLM/latência."
        ) from e
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Erro de conexão com {OLLAMA_API_URL}. Verifique rota, DNS, serviço e rede."
        ) from e

def _strip_code_fences(text: str) -> str:
    """Remove cercas ``` de markdown se presentes."""
    t = (text or "").strip()
    if t.startswith("```"):
        # remove primeira linha ```... e última ```
        lines = t.splitlines()
        # descarta primeira e última linha se são fences
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return t

def _extract_text(resp: Dict[str, Any]) -> str:
    """Extrai o texto útil do JSON retornado pela LLM."""
    if not isinstance(resp, dict):
        return ""
    # chaves diretas comuns
    for k in ("text", "response", "generated_text", "output", "answer"):
        v = resp.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    # estilo OpenAI/compat
    choices = resp.get("choices")
    if isinstance(choices, list) and choices:
        c0 = choices[0] or {}
        # text direto
        if isinstance(c0.get("text"), str):
            return c0["text"].strip()
        # message.content
        msg = c0.get("message") or {}
        if isinstance(msg.get("content"), str):
            return msg["content"].strip()
    # último recurso: stringificar
    return json.dumps(resp, ensure_ascii=False)

def get_llama_response(prompt: str, system: str = "", max_tokens: int = 256, temperature: float = 0.2, extra: Optional[Dict[str, Any]] = None) -> str:
    """Envia prompt à LLM e retorna texto limpo."""
    try:
        resp = infer_llm(
            prompt=prompt,
            system=system or "",
            max_tokens=max_tokens,
            temperature=temperature,
            extra=extra,
            # mantém coerência: max_new_tokens espelhado
            max_new_tokens=max_tokens,
        )
        txt = _extract_text(resp)
        return _strip_code_fences(txt).strip()
    except Exception as e:
        return f""

def classify_intent_llm(texto: str) -> str:
    """
    Classifica a intenção do usuário.
    Retorno compatível com atendimento.py: um destes rótulos longos:
      - relato_caso
      - agendar_consulta_cliente
      - consulta_andamento_cliente
      - enviar_documento_cliente
    """
    system = "Classificador de intenção. Responda apenas com UMA palavra do conjunto solicitado."
    prompt = (
        "Classifique a intenção do usuário em UMA palavra, dentre: relato_caso, agendar, andamento, documento.\n"
        f"Texto: {texto}\n"
        "Resposta:"
    )
    raw = get_llama_response(prompt=prompt, system=system, max_tokens=8, temperature=0.0)
    label = (raw or "").strip().lower()
    # normalização curta -> rótulos usados no atendimento.py
    mapping = {
        "relato_caso": "relato_caso",
        "agendar": "agendar_consulta_cliente",
        "andamento": "consulta_andamento_cliente",
        "documento": "enviar_documento_cliente",
    }
    return mapping.get(label, "relato_caso")

def extrair_dados_caso_llm(texto: str, dados_existentes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extrai dados estruturados do relato do caso. Retorna dict com:
      nome_cliente, telefone, area_direito, urgencia, resumo_caso, observacoes
    """
    base = dados_existentes or {}
    system = "Você extrai informações de casos jurídicos e responde apenas em JSON válido (sem comentários)."
    prompt = (
        "Extraia os seguintes campos do texto e responda em JSON com as chaves exatamente:\n"
        "nome_cliente, telefone, area_direito, urgencia, resumo_caso, observacoes.\n"
        "Se não souber algum campo, deixe como null ou string vazia. Use português.\n"
        f"Texto: {texto}"
    )
    try:
        raw = get_llama_response(prompt=prompt, system=system, max_tokens=256, temperature=0.1)
        raw = _strip_code_fences(raw)
        data = json.loads(raw)
        # saneamento + defaults
        return {
            "nome_cliente": data.get("nome_cliente") or base.get("nome_cliente"),
            "telefone": data.get("telefone") or base.get("telefone") or base.get("telefone_cliente") or "",
            "area_direito": data.get("area_direito") or "Geral",
            "urgencia": data.get("urgencia") or "Média",
            "resumo_caso": data.get("resumo_caso") or texto,
            "observacoes": data.get("observacoes") or "",
        }
    except Exception:
        # fallback robusto
        return {
            "nome_cliente": base.get("nome_cliente"),
            "telefone": base.get("telefone") or base.get("telefone_cliente") or "",
            "area_direito": "Geral",
            "urgencia": "Média",
            "resumo_caso": texto,
            "observacoes": "",
        }
