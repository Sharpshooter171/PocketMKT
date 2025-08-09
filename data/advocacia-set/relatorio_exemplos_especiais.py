import json
import random

# Lê o dataset gerado
with open("dataset_finetune_advocacia.jsonl", "r", encoding="utf-8") as f:
    linhas = [json.loads(l) for l in f.readlines()]

# Funções para identificar tipos especiais
def is_negativo(ex):
    return (
        "não posso fornecer informações jurídicas" in ex["prompt"].lower()
        or "não forneço pareceres jurídicos" in ex["prompt"].lower()
        or "não posso consultar processos" in ex["prompt"].lower()
        or "não posso informar prazos jurídicos" in ex["prompt"].lower()
    )

def is_fora_contexto(ex):
    return any(
        frase in ex["prompt"].lower()
        for frase in [
            "qual o melhor restaurante", "você gosta de futebol", "me recomenda um filme", "qual seu nome?", "como está o tempo"
        ]
    )

def is_truncado(ex):
    return any(
        s in ex["prompt"] for s in ["Oi...", "Volto depois", "Preciso sair, depois continuo", "Acho que caiu a conexão", "..."]
    )

def is_ruido(ex):
    return any(e in ex["prompt"] for e in ["blz", "vlw", "qdo", "msg", "pq", "docs", "vc", "tbm", "pra", "tá ok", "obg", "obrigadão", "valeu mesmo", "urgente urgente!", "por favor por favor!", "agora agora!", "🙏", "🤷‍♂️", "👀", "👋", "✅", "📆", "📞", "⚠️", "📢", "📄", "📬", "📎", "📝", "💰", "💸", "🧾", "📈", "🕒", "🔎", "🔄", "😉", "👍"])

# Seleciona exemplos
def sample_by_type(linhas, filtro, n=3):
    filtrados = [ex for ex in linhas if filtro(ex)]
    return random.sample(filtrados, min(n, len(filtrados)))

relatorio = {}
relatorio["negativo"] = sample_by_type(linhas, is_negativo)
relatorio["fora_contexto"] = sample_by_type(linhas, is_fora_contexto)
relatorio["truncado"] = sample_by_type(linhas, is_truncado)
relatorio["ruido"] = sample_by_type(linhas, is_ruido)

with open("relatorio_exemplos_especiais.json", "w", encoding="utf-8") as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)

print("Relatório salvo em relatorio_exemplos_especiais.json. Exemplos por tipo:")
for tipo, exemplos in relatorio.items():
    print(f"\nTipo: {tipo}")
    for ex in exemplos:
        print("-"*40)
        print(ex["prompt"])
