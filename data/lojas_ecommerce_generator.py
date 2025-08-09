from faker import Faker
import random
import json
from datetime import datetime

fake = Faker('pt_BR')

# -------------------- Listas Estruturadas -------------------------

PRODUTOS_LOJA = [
    # Eletrônicos
    "smartphone", "notebook gamer", "tablet", "smartwatch", "fone bluetooth",
    "caixa de som JBL", "mouse gamer", "teclado mecânico", "monitor 4K",
    "webcam HD", "impressora multifuncional", "roteador Wi-Fi 6",
    "carregador wireless", "power bank", "adaptador USB-C",
    
    # Eletrodomésticos
    "geladeira", "fogão 4 bocas", "micro-ondas", "máquina de lavar",
    "liquidificador", "batedeira", "aspirador de pó", "ventilador",
    "ar-condicionado split", "purificador de água", "cafeteira",
    "grill elétrico", "ferro de passar", "secador de cabelo",
    
    # Móveis
    "sofá retrátil", "cadeira gamer", "mesa de escritório", "estante",
    "cama box", "guarda-roupa", "rack para TV", "criado-mudo",
    "poltrona reclinável", "banqueta", "aparador", "espelho decorativo",
    
    # Vestuário
    "tênis Nike", "camiseta básica", "calça jeans", "moletom",
    "jaqueta corta-vento", "bermuda", "vestido", "blazer",
    "meia esportiva", "cueca box", "sutiã", "pijama",
    
    # Acessórios
    "mochila escolar", "bolsa feminina", "carteira", "relógio inteligente",
    "óculos de sol", "brinco", "colar", "pulseira",
    "cinto de couro", "chapéu", "luvas", "cachecol",
    
    # Esportes
    "bola de futebol", "raquete de tênis", "tênis de corrida",
    "bicicleta", "skate", "patins", "halteres", "corda para pular",
    "prancha de surf", "mala de viagem", "garrafa térmica", "toalha esportiva",
    
    # Beleza
    "perfume", "creme hidratante", "batom", "esmalte",
    "kit maquiagem", "escova de cabelo", "secador profissional",
    "chapinha", "barbeador elétrico", "aparelho de depilação",
    
    # Bebês
    "carrinho de bebê", "berço", "mamadeira", "fralda",
    "chupeta", "brinquedo educativo", "banheira", "cadeirinha para carro",
    
    # Livros
    "livro de ficção", "enciclopédia", "livro infantil", "biografia",
    "livro de culinária", "guia de viagem", "quadrinho", "livro acadêmico",
    
    # Automotivo
    "pneu", "bateria para carro", "kit de limpeza", "capa para volante",
    "aromatizador", "cabo jumper", "farol auxiliar", "tapete para carro",
    
    # Pet Shop
    "ração para cães", "coleira", "casinha para pet", "brinquedo para gatos",
    "aquário", "tapete higiênico", "comedouro automático", "gaiola para pássaros"
]

# Produtos aleatórios adicionais para variedade
for _ in range(30):
    PRODUTOS_LOJA.append(f"{fake.company()} {fake.word()}")

# Variantes de produtos
VARIANTES_PRODUTO = [
    # Tamanhos
    "tamanho P", "tamanho M", "tamanho G", "tamanho GG", "tamanho XG",
    "tamanho 36", "tamanho 38", "tamanho 40", "tamanho 42", "tamanho 44",
    "tamanho 46", "tamanho 48", "tamanho 50", "tamanho único",
    
    # Cores
    "cor preta", "cor branca", "cor vermelha", "cor azul", "cor verde",
    "cor amarela", "cor rosa", "cor roxa", "cor cinza", "cor bege",
    "cor marrom", "cor dourada", "cor prateada", "cor transparente",
    "cor listrada", "cor xadrez", "cor degradê", "cor fosca",
    
    # Modelos
    "modelo básico", "modelo premium", "modelo esportivo", "modelo vintage",
    "modelo moderno", "modelo retrô", "modelo slim", "modelo oversized",
    "modelo infantil", "modelo adulto", "modelo unissex",
    
    # Versões
    "versão 2023", "versão 2024", "versão plus", "versão light",
    "versão pro", "versão max", "versão mini", "versão travel",
    "versão wireless", "versão com fio", "versão digital",
    
    # Capacidades
    "capacidade 500ml", "capacidade 1L", "capacidade 2L", "capacidade 5L",
    "capacidade 10L", "capacidade 16GB", "capacidade 32GB", "capacidade 64GB",
    "capacidade 128GB", "capacidade 256GB", "capacidade 500GB",
    "capacidade 1TB", "capacidade 2TB"
]

PROMOCOES = [
    # Descontos
    "desconto de 10%", "desconto de 20%", "desconto de 30%", 
    "desconto de 40%", "desconto de 50%", "desconto relâmpago",
    "desconto progressivo", "desconto em 2ª unidade", "desconto à vista",
    
    # Frete
    "frete grátis", "frete fixo R$ 10", "frete econômico", 
    "frete expresso grátis", "frete com retirada na loja",
    
    # Brindes
    "brinde exclusivo", "brinde surpresa", "kit presente", 
    "amostra grátis", "produto extra",
    
    # Programas de benefícios
    "cashback", "pontos multiplicados", "milhas extras", 
    "parcelamento sem juros", "parcelamento em 12x",
    
    # Combos
    "combo especial", "kit completo", "leva 2 paga 1", 
    "combo família", "promoção casada",
    
    # Temporais
    "oferta do dia", "black friday", "cyber monday", 
    "dia dos pais", "dia das mães", "natal"
]

# ----------------- Função Texto Informal ------------------------

def texto_informal(frase):
    mapeamento = {
        "você": "vc", "vocês": "vcs", "está": "ta", "quanto": "qnto",
        "demora": "dmra", "horas": "hrs", "tem": "tem", "produto": "prdt",
        "promoção": "promo", "com": "c/", "para": "pra"
    }
    frase = frase.lower()
    for k, v in mapeamento.items():
        frase = frase.replace(k, v)
    if random.random() < 0.4:
        frase = frase.replace("a", "aa", 1)
    if random.random() < 0.3:
        frase = frase.replace("e", "ee", 1)
    return frase

def whatsapp_style(frase):
    # Simula erros, abreviações, emojis e informalidade típica do WhatsApp
    gírias = ["rs", "kkk", "blz", "vlw", "obg", "tmj", "pq", "q", "tdb", "sussa"]
    if random.random() < 0.2:
        frase = frase.lower()
    if random.random() < 0.15:
        frase = frase.replace("não", "naum")
    if random.random() < 0.15:
        frase = frase.replace("quero", "keru").replace("preciso", "preciso msm")
    if random.random() < 0.1:
        frase += " " + random.choice(gírias)
    if random.random() < 0.1:
        frase += " 😔"
    if random.random() < 0.1:
        frase = frase.replace("você", "vc").replace("está", "ta")
    if random.random() < 0.1:
        frase = frase.replace(" ", "")
    return frase    

# ----------------- Gerador de Diálogos ---------------------------

def gerar_dialogo_cliente():
    produto = random.choice(PRODUTOS_LOJA)
    variante = random.choice(VARIANTES_PRODUTO)

    pergunta = f"Oi, vcs ainda tem o {produto} {variante}?"
    if random.random() < 0.7:
        pergunta = texto_informal(pergunta)
        pergunta = whatsapp_style(pergunta)

    resposta = f"Sim, temos o {produto} disponível no {variante}. Quer reservar?"
    if random.random() < 0.5:
        resposta = texto_informal(resposta)
        resposta = whatsapp_style(resposta)
    return montar_estrutura("cliente", "consulta_estoque", pergunta, resposta)

def gerar_dialogo_promocao():
    validade = fake.date_between(start_date='today', end_date='+15d').strftime('%d/%m')
    pergunta = f"O {produto} ainda ta c/ {promocao}?"
    if random.random() < 0.7:
        pergunta = texto_informal(pergunta)
        pergunta = whatsapp_style(pergunta)
    resposta = f"Sim, o {promocao} do {produto} é válido até {validade}. Aproveita!"
    if random.random() < 0.5:
        resposta = texto_informal(resposta)
        resposta = whatsapp_style(resposta)
    return montar_estrutura("cliente", "informacoes_promocao", pergunta, resposta)

def gerar_dialogo_contratante():
    vendas = fake.random_number(digits=5)
    pergunta = "Me manda o relatório de vendas da semana"
    if random.random() < 0.3:
        pergunta = texto_informal(pergunta)
        pergunta = whatsapp_style(pergunta)
    resposta = f"Relatório gerado: R$ {vendas} em vendas totais. Enviado no e-mail."
    if random.random() < 0.2:
        resposta = texto_informal(resposta)
        resposta = whatsapp_style(resposta)
    return montar_estrutura("contratante", "relatorio_vendas", pergunta, resposta)

# ----------------- Monta Estrutura Final --------------------------

def montar_estrutura(tipo, funcao, pergunta, resposta):
    return {
        "segment": "Lojas e E-commerce",
        "user_type": tipo,
        "function": funcao,
        "user_query": pergunta,
        "bot_response": resposta,
        "timestamp": fake.date_time_this_year().isoformat()
    }

# ----------------- Centralizador de Dataset ----------------------

def gerar_dataset(total_estoque=100, total_promocoes=80, total_contratante=50):
    dataset = []

    for _ in range(total_estoque):
        dataset.append(gerar_dialogo_cliente())

    for _ in range(total_promocoes):
        dataset.append(gerar_dialogo_promocao())

    for _ in range(total_contratante):
        dataset.append(gerar_dialogo_contratante())

    print(f"Total de conversas geradas: {len(dataset)}")
    salvar_json(dataset, "dataset_loja.json")

# ----------------- Salvar em Arquivo ------------------------------

def salvar_json(data, nome_arquivo):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Dataset salvo com sucesso em: {nome_arquivo}")

# ----------------- Execução Principal ----------------------------

if __name__ == "__main__":
    gerar_dataset()
