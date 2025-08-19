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
import re  # novo

# Helper: limpa eco do template Mistral Instruct na saída
def _clean_mistral_echo(txt: str) -> str:
    s = (txt or "").lstrip()
    # removes everything before [/INST] if it echoes
    if s.startswith("<s>[INST]") or s.startswith("[INST]"):
        end = s.find("[/INST]")
        if end != -1:
            s = s[end+len("[/INST]"):].lstrip()
    # cuts at </s> if there's garbage after
    eos = s.find("</s>")
    if eos != -1:
        s = s[:eos]
    # removes role prefix that sometimes leaks
    for pref in ("Usuário:", "Usuario:", "Atendente:", "Assistente:"):
        if s.startswith(pref):
            s = s[len(pref):].lstrip()
    return s.strip()

# Se LLM_BASE_URL estiver definido, ele prevalece (use isso no CPU para depurar mais fácil).
# Default mantido: http://172.31.18.20:8000
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://172.31.18.20:8000").rstrip("/")

# Legado (mantido por compat/variáveis, mas NÃO usado para enviar): HOST/PORT/BASE
HOST = os.getenv("LLM_HOST", "172.31.18.20")
PORT = os.getenv("LLM_PORT", "8000")
ROUTE = os.getenv("LLM_ROUTE", "/infer")
BASE = os.getenv("LLM_BASE_URL", f"http://{HOST}:{PORT}")

# Caminho único de envio (evita drift): sempre LLM_BASE_URL + ROUTE
OLLAMA_API_URL = f"{LLM_BASE_URL}{ROUTE}"

# Sessão com keep-alive
SESSION = requests.Session()
SESSION.headers.update({"Content-Type": "application/json"})

def health(timeout: tuple[int, int] = (2, 5)) -> Dict[str, Any]:
    """Ping simples do servidor (espera /health; se não existir, retorna ok pelo status)."""
    # Usa a mesma base do envio para evitar divergência.
    url = f"{LLM_BASE_URL}/health"
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
        # Compatível com llm_server.py: envia max_new_tokens (e mantém max_tokens)
        "max_new_tokens": max_new_tokens if max_new_tokens is not None else max_tokens,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if extra:
        payload.update(extra)

    # Caminho único de envio; logs temporários pós-sucesso
    url = OLLAMA_API_URL
    try:
        r = requests.post(url, json=payload, timeout=(timeout_connect, timeout_read))
        r.raise_for_status()
        # LOG TEMPORÁRIO: URL e status quando sucesso (para depuração)
        print(f"[ollama_service] POST {url} -> {r.status_code}")
        return r.json()
    except requests.exceptions.ConnectTimeout as e:
        raise RuntimeError(
            f"Timeout ao conectar em {url}. Verifique SG/serviço e se está em 0.0.0.0."
        ) from e
    except requests.exceptions.ReadTimeout as e:
        raise RuntimeError(
            f"Conectou mas não respondeu a tempo (read timeout) em {url}. Verifique logs/latência."
        ) from e
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Erro de conexão com {url}. Verifique rota, DNS, serviço e rede."
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

def get_llama_response(
    prompt: str,
    system: str = "",
    max_tokens: int = 512,
    temperature: float = 0.2,
    extra: Optional[Dict[str, Any]] = None
) -> str:
    """
    Chama a GPU em /infer. Envie 'prompt' já montado por montar_prompt_instruct().
    Aumenta max_tokens por padrão (512). Limpa eco do template [INST].
    Ignora silenciosamente parâmetros não usados (temperature/extra) para compatibilidade.
    """
    # Caminho único de envio; usar mesma URL para evitar drift.
    url = OLLAMA_API_URL
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "max_new_tokens": int(max_tokens),
        "system": system or ""
    }
    # Permite providers que aceitam temperature/extra sem quebrar
    if temperature is not None:
        payload["temperature"] = float(temperature)
    if extra and isinstance(extra, dict):
        payload.update(extra)
    try:
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        # LOG TEMPORÁRIO: URL e status quando sucesso (para depuração)
        print(f"[ollama_service] POST {url} -> {r.status_code}")
        if r.headers.get("content-type","").lower().startswith("application/json"):
            data = r.json()
            txt = data.get("text") or data.get("response") or data.get("generated_text") or ""
        else:
            txt = r.text or ""
        cleaned = _clean_mistral_echo(txt)
        # fallback mínimo ao remover cercas se houver
        cleaned = _strip_code_fences(cleaned)
        return cleaned.strip()
    except Exception as e:
        return f"(Falha ao consultar LLM: {e})"

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
