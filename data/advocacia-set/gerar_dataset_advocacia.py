# ====== IMPORTS E CONSTANTES ======
import random
import json
import string
from faker import Faker

faker = Faker('pt_BR')

SAUDACOES = [
    "Olá", "Oi", "Bom dia", "Boa tarde", "Boa noite", "Tudo bem?", "Tudo certo?", "E aí", "E aí, beleza?", "Opa", "Alô", "Fala", "Caro(a)", "Prezados", "Saudações", "Falaê", "Salve", "👋"
]
DESPEDIDAS = [
    "Obrigado!", "Aguardo retorno", "Até logo", "Grato(a)", "Valeu", "Fico no aguardo", "Qualquer coisa, estou à disposição", "Abraço", "Att.", "👍", "🙏", "Até mais", "No aguardo", "Obrigado desde já", "Forte abraço"
]
EMOJIS = [
    "🙏", "🤷‍♂️", "👀", "👋", "✅", "📆", "📞", "⚠️", "📢", "📄", "📬", "📎", "📝", "💰", "💸", "🧾", "📈", "🕒", "🔎", "🔄", "📢", "😉", "👍"
]
GIRIAS = [
    "blz", "vlw", "qdo", "msg", "pq", "docs", "vc", "tbm", "pra", "tá ok", "s/ novidades", "obg", "obrigadão", "valeu mesmo"
]
REPETICOES = [
    "urgente urgente!", "por favor por favor!", "agora agora!"
]
MENSAGENS_AUTOMATICAS = [
    "Mensagem automática do sistema", "Não responda esta mensagem"
]
LINKS_CURTOS = [
    "Acesse: bit.ly/contrato123", "Acesse: bit.ly/docpendente456", "Acesse: bit.ly/revisao789"
]

# ====== CONTADORES GLOBAIS ======
contadores = {
    'onboarding': {'negativo': 0, 'ruido': 0, 'truncado': 0, 'fora_contexto': 0},
    'cliente_cadastrado': {'negativo': 0, 'ruido': 0, 'truncado': 0, 'fora_contexto': 0},
    'advogado': {'negativo': 0, 'ruido': 0, 'truncado': 0, 'fora_contexto': 0},
}

# ====== SYSTEM PROMPTS ======
SYSTEM_PROMPT_ONBOARDING = (
    "Você é um assistente virtual que faz a triagem inicial em um escritório de advocacia. "
    "Sempre cumprimente o usuário, colete nome completo e motivo do contato. "
    "Nunca forneça informações jurídicas, técnicas ou invente dados. "
    "Encaminhe dúvidas técnicas para o advogado responsável. "
    "Use respostas curtas, diretas, profissionais e acolhedoras. "
    "Se o cliente já informou nome e motivo, agradeça, NÃO repita perguntas e informe os próximos passos, incluindo agendamento, se necessário."
)

SYSTEM_PROMPT_CLIENTE_CADASTRADO = (
    "Você é um assistente virtual de triagem para um escritório de advocacia. "
    "O cliente já está cadastrado. "
    "Responda apenas dúvidas administrativas, de agenda, documentos pendentes e rotinas do escritório. "
    "Nunca forneça opiniões jurídicas, detalhes técnicos, leis ou prazos. Não invente procedimentos. "
    "Se a dúvida for técnica, explique que o advogado responderá posteriormente. "
    "Use frases curtas, profissionais, acolhedoras e SEM repetir a coleta de dados. "
    "Reconheça informações já fornecidas pelo cliente e oriente sobre próximos passos."
)

SYSTEM_PROMPT_ADVOGADO = (
    "Você é um assistente virtual que auxilia advogados em rotinas administrativas do escritório. "
    "Responda apenas dúvidas sobre documentos, prazos, agenda, estatísticas e fluxo de atendimento. "
    "Nunca dê opiniões jurídicas nem trate de casos específicos de clientes. "
    "Se a dúvida for jurídica, encaminhe ao setor responsável. "
    "Use sempre respostas curtas, claras e objetivas."
)

# ====== FUNÇÕES ======
def adicionar_ruido_texto(texto):
    """
    Adiciona no máximo DOIS ruídos diferentes (emoji, gíria, repetição) por mensagem de usuário, escolhidos aleatoriamente.
    """
    opcoes = [
        lambda t: t + " " + random.choice(GIRIAS),
        lambda t: t + " " + random.choice(REPETICOES),
        lambda t: t + " " + random.choice(EMOJIS)
    ]
    n = random.choices([0,1,2], weights=[0.5,0.3,0.2])[0]
    if n == 0:
        return texto
    escolhidas = random.sample(opcoes, k=n)
    for func in escolhidas:
        texto = func(texto)
    return texto

def aplicar_ruido_bot(resposta, nivel_ruido):
    """
    Aplica no máximo UM tipo de ruído (emoji, gíria OU repetição OU despedida) por resposta do bot, nunca mais de um.
    Também limita o comprimento da resposta a 120 caracteres (truncando e adicionando '...').
    """
    if nivel_ruido <= 0:
        return resposta
    tipos_ruido = [
        lambda r: r + " " + random.choice(EMOJIS),
        lambda r: r + " " + random.choice(GIRIAS),
        lambda r: r + " " + random.choice(REPETICOES),
        lambda r: r + " " + random.choice(DESPEDIDAS)
    ]
    if random.random() < nivel_ruido:
        ruido_func = random.choice(tipos_ruido)
        resposta = ruido_func(resposta)
    # Limita comprimento
    if len(resposta) > 120:
        resposta = resposta[:117] + '...'
    return resposta

def gerar_exemplo_decisao_permuta(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo sobre decisão de permuta, troca de bens ou acordo de substituição.
    """
    nome = faker.name()
    saudacao = random.choice(SAUDACOES)
    tipo_permuta = random.choice([
        "troca de imóvel",
        "permuta de veículos",
        "substituição de garantia",
        "acordo de permuta comercial",
        "troca de bens móveis",
        "permuta de ações judiciais",
        "substituição de parte no processo"
    ])
    processo_num = f"000{random.randint(1000,9999)}-{random.randint(10,99)}.2024.8.26.0000"
    mensagem_usuario = random.choice([
        f"{saudacao}, qual a decisão sobre a {tipo_permuta}? Ficou alguma pendência?",
        f"{saudacao}, a {tipo_permuta} foi aprovada? Sobre o documento que enviei semana passada...",
        f"{saudacao}, preciso saber se a {tipo_permuta} está autorizada no processo {processo_num}.",
        f"{saudacao}, pode atualizar o status da {tipo_permuta}? Conforme conversamos ontem.",
        f"{saudacao}, houve definição sobre a {tipo_permuta}? Mais alguma dúvida?"
    ])
    canal = random.choice(["e-mail", "WhatsApp", "Google Drive", "Telegram", "dropbox", "portal do cliente", "correio físico"])
    formato = random.choice(["PDF", "JPG", "DOCX", "XLSX"])
    resposta_bot = random.choice([
        f"Decisão sobre a {tipo_permuta}: aprovada. Documento em anexo ({formato}) enviado por {canal}.",
        f"A {tipo_permuta} foi autorizada. Documentos serão preparados para assinatura e enviados via {canal}.",
        f"Permuta em análise. Aguarde retorno do setor responsável.",
        f"Status da {tipo_permuta}: pendente de confirmação das partes.",
        f"A {tipo_permuta} foi concluída com sucesso. Notificações enviadas por {canal}."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 🔄", " urgente!", " preciso decidir hoje!", " (cliente aguardando)"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    return {
        "prompt": f"[DECISÃO PERMUTA]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_status_negociacao(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo sobre status de negociação, andamento de acordo ou proposta.
    """
    nome = faker.name()
    saudacao = random.choice(SAUDACOES)
    tipo_negociacao = random.choice([
        "acordo trabalhista",
        "negociação de honorários",
        "proposta de acordo extrajudicial",
        "mediação familiar",
        "negociação de dívida",
        "acordo de parcelamento",
        "proposta de indenização"
    ])
    processo_num = f"000{random.randint(1000,9999)}-{random.randint(10,99)}.2024.8.26.0000"
    mensagem_usuario = random.choice([
        f"{saudacao}, qual o status da {tipo_negociacao} no processo {processo_num}?",
        f"{saudacao}, houve avanço na {tipo_negociacao}? Conforme conversamos ontem.",
        f"{saudacao}, preciso saber se a {tipo_negociacao} foi aceita. Ficou alguma pendência?",
        f"{saudacao}, pode atualizar sobre a {tipo_negociacao}? Sobre o documento que enviei semana passada...",
        f"{saudacao}, a {tipo_negociacao} está em andamento? Mais alguma dúvida?"
    ])
    canal = random.choice(["e-mail", "WhatsApp", "Google Drive", "Telegram", "dropbox", "portal do cliente", "correio físico"])
    formato = random.choice(["PDF", "JPG", "DOCX", "XLSX"])
    resposta_bot = random.choice([
        f"Status da {tipo_negociacao}: aguardando resposta da outra parte. Documento ({formato}) enviado por {canal}.",
        f"A {tipo_negociacao} está em andamento. Última atualização registrada no sistema.",
        f"Proposta de {tipo_negociacao} foi aceita. Próximos passos serão informados por {canal}.",
        f"Negociação concluída com sucesso. Documentos em {formato} enviados para assinatura via {canal}.",
        f"Ainda não houve resposta sobre a {tipo_negociacao}. Seguimos acompanhando."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 🤝", " urgente!", " preciso saber hoje!", " (cliente aguardando)"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    return {
        "prompt": f"[STATUS NEGOCIAÇÃO]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_revisao_documento(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo sobre revisão de documento jurídico, solicitação de análise ou feedback.
    """
    nome = faker.name()
    saudacao = random.choice(SAUDACOES)
    tipo_documento = random.choice([
        "petição inicial",
        "contrato de prestação de serviços",
        "acordo extrajudicial",
        "contestação trabalhista",
        "recurso de apelação",
        "notificação extrajudicial",
        "laudo pericial"
    ])
    processo_num = f"000{random.randint(1000,9999)}-{random.randint(10,99)}.2024.8.26.0000"
    mensagem_usuario = random.choice([
        f"{saudacao}, pode revisar o {tipo_documento} antes do envio?",
        f"{saudacao}, preciso de feedback sobre o {tipo_documento}.",
        f"{saudacao}, o {tipo_documento} está pronto para análise?",
        f"{saudacao}, favor revisar o {tipo_documento} e apontar ajustes.",
        f"{saudacao}, revisão do {tipo_documento} foi concluída?",
        f"Prezados, solicito, por gentileza, análise do {tipo_documento} referente ao processo {processo_num}.",
        f"E aí, galera, tudo na paz? Mandei o {tipo_documento} pra revisão, blz?",
        f"Acho que mandei o documento errado, podem conferir?",
        f"Enviei áudio pq estou sem tempo, depois me avisem se está ok.",
        f"Qual status?",
        f"Me liga urgente!",
        f"Ninguém me respondeu ainda! Preciso de urgência, por favor!",
        f"{saudacao}, mandei o {tipo_documento} semana passada, ficou alguma pendência? Mais alguma dúvida?",
        f"{saudacao}, segue o {tipo_documento} em PDF e JPG, qualquer coisa me avise."
    ])
    resposta_bot = random.choice([
        f"Revisão do {tipo_documento} concluída. Documento pronto para envio.",
        f"{tipo_documento.title()} revisado. Sugestões de ajustes enviadas ao responsável.",
        f"Análise do {tipo_documento} finalizada. Nenhuma pendência identificada.",
        f"Revisão realizada! Documento disponível no sistema para conferência.",
        f"Feedback sobre o {tipo_documento} enviado. Aguardando confirmação do responsável.",
        f"Detectamos que o documento enviado não corresponde ao processo {processo_num}. Favor reenviar."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 📝", " urgente!", " preciso hoje!", " (cliente aguardando)"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    return {
        "prompt": f"[REVISÃO DOCUMENTO]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_documento_pendente(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo sobre documento pendente, solicitação ou cobrança de envio.
    """
    nome = faker.name()
    saudacao = random.choice(SAUDACOES)
    tipo_documento = random.choice([
        "procuração assinada",
        "comprovante de residência",
        "documento de identidade",
        "contrato social",
        "certidão negativa",
        "laudo pericial",
        "comprovante de pagamento"
    ])
    processo_num = f"000{random.randint(1000,9999)}-{random.randint(10,99)}.2024.8.26.0000"
    canal = random.choice(["e-mail", "WhatsApp", "Google Drive", "Telegram", "dropbox", "portal do cliente", "correio físico"])
    formato = random.choice(["PDF", "JPG", "DOCX", "XLSX"])
    mensagem_usuario = random.choice([
        f"{saudacao}, há algum documento pendente do cliente?",
        f"{saudacao}, preciso saber se falta enviar o {tipo_documento}.",
        f"{saudacao}, o cliente já enviou o {tipo_documento}?",
        f"{saudacao}, pode cobrar o envio do {tipo_documento}?",
        f"{saudacao}, falta algum documento para o processo?",
        f"Prezados, solicito, por gentileza, confirmação do envio do {tipo_documento} referente ao processo {processo_num}.",
        f"E aí, galera, tudo certo? Mandei o {tipo_documento} mas acho que era outro, confere pra mim?",
        f"Acho que mandei o documento errado, podem conferir?",
        f"Enviei áudio pq estou sem tempo, depois me avisem se está ok.",
        f"Qual status?",
        f"Me liga urgente!",
        f"Ninguém me respondeu ainda! Preciso de urgência, por favor!",
        f"{saudacao}, mandei o {tipo_documento} semana passada, ficou alguma pendência? Mais alguma dúvida?",
        f"{saudacao}, segue o {tipo_documento} em PDF e JPG, qualquer coisa me avise."
    ])
    resposta_bot = random.choice([
        f"Documento pendente: {tipo_documento}. Solicitação de envio enviada ao cliente por {canal} ({formato}).",
        f"O cliente ainda não enviou o {tipo_documento}. Lembrete enviado ao cliente.",
        f"Todos os documentos foram recebidos, exceto o {tipo_documento}.",
        f"Cobrança de envio do {tipo_documento} registrada. Acompanhe pelo sistema.",
        f"{tipo_documento.title()} pendente. Cliente será notificado novamente.",
        f"Detectamos que o documento enviado não corresponde ao processo {processo_num}. Favor reenviar."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 📄", " urgente!", " falta só esse!", " (cliente atrasado)"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + '[FIM]'
    return {
        "prompt": f"[DOCUMENTO PENDENTE]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_indicacao(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo sobre indicação de clientes, parceiros ou serviços jurídicos.
    """
    nome = faker.name()
    saudacao = random.choice(["Olá", "Oi", "Bom dia", "Boa tarde", "Tudo bem?"])
    tipo_indicacao = random.choice([
        "novo cliente",
        "parceiro de negócios",
        "serviço de contabilidade",
        "especialista em direito tributário",
        "advogado correspondente",
        "empresa para consultoria",
        "indicação para mediação"
    ])
    mensagem_usuario = random.choice([
        f"{saudacao}, gostaria de fazer uma indicação de {tipo_indicacao}.",
        f"{saudacao}, posso indicar um {tipo_indicacao} para o escritório?",
        f"{saudacao}, segue indicação de {tipo_indicacao} para análise.",
        f"{saudacao}, quero recomendar um {tipo_indicacao} para nossos serviços.",
        f"{saudacao}, como faço para registrar uma indicação de {tipo_indicacao}?"
    ])
    resposta_bot = random.choice([
        f"Indicação de {tipo_indicacao} registrada com sucesso. Obrigado pela colaboração!",
        f"Agradecemos a indicação de {tipo_indicacao}, {nome.split()[0]}. O setor responsável irá analisar.",
        f"Indicação recebida! Entraremos em contato para mais detalhes se necessário.",
        f"Registro de indicação de {tipo_indicacao} efetuado. Você será avisado sobre o andamento.",
        f"Indicação anotada. Caso precise complementar informações, envie por este canal."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 🤝", " urgente!", " posso indicar mais?", " (indicação de confiança)"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    return {
        "prompt": f"[INDICAÇÃO]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_pagamento_fora_padrao(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo sobre pagamento fora do padrão, cobranças e exceções.
    """
    nome = faker.name()
    saudacao = random.choice(["Olá", "Oi", "Bom dia", "Boa tarde", "Tudo bem?"])
    motivo = random.choice([
        "pagamento parcial",
        "pagamento em atraso",
        "pagamento em duplicidade",
        "pagamento não identificado",
        "pagamento via transferência internacional",
        "pagamento em espécie",
        "pagamento por terceiros"
    ])
    valor = random.choice(["R$ 1.200,00", "R$ 3.000,00", "R$ 2.500,00", "R$ 800,00"])
    mensagem_usuario = random.choice([
        f"{saudacao}, identifiquei um {motivo} no valor de {valor}.",
        f"{saudacao}, preciso registrar um {motivo} para o cliente.",
        f"{saudacao}, houve um {motivo} referente ao processo X.",
        f"{saudacao}, como proceder com {motivo} de {valor}?",
        f"{saudacao}, o sistema acusou {motivo} no pagamento do cliente."
    ])
    resposta_bot = random.choice([
        f"Pagamento fora do padrão registrado: {motivo} - {valor}. Setor financeiro notificado.",
        f"Atenção: {motivo} detectado. Orientação enviada ao responsável.",
        f"Situação de {motivo} encaminhada para análise. Aguarde retorno do financeiro.",
        f"{motivo.title()} de {valor} registrado. Cliente será informado se necessário.",
        f"Procedimento especial para {motivo} iniciado. Documentação será revisada."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 💳", " urgente!", " precisa de atenção!", " (caso atípico)"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    return {
        "prompt": f"[PAGAMENTO FORA PADRÃO]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_consulta_andamento(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo sobre consulta de andamento de processo, tarefa ou documento.
    """
    nome = faker.name()
    saudacao = random.choice(["Olá", "Oi", "Bom dia", "Boa tarde", "Tudo bem?"])
    tipo_andamento = random.choice([
        "processo 1234567-89.2023.8.26.0001",
        "petição protocolada",
        "audiência marcada",
        "documento pendente",
        "recurso em análise",
        "pagamento em processamento",
        "contrato em revisão"
    ])
    mensagem_usuario = random.choice([
        f"{saudacao}, qual o andamento do {tipo_andamento}?",
        f"{saudacao}, preciso saber o status do {tipo_andamento}.",
        f"{saudacao}, houve atualização no {tipo_andamento}?",
        f"{saudacao}, pode consultar o andamento do {tipo_andamento}?",
        f"{saudacao}, o que mudou no {tipo_andamento} desde a última consulta?"
    ])
    resposta_bot = random.choice([
        f"O {tipo_andamento} está em andamento. Última atualização registrada no sistema.",
        f"Status do {tipo_andamento}: aguardando manifestação da parte contrária.",
        f"{tipo_andamento.title()} atualizado. Nenhuma pendência identificada.",
        f"O {tipo_andamento} foi concluído com sucesso.",
        f"Não houve novas atualizações no {tipo_andamento} desde a última consulta."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 🔎", " urgente!", " preciso saber hoje!", " (cliente cobrando)"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    return {
        "prompt": f"[CONSULTA ANDAMENTO]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_envio_documento_cliente(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo sobre envio de documento ao cliente, confirmação e dúvidas.
    """
    nome = faker.name()
    saudacao = random.choice(["Olá", "Oi", "Bom dia", "Boa tarde", "Tudo bem?"])
    tipo_documento = random.choice([
        "procuração assinada",
        "contrato revisado",
        "petição protocolada",
        "comprovante de pagamento",
        "laudo pericial",
        "notificação extrajudicial",
        "acordo homologado"
    ])
    canal_envio = random.choice(["e-mail", "WhatsApp", "portal do cliente", "Google Drive"])
    mensagem_usuario = random.choice([
        f"{saudacao}, envie o {tipo_documento} para o cliente por {canal_envio}.",
        f"{saudacao}, o {tipo_documento} já foi enviado ao cliente?",
        f"{saudacao}, preciso confirmar o envio do {tipo_documento} ao cliente.",
        f"{saudacao}, pode reenviar o {tipo_documento} para o cliente?",
        f"{saudacao}, o cliente recebeu o {tipo_documento}?"
    ])
    resposta_bot = random.choice([
        f"{tipo_documento.title()} enviado ao cliente via {canal_envio}.",
        f"Confirmação: {tipo_documento} já foi enviado ao cliente.",
        f"Reenvio do {tipo_documento} realizado com sucesso.",
        f"Cliente recebeu o {tipo_documento} e confirmou o recebimento.",
        f"Envio do {tipo_documento} agendado para hoje pelo {canal_envio}."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 📤", " urgente!", " preciso do comprovante!", " (cliente aguardando)"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    return {
        "prompt": f"[ENVIO DOCUMENTO CLIENTE]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_documento_juridico(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo sobre solicitação, envio ou dúvidas de documentos jurídicos.
    """
    nome = faker.name()
    saudacao = random.choice(["Olá", "Oi", "Bom dia", "Boa tarde", "Tudo bem?"])
    tipo_documento = random.choice([
        "procuração",
        "contrato social",
        "petição inicial",
        "certidão negativa",
        "laudo pericial",
        "contrato de prestação de serviços",
        "acordo extrajudicial",
        "notificação extrajudicial"
    ])
    mensagem_usuario = random.choice([
        f"{saudacao}, preciso do modelo de {tipo_documento}.",
        f"{saudacao}, pode enviar o {tipo_documento} para análise?",
        f"{saudacao}, onde encontro o {tipo_documento} do cliente?",
        f"{saudacao}, o {tipo_documento} já está disponível no sistema?",
        f"{saudacao}, pode revisar o {tipo_documento} antes do envio?"
    ])
    resposta_bot = random.choice([
        f"O {tipo_documento} foi enviado para seu e-mail cadastrado.",
        f"Modelo de {tipo_documento} disponível no painel de documentos.",
        f"{tipo_documento.title()} anexado ao sistema. Verifique na área de documentos.",
        f"Revisão do {tipo_documento} concluída. Pronto para envio.",
        f"Documento {tipo_documento} disponível para download."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 📄", " urgente!", " preciso hoje!", " (pode ser por e-mail?)"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    return {
        "prompt": f"[DOCUMENTO JURÍDICO]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_honorarios(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo sobre honorários advocatícios, cobranças e pagamentos.
    """
    nome = faker.name()
    saudacao = random.choice(["Olá", "Oi", "Bom dia", "Boa tarde", "Tudo bem?"])
    valor = random.choice(["R$ 1.500,00", "R$ 2.800,00", "R$ 3.200,00", "R$ 900,00", "R$ 4.500,00"])
    status = random.choice(["pendente", "pago", "vencido", "em negociação"])
    mensagem_usuario = random.choice([
        f"{saudacao}, qual o status do pagamento dos honorários do cliente João?",
        f"{saudacao}, preciso cobrar honorários do processo X.",
        f"{saudacao}, os honorários do caso Maria já foram recebidos?",
        f"{saudacao}, pode enviar um lembrete de cobrança de honorários?",
        f"{saudacao}, quero saber o valor pendente de honorários do mês."
    ])
    resposta_bot = random.choice([
        f"O valor de honorários é {valor} e está {status}.",
        f"Cobrança de honorários enviada ao cliente. Status: {status}.",
        f"Honorários do caso em questão: {valor} - {status}.",
        f"Lembrete de pagamento de honorários enviado ao cliente.",
        f"Todos os honorários do mês estão em dia, {nome.split()[0]}."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 💰", " urgente!", " preciso cobrar!", " (atrasado)"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    return {
        "prompt": f"[HONORÁRIOS]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_alerta_prazo(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo de alerta de prazo para petição ou audiência.
    """
    nome = faker.name()
    saudacao = random.choice(["Olá", "Oi", "Bom dia", "Boa tarde", "Tudo bem?"])
    tipo_prazo = random.choice([
        "prazo para contestação",
        "prazo para recurso",
        "prazo para apresentação de documentos",
        "prazo para audiência",
        "prazo para manifestação",
        "prazo para defesa",
        "prazo para protocolo de petição"
    ])
    data_prazo = faker.date_between(start_date="+1d", end_date="+15d").strftime("%d/%m/%Y")
    mensagem_usuario = random.choice([
        f"{saudacao}, preciso de um alerta para o {tipo_prazo} em {data_prazo}.",
        f"{saudacao}, me avise sobre o {tipo_prazo} que vence em {data_prazo}.",
        f"{saudacao}, configure um lembrete para o {tipo_prazo} ({data_prazo}).",
        f"{saudacao}, não posso perder o {tipo_prazo} de {data_prazo}. Pode avisar?"
    ])
    resposta_bot = random.choice([
        f"Alerta configurado para o {tipo_prazo} em {data_prazo}. Você receberá um lembrete automático.",
        f"Pode deixar, {nome.split()[0]}! Lembrete do {tipo_prazo} agendado para {data_prazo}.",
        f"Lembrete criado: {tipo_prazo} - {data_prazo}. Você será avisado com antecedência.",
        f"Tudo certo! Alerta do {tipo_prazo} salvo. Notificaremos antes do vencimento."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 🙏", " não esquecer!", " urgente!", " por favor!"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    return {
        "prompt": f"[ALERTA PRAZO]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_aprovacao_peticao(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo de aprovação de petição pelo advogado.
    """
    nome = faker.name()
    saudacao = random.choice(["Olá", "Oi", "Bom dia", "Boa tarde", "Tudo certo?", "Prezados"])
    tipo_peticao = random.choice([
        "contestação trabalhista",
        "recurso de apelação",
        "petição inicial de divórcio",
        "embargos de declaração",
        "manifestação sobre laudo pericial",
        "pedido de liminar",
        "contrarrazões ao recurso",
        "petição de cumprimento de sentença"
    ])
    mensagem_usuario = random.choice([
        f"{saudacao}, recebi a {tipo_peticao} para revisão.",
        f"{saudacao}, posso aprovar a {tipo_peticao}?",
        f"{saudacao}, a {tipo_peticao} está pronta para assinatura?",
        f"{saudacao}, favor revisar e aprovar a {tipo_peticao}.",
        f"{saudacao}, segue a {tipo_peticao} para aprovação."
    ])
    resposta_bot = random.choice([
        f"A {tipo_peticao} foi aprovada e encaminhada para assinatura.",
        f"Petição revisada e aprovada, {nome.split()[0]}. Pode prosseguir com o protocolo.",
        f"Aprovação registrada! Se precisar de ajustes, por favor, sinalize.",
        f"{tipo_peticao.title()} aprovada. Documentos anexados ao sistema.",
        f"Tudo certo! {tipo_peticao.title()} aprovada e salva no painel do escritório."
    ])
    if random.random() < 0.08:
        mensagem_usuario += random.choice([" 👍", " (está ok?)", " posso assinar?", " tudo certo?"])
    if random.random() < 0.2:
        mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    return {
        "prompt": f"[APROVAÇÃO PETIÇÃO]\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot}"
    }
def gerar_exemplo_onboarding(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    """
    Gera um exemplo de diálogo de onboarding do advogado contratante, coletando dados essenciais.
    """
    nome = faker.name()
    saudacao = random.choice(SAUDACOES)
    motivo = random.choice([
        "saber o andamento do meu processo",
        "agendar uma consulta",
        "dúvida sobre honorários",
        "perdi meus documentos",
        "quero saber quais documentos faltam",
        "consultar audiência marcada",
        "fazer uma indicação",
        "saber sobre segunda via de documento",
        "cancelar um agendamento",
        "atualizar meus dados"
    ])
    exemplos_negativos = [
        ("Qual é o prazo para recurso de apelação?", "Não posso fornecer informações jurídicas. Um advogado irá analisar e responder."),
        ("Me informe a lei sobre rescisão contratual.", "Não posso fornecer informações jurídicas ou leis. Um advogado irá responder."),
        ("Pode me dar um parecer sobre meu caso?", "Não forneço pareceres jurídicos. Encaminharei ao advogado responsável."),
        ("Quero saber detalhes do processo 0001234-55.2024.8.26.0000.", "Não posso consultar processos ou fornecer informações jurídicas. Aguarde contato do advogado."),
        ("Qual o prazo para apresentar contestação?", "Não posso informar prazos jurídicos. Um advogado irá responder.")
    ]
    negativo = False
    ruido = False
    truncado = False
    fora_contexto = False
    if random.random() < 0.08:
        mensagem_usuario, resposta_bot_local = random.choice(exemplos_negativos)
        negativo = True
    else:
        mensagem_usuario = f"{saudacao}, meu nome é {nome}. Quero {motivo}."
        if random.random() < 0.10:
            mensagem_usuario = random.choice([
                "Oi...",
                "Volto depois",
                "Preciso sair, depois continuo",
                "Acho que caiu a conexão",
                mensagem_usuario[:random.randint(5, max(10, len(mensagem_usuario)//2))] + "..."
            ])
            truncado = True
        elif random.random() < 0.2:
            mensagem_usuario = adicionar_ruido_texto(mensagem_usuario)
            ruido = True
        if random.random() < 0.05:
            mensagem_usuario = random.choice([
                "Qual o melhor restaurante da cidade?",
                "Você gosta de futebol?",
                "Como está o tempo aí?",
                "Me recomenda um filme?",
                "Qual seu nome?"
            ])
            fora_contexto = True
        resposta_bot_local = random.choice([
            f"Olá! Seu pedido foi registrado. Aguarde retorno do escritório.",
            "Olá! Vou encaminhar seu pedido para o setor responsável. Aguarde nosso contato.",
            "Recebido. Em breve, um advogado irá te atender.",
            "Perfeito. Já registrei seu motivo, aguarde retorno do escritório.",
            "Pode aguardar, o atendimento será realizado em breve.",
            "Não recebi o documento ainda, pode reenviar?",
            "Poderia, por gentileza, enviar o contrato?",
            "Estou verificando, retornarei em breve com mais informações.",
            "Assim que tiver novidades, aviso por aqui.",
            "Não posso responder essa dúvida técnica, encaminharei ao responsável.",
            "Não posso responder questões jurídicas, um advogado irá analisar e responder.",
            "Nenhuma cobrança pendente."
        ])
        if random.random() < 0.05:
            resposta_bot_local = random.choice([
                "Desculpe, não entendi sua última mensagem.",
                "Aguarde um momento, por favor.",
                "Mensagem recebida, mas não localizei o contexto.",
                "Posso ajudar em mais alguma coisa?"
            ])
    resposta_bot_local = aplicar_ruido_bot(resposta_bot_local, nivel_ruido_bot) + token_fim
    if negativo:
        contadores['onboarding']['negativo'] += 1
    if ruido:
        contadores['onboarding']['ruido'] += 1
    if truncado:
        contadores['onboarding']['truncado'] += 1
    if fora_contexto:
        contadores['onboarding']['fora_contexto'] += 1
    return {
        "prompt": f"{SYSTEM_PROMPT_ONBOARDING}\nUsuário: {mensagem_usuario}\nAtendente: {resposta_bot_local}{token_fim}"
    }
def gerar_exemplo_cliente_cadastrado(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    nome = faker.name()
    exemplos_negativos = [
        ("Qual é o prazo para recurso de apelação?", "Não posso fornecer informações jurídicas. Um advogado irá analisar e responder."),
        ("Me informe a lei sobre rescisão contratual.", "Não posso fornecer informações jurídicas ou leis. Um advogado irá responder."),
        ("Pode me dar um parecer sobre meu caso?", "Não forneço pareceres jurídicos. Encaminharei ao advogado responsável."),
        ("Quero saber detalhes do processo 0001234-55.2024.8.26.0000.", "Não posso consultar processos ou fornecer informações jurídicas. Aguarde contato do advogado."),
        ("Qual o prazo para apresentar contestação?", "Não posso informar prazos jurídicos. Um advogado irá responder.")
    ]
    negativo = False
    ruido = False
    truncado = False
    fora_contexto = False
    if random.random() < 0.08:
        tipo_pergunta, resposta_bot = random.choice(exemplos_negativos)
        negativo = True
    else:
        tipo_pergunta = random.choice([
            "Preciso enviar algum documento pendente?",
            "Qual o horário de funcionamento do escritório?",
            "Como remarco meu atendimento?",
            "Já tenho cadastro, qual o próximo passo?",
            "Quais documentos faltam no meu processo?",
            "Tem reunião agendada para mim?",
            "O advogado já recebeu meus documentos?",
            "Gostaria de atualizar meus dados de contato.",
            "Quero saber se tem cobrança pendente.",
            "Preciso cancelar uma consulta."
        ])
        if random.random() < 0.10:
            tipo_pergunta = random.choice([
                "Oi...",
                "Volto depois",
                "Preciso sair, depois continuo",
                "Acho que caiu a conexão",
                tipo_pergunta[:random.randint(5, max(10, len(tipo_pergunta)//2))] + "..."
            ])
            truncado = True
        elif random.random() < 0.2:
            tipo_pergunta = adicionar_ruido_texto(tipo_pergunta)
            ruido = True
        if random.random() < 0.05:
            tipo_pergunta = random.choice([
                "Qual o melhor restaurante da cidade?",
                "Você gosta de futebol?",
                "Como está o tempo aí?",
                "Me recomenda um filme?",
                "Qual seu nome?"
            ])
            fora_contexto = True
        resposta_bot = random.choice([
            "Nenhuma cobrança pendente.",
            "O escritório funciona de segunda a sexta, das 8h às 18h. Aguarde retorno do escritório.",
            "Para remarcar, basta responder com o novo horário desejado. Aguarde confirmação.",
            "Seus dados já foram anotados, aguarde o contato do advogado.",
            "Você pode consultar suas reuniões no portal do cliente.",
            "Seu pedido de cancelamento foi registrado. Aguarde retorno do escritório.",
            "Não recebi o documento ainda, pode reenviar?",
            "Poderia, por gentileza, enviar o contrato?",
            "Estou verificando, retornarei em breve com mais informações.",
            "Assim que tiver novidades, aviso por aqui.",
            "Não posso responder essa dúvida técnica, encaminharei ao responsável.",
            "Não posso responder questões jurídicas, um advogado irá analisar e responder."
        ])
        if random.random() < 0.05:
            resposta_bot = random.choice([
                "Desculpe, não entendi sua última mensagem.",
                "Aguarde um momento, por favor.",
                "Mensagem recebida, mas não localizei o contexto.",
                "Posso ajudar em mais alguma coisa?"
            ])
    # Ruído, emoji e despedida no bot: controlado por parâmetro
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    if negativo:
        contadores['cliente_cadastrado']['negativo'] += 1
    if ruido:
        contadores['cliente_cadastrado']['ruido'] += 1
    if truncado:
        contadores['cliente_cadastrado']['truncado'] += 1
    if fora_contexto:
        contadores['cliente_cadastrado']['fora_contexto'] += 1
    return {
        "prompt": f"{SYSTEM_PROMPT_CLIENTE_CADASTRADO}\nUsuário: {tipo_pergunta}\nAtendente: {resposta_bot}{token_fim}"
    }

def gerar_exemplo_advogado(nivel_ruido_bot=0.02, token_fim='[FIM]'):
    exemplos_negativos = [
        ("Qual é o prazo para recurso de apelação?", "Não posso fornecer informações jurídicas. Um advogado irá analisar e responder."),
        ("Me informe a lei sobre rescisão contratual.", "Não posso fornecer informações jurídicas ou leis. Um advogado irá responder."),
        ("Pode me dar um parecer sobre meu caso?", "Não forneço pareceres jurídicos. Encaminharei ao advogado responsável."),
        ("Quero saber detalhes do processo 0001234-55.2024.8.26.0000.", "Não posso consultar processos ou fornecer informações jurídicas. Aguarde contato do advogado."),
        ("Qual o prazo para apresentar contestação?", "Não posso informar prazos jurídicos. Um advogado irá responder.")
    ]
    negativo = False
    ruido = False
    truncado = False
    fora_contexto = False
    if random.random() < 0.08:
        tarefa, resposta_bot = random.choice(exemplos_negativos)
        negativo = True
    else:
        tarefa = random.choice([
            "Preciso de alerta de prazo para petição.",
            "Como aprovo uma petição do cliente?",
            "Atualize a lista de clientes aguardando contato.",
            "Quais documentos estão pendentes no processo X?",
            "Envie resumo estatístico dos atendimentos do mês.",
            "Como reviso documentos antes do envio?",
            "Quero receber notificação de audiência.",
            "Como alterar ou cancelar um agendamento?",
            "Como envio resumo do caso para o cliente?",
            "Preciso de lembrete para audiência amanhã."
        ])
        if random.random() < 0.10:
            tarefa = random.choice([
                "Oi...",
                "Volto depois",
                "Preciso sair, depois continuo",
                "Acho que caiu a conexão",
                tarefa[:random.randint(5, max(10, len(tarefa)//2))] + "..."
            ])
            truncado = True
        elif random.random() < 0.2:
            tarefa = adicionar_ruido_texto(tarefa)
            ruido = True
        if random.random() < 0.05:
            tarefa = random.choice([
                "Qual o melhor restaurante da cidade?",
                "Você gosta de futebol?",
                "Como está o tempo aí?",
                "Me recomenda um filme?",
                "Qual seu nome?"
            ])
            fora_contexto = True
        resposta_bot = random.choice([
            "O sistema enviará alerta de prazo automaticamente 2 dias antes do vencimento. Aguarde retorno do escritório.",
            "Para aprovar uma petição, acesse o painel de documentos e clique em 'aprovar'. Aguarde confirmação.",
            "Lista de clientes aguardando contato atualizada. Aguarde retorno do escritório.",
            "Documento pendente identificado, notifique o cliente pelo chat. Aguarde retorno do escritório.",
            "Segue o resumo estatístico por e-mail. Aguarde retorno do escritório.",
            "Para revisar documentos, utilize a função 'revisão' no portal interno. Aguarde retorno do escritório.",
            "Notificação de audiência será enviada por e-mail e WhatsApp. Aguarde retorno do escritório.",
            "Agendamento alterado com sucesso. Aguarde retorno do escritório.",
            "Resumo do caso enviado ao cliente. Aguarde retorno do escritório.",
            "Lembrete de audiência agendado. Aguarde retorno do escritório.",
            "Não recebi o documento ainda, pode reenviar?",
            "Poderia, por gentileza, enviar o contrato?",
            "Estou verificando, retornarei em breve com mais informações.",
            "Assim que tiver novidades, aviso por aqui.",
            "Não posso responder essa dúvida técnica, encaminharei ao responsável.",
            "Não posso responder questões jurídicas, um advogado irá analisar e responder."
        ])
        if random.random() < 0.05:
            resposta_bot = random.choice([
                "Desculpe, não entendi sua última mensagem.",
                "Aguarde um momento, por favor.",
                "Mensagem recebida, mas não localizei o contexto.",
                "Posso ajudar em mais alguma coisa?"
            ])
    # Ruído, emoji e despedida no bot: controlado por parâmetro
    resposta_bot = aplicar_ruido_bot(resposta_bot, nivel_ruido_bot) + token_fim
    if negativo:
        contadores['advogado']['negativo'] += 1
    if ruido:
        contadores['advogado']['ruido'] += 1
    if truncado:
        contadores['advogado']['truncado'] += 1
    if fora_contexto:
        contadores['advogado']['fora_contexto'] += 1
    return {
        "prompt": f"{SYSTEM_PROMPT_ADVOGADO}\nUsuário: {tarefa}\nAtendente: {resposta_bot}{token_fim}"
    }


# Geração dos exemplos - robustez e cobertura
exemplos = []
for _ in range(15000):
    exemplos.append(gerar_exemplo_onboarding())
for _ in range(15000):
    exemplos.append(gerar_exemplo_cliente_cadastrado())
for _ in range(15000):
    exemplos.append(gerar_exemplo_advogado())

# Shuffle para não ficar agrupado
random.shuffle(exemplos)

# Salva em JSONL
with open("dataset_finetune_advocacia_45k.jsonl", "w", encoding="utf-8") as f:
    for exemplo in exemplos:
        f.write(json.dumps(exemplo, ensure_ascii=False) + "\n")

# Exibe contadores de logs
print("\nResumo dos fluxos e ruídos gerados:")
for segmento, tipos in contadores.items():
    print(f"Segmento: {segmento}")
    for tipo, valor in tipos.items():
        print(f"  {tipo}: {valor}")
print("\nDataset salvo com sucesso! Total de exemplos:", len(exemplos))
