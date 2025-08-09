from faker import Faker
import random
import csv

faker = Faker('pt_BR')  # Generate Brazilian Portuguese data

# Possíveis motivos de contato
motivos = [
    "Agendar consulta",
    "Remarcar atendimento",
    "Tirar dúvida",
    "Reclamação",
    "Saber preços",
    "Confirmar horário"
]

# Possíveis preferências de horário/data
preferencias = [
    "de manhã", "à tarde", "à noite",
    "sábado", "domingo",
    "próxima semana", "mês que vem", "em agosto", "em setembro"
]

# Função para montar mensagens simuladas
def gerar_mensagem(nome, necessidade, preferencia):
    formatos = [
        f"Oi, meu nome é {nome}, queria {necessidade.lower()} {preferencia}",
        f"Olá, gostaria de {necessidade.lower()} {preferencia}",
        f"{necessidade} {preferencia}, pode me ajudar?",
        f"Bom dia, sou {nome} e quero {necessidade.lower()} {preferencia}",
        f"Quero {necessidade.lower()} {preferencia}",
        f"Olá, meu nome é {nome} e preciso {necessidade.lower()}",
        f"Você pode me ajudar a {necessidade.lower()}?",
        f"Oi, {preferencia} teria horário para {necessidade.lower()}?"
    ]
    return random.choice(formatos)

# Lista final dos dados gerados
dados = []

# Número de exemplos desejado
total_exemplos = 5000

for _ in range(total_exemplos):
    nome = faker.name()
    necessidade = random.choice(motivos)
    preferencia = random.choice(preferencias)

    mensagem = gerar_mensagem(nome, necessidade, preferencia)
    
    # Nem todas as mensagens terão todas as informações, simula casos incompletos:
    incluir_nome = random.choices([True, False], weights=[0.7, 0.3])[0]
    incluir_necessidade = random.choices([True, False], weights=[0.9, 0.1])[0]
    incluir_preferencia = random.choices([True, False], weights=[0.8, 0.2])[0]

    mensagem_final = mensagem
    nome_final = nome if incluir_nome else "NOME_NAO_ENCONTRADO"
    necessidade_final = necessidade if incluir_necessidade else "NECESSIDADE_NAO_ENCONTRADA"
    preferencia_final = preferencia if incluir_preferencia else "PREFERENCIA_NAO_ENCONTRADA"

    dados.append([mensagem_final, nome_final, necessidade_final, preferencia_final])

# Salvar em CSV pronto para treino
with open('dataset_treino_bot.csv', mode='w', encoding='utf-8', newline='') as arquivo:
    writer = csv.writer(arquivo)
    writer.writerow(["mensagem", "nome_esperado", "necessidade_esperada", "preferencia_esperada"])
    writer.writerows(dados)

print("✅ Dataset gerado com sucesso: dataset_treino_bot.csv")
