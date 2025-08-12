from unidecode import unidecode
import re

def fluxo_relato_caso(mensagem):
    """Detecta relato de novo caso do cliente."""
    texto = unidecode(mensagem.lower())
    if any(palavra in texto for palavra in [
        "abrir processo", "relatar caso", "preciso de advogado", "tenho um problema",
        "quero resolver um problema", "meu patrao", "fui demitido", "direito trabalhista",
        "direito de familia", "direito civil", "direito penal", "direito previdenciario",
        "direito do consumidor"
    ]):
        return {"acao": "relato_caso"}
    # termos sem acento / troncos
    if any(k in texto for k in ["demitid","pensao","divida","indeniza","direito","banco","juros"]):
        return {"acao": "relato_caso"}
    return None

def fluxo_consulta_andamento_cliente(mensagem):
    """Detecta consulta de andamento por parte do cliente."""
    texto = unidecode(mensagem.lower())
    if any(palavra in texto for palavra in [
        "andamento do meu processo", "meu processo", "status do caso", "ja saiu decisao",
        "tem novidade", "como esta meu caso", "consulta andamento", "status do processo"
    ]):
        return {"acao": "consulta_andamento_cliente"}
    return None

def fluxo_enviar_documento_cliente(mensagem):
    """Detecta envio de documento pelo cliente."""
    texto = unidecode(mensagem.lower())
    if any(palavra in texto for palavra in [
        "enviei documento", "segue anexo", "enviei meu rg", "comprovante de endereco",
        "enviei cnh", "enviei meus documentos", "segue comprovante", "segue documento"
    ]):
        return {"acao": "enviar_documento_cliente"}
    return None

def fluxo_agendar_consulta_cliente(mensagem):
    """Detecta pedido de agendamento de consulta pelo cliente."""
    texto = unidecode(mensagem.lower())
    gatilhos = [
        "agendar consulta","quero marcar","preciso de uma reuniao","agendar reuniao","marcar consulta",
        "marcar horario","agendar atendimento","marcacao","agendamento","agenda",
        "consultar horario","amanha","hoje","sexta","semana que vem"
    ]
    if (
        any(p in texto for p in gatilhos)
        or re.search(r'\b(\d{1,2}(:\d{2})?\s?(h|hrs|horas)?)\b', texto)
        or re.search(r'\b(\d{1,2}/\d{1,2}(/\d{2,4})?)\b', texto)
        or re.search(r'\b(segunda|terca|terça|quarta|quinta|sexta|sabado|sábado|domingo)\b', texto, re.IGNORECASE)
    ):
        return {"acao": "agendar_consulta_cliente"}
    return None

def fluxo_atualizar_cadastro_cliente(mensagem):
    """Detecta pedido de atualização de cadastro pelo cliente."""
    texto = unidecode(mensagem.lower())
    if any(palavra in texto for palavra in [
        "mudei de endereco", "atualizar meu cadastro", "meu telefone mudou", "troquei de telefone",
        "novo endereco", "novo telefone", "atualizar endereco", "atualizar telefone"
    ]):
        return {"acao": "atualizar_cadastro_cliente"}
    return None

def fluxo_update_documento_pendente(mensagem):
    """Detecta atualização sobre documento faltando."""
    t = unidecode(mensagem.lower())
    if "documento pendente" in t or "atualizacao documento" in t:
        return {"acao": "update_documento_pendente"}
    return None

def fluxo_nao_atendimento_area(mensagem):
    """Detecta recusa/explicação de não atendimento de área."""
    t = unidecode(mensagem.lower())
    if "nao atendo" in t or "nao faco" in t or "fora da minha area" in t:
        return {"acao": "recusa_area"}
    return None

def fluxo_status_multiplos_processos(mensagem):
    """Detecta pedido de status de vários processos."""
    if "vários processos" in mensagem.lower() or re.search(r'processos?\s+(\d{2,})', mensagem):
        return {"acao": "status_multiplos_processos"}
    return None

def fluxo_notificacao_cliente(mensagem):
    """Detecta pergunta sobre notificação ao cliente."""
    if "já notificou" in mensagem.lower() or "bot avisou" in mensagem.lower():
        return {"acao": "checar_notificacao_cliente"}
    return None

def fluxo_alterar_cancelar_agendamento(mensagem):
    """Detecta pedido para alterar ou cancelar agendamento."""
    if "cancelar agendamento" in mensagem.lower() or "alterar horário" in mensagem.lower():
        return {"acao": "alterar_cancelar_agendamento"}
    return None


def fluxo_resumo_estatisticas(mensagem):
    """Detecta pedido de resumos, estatísticas, relatórios."""
    analise = analisar_texto(mensagem)
    if analise["resumo"]:
        return {"acao": "resumo_estatisticas"}
    if "resumo" in mensagem.lower() or "estatística" in mensagem.lower() or "relatório" in mensagem.lower():
        return {"acao": "resumo_estatisticas"}
    return None

def fluxo_lembrete_audiencia(mensagem):
    """Detecta pedido de lembrete de audiência."""
    if "lembrete audiência" in mensagem.lower() or "avisar audiência" in mensagem.lower():
        return {"acao": "lembrete_audiencia"}
    return None

def fluxo_enviar_resumo_caso(mensagem):
    """Detecta pedido para enviar resumo de caso a advogado específico."""
    if "enviar resumo" in mensagem.lower() or "resumir caso" in mensagem.lower():
        return {"acao": "enviar_resumo_caso"}
    return None
def fluxo_envio_documento_cliente(mensagem):
    """Detecta comando para enviar documento ao cliente."""
    texto = mensagem.lower()
    if "enviar para o cliente" in texto or "mandar por email" in texto or "enviar documento" in texto:
        return {"acao": "enviar_documento_cliente"}
    return None

def fluxo_consulta_andamento(mensagem):
    """
    Detecta pedido de consulta de andamento.
    Se não encontrar número do processo ou nome do cliente, retorna status de informação faltante.
    """
    texto = mensagem.lower()
    if any(word in texto for word in ["diário oficial", "consulta andamento", "andamento no tribunal", "processo"]):
        numero_processo = extrair_numero_processo(mensagem)
        nome_cliente = extrair_nome(mensagem)
        
        if numero_processo or nome_cliente:
            return {"acao": "consulta_andamento", "numero_processo": numero_processo, "nome_cliente": nome_cliente}
        else:
            # Se a intenção é detectada mas falta o dado principal, marca como "info_faltante"
            return {"acao": "consulta_andamento", "status": "info_faltante"}
    return None


def fluxo_pagamento_fora_padrao(mensagem):
    """Detecta proposta de pagamento incomum, como permuta."""
    analise = analisar_texto(mensagem)
    if "permuta" in mensagem.lower() or analise["negociacao"]:
        return {"tipo": "pagamento_fora_padrao"}
    return None

def fluxo_indicacao(mensagem):
    """Detecta pedido para indicar outro advogado, especialista ou referência."""
    analise = analisar_texto(mensagem)
    if analise["indicacao"]:
        return {"acao": "indicar_profissional"}
    return None


def fluxo_documento_pendente(mensagem):
    """Detecta alerta de documento faltando ou pendente."""
    lembretes = extrair_lembretes(mensagem)
    if lembretes:
        return {"acao": "lembrete_documento", "itens": lembretes}
    return None

def fluxo_revisao_documento(mensagem):
    """Detecta pedido de revisão ou ajuste de documento."""
    texto = mensagem.lower()
    if any(word in texto for word in ["revisar", "corrigir", "ajustar"]):
        return {"acao": "revisar_documento"}
    return None

def fluxo_status_negociacao(mensagem):
    """Detecta negociação, parcelamento, permuta, desconto, etc."""
    analise = analisar_texto(mensagem)
    if analise["negociacao"]:
        return {"status_negociacao": analise["negociacao"]}
    return None

def fluxo_decisao_permuta(mensagem):
    """Detecta se o advogado decide/pergunta sobre permuta."""
    if "permuta" in mensagem.lower():
        return {"decisao": "permuta"}
    return None

def fluxo_sumiço_cliente(mensagem):
    """Detecta sumiço ou espera de resposta do cliente."""
    if any(word in mensagem.lower() for word in ["sumido", "cadê você", "aguardo retorno"]):
        return {"acao": "cobrar_resposta"}
    return None

def fluxo_update_clientes_aguardando(mensagem):
    """Detecta pedido de atualização sobre clientes que não responderam."""
    if any(word in mensagem.lower() for word in ["aguardando retorno", "update clientes", "clientes pendentes"]):
        return {"acao": "update_clientes_aguardando"}
    return None
# === Fluxos jurídicos inteligentes ===


def fluxo_onboarding_advogado(mensagem):
    """Recebe mensagem e retorna dict de cadastro para onboarding do advogado."""
    numero_oab, estado_oab = extrair_oab(mensagem)
    cadastro = {
        "nome_completo": extrair_nome(mensagem),
        "oab_numero": numero_oab,
        "oab_estado": estado_oab,
        "email": extrair_email(mensagem),
        "areas_atuacao": extrair_area(mensagem),
        "nome_escritorio": extrair_nome_escritorio(mensagem)
    }
    return cadastro

def fluxo_aprovacao_peticao(mensagem):
    """Verifica se o advogado aprovou ou pediu revisão da minuta/petição."""
    texto = mensagem.lower()
    if any(word in texto for word in ["aprovo", "aprovado", "ok", "concordo", "autorizo"]):
        return {"status": "aprovado"}
    elif any(word in texto for word in ["revisar", "corrigir", "ajustar", "alterar", "não aprovei"]):
        return {"status": "revisar"}
    else:
        return {"status": "pendente"}

def fluxo_alerta_prazo(mensagem):
    """Identifica pedidos de lembrete de prazo/audiência."""
    analise = analisar_texto(mensagem)
    if "lembrete" in mensagem.lower() or "prazo" in mensagem.lower() or "audiência" in mensagem.lower():
        return {"tipo": "lembrete", "datas": analise["datas"], "horarios": analise["horarios"]}
    return None

def fluxo_honorarios(mensagem):
    """Identifica assuntos de pagamento, honorários, condições especiais."""
    pagamentos = extrair_pagamento(mensagem)
    analise = analisar_texto(mensagem)
    if pagamentos or analise["negociacao"]:
        return {"tipo": "pagamento", "formas": pagamentos, "negociacao": analise["negociacao"]}
    return None

def fluxo_documento_juridico(mensagem):
    """Detecta pedido/revisão/envio de modelo de documento jurídico."""
    docs = extrair_documentos(mensagem)
    if docs:
        return {"documentos": docs}
    return None

import os, traceback
import spacy, spacy.util

USE_SPACY = os.getenv("USE_SPACY", "true").lower() == "true"
SPACY_MODEL = os.getenv("SPACY_MODEL", "pt_core_news_sm")

nlp = None
if USE_SPACY:
    try:
        if not spacy.util.is_package(SPACY_MODEL):
            print(f"AVISO: '{SPACY_MODEL}' não é pacote registrado do spaCy. Tentando carregar mesmo assim...")
        nlp = spacy.load(SPACY_MODEL)
        print(f"✅ spaCy carregado: {SPACY_MODEL} | pipes={nlp.pipe_names}")
    except Exception:
        print("⚠️  Falha ao carregar spaCy. Detalhes:")
        traceback.print_exc()
        print("AVISO: Modelo spaCy não encontrado. Usando função mock para testes.")
        # Mock simples para permitir testes sem o modelo
        class MockNLP:
            def __call__(self, text):
                return MockDoc(text)

        class MockDoc:
            def __init__(self, text):
                self.text = text
                self.ents = []

            def __iter__(self):
                return iter([MockToken(word) for word in self.text.split()])

        class MockToken:
            def __init__(self, text):
                self.text = text
                self.lemma_ = text.lower()

        nlp = MockNLP()
else:
    print("AVISO: USE_SPACY=false — usando função mock.")
    class MockNLP:
        def __call__(self, text):
            return MockDoc(text)

    class MockDoc:
        def __init__(self, text):
            self.text = text
            self.ents = []

        def __iter__(self):
            return iter([MockToken(word) for word in self.text.split()])

    class MockToken:
        def __init__(self, text):
            self.text = text
            self.lemma_ = text.lower()

    nlp = MockNLP()


def analisar_texto(text):
    doc = nlp(text)
    resultado = {
        "tokens": [token.text for token in doc],
        "lemmas": [token.lemma_ for token in doc],
        "nomes": [],
        "datas": [],
        "horarios": [],
        "locais": [],
        "emails": [],
        "documentos": [],
        "oab": [],
        "valores": [],
        "pagamentos": [],
        "areas_direito": [],
        "escritorio": [],
        "canal": [],
        "intencao": [],
        "status": [],
        "cliente": [],
        "advogado": [],
        "erro_correcoes": [],
        "checklist_docs": [],
        "negociacao": [],
        "indicacao": [],
        "resumo": [],
        "raw_doc": doc
    }

    # --- NER spaCy
    for ent in doc.ents:
        if ent.label_ == "PER":
            resultado["nomes"].append(ent.text.title())
        elif ent.label_ in ["DATE"]:
            resultado["datas"].append(ent.text)
        elif ent.label_ in ["TIME"]:
            resultado["horarios"].append(ent.text)
        elif ent.label_ == "LOC":
            resultado["locais"].append(ent.text.title())
        elif ent.label_ == "ORG":
            resultado["escritorio"].append(ent.text.title())
        elif ent.label_ == "MISC":
            resultado["areas_direito"].append(ent.text.title())

    # --- Regexs customizadas para domínios jurídicos e variáveis do app
    resultado["emails"] = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    resultado["oab"] = re.findall(r'\d{3,10}\s*[A-Z]{2}', text, re.IGNORECASE)
    resultado["valores"] = re.findall(r'R?\$\s?\d{1,3}(\.\d{3})*,?\d*', text)
    resultado["documentos"] = re.findall(r'(procuração|contrato|petiç[ãa]o|documento[s]?|certidão|RG|CPF|carteira de trabalho)', text, re.IGNORECASE)
    resultado["pagamentos"] = re.findall(r'(pix|boleto|parcelamento|permuta|cart[aã]o|dinheiro|transfer[eê]ncia)', text, re.IGNORECASE)
    resultado["areas_direito"] += re.findall(r'(civil|trabalhista|fam[ií]lia|consumidor|imobili[aá]rio|previdenci[aá]rio|penal|empresarial|tribut[áa]rio)', text, re.IGNORECASE)
    resultado["canal"] = re.findall(r'(telefone|video-chamada|mensagem|whatsapp|e-mail|teams|zoom|meet|presencial)', text, re.IGNORECASE)
    resultado["erro_correcoes"] = re.findall(r'(desculpa|corrigir|corrigi|err[ei]|ignore|retificar|retifica[cç][aã]o)', text, re.IGNORECASE)
    resultado["checklist_docs"] = re.findall(r'(faltou|pendente|enviar documento|esqueci|lembrete|documento pendente)', text, re.IGNORECASE)
    resultado["negociacao"] = re.findall(r'(parcelar|permuta|desconto|condi[cç][aã]o especial|negociar|pagamento em bens|proposta de pagamento)', text, re.IGNORECASE)
    resultado["indicacao"] = re.findall(r'(indica[cç][aã]o|encaminhar|especialista|outro advogado|referenciar)', text, re.IGNORECASE)
    resultado["resumo"] = re.findall(r'(resumo|sum[aá]rio|estat[ií]stica|relat[oó]rio|consolidado)', text, re.IGNORECASE)

    # --- Intenções detalhadas (priorize ordem do fluxo!)
    intencoes = []
    if re.search(r'(agendar|marcar|consulta|hor[aá]rio|conversa|agenda|atendimento)', text, re.IGNORECASE):
        intencoes.append("agendamento")
    if re.search(r'(status|andamento|protocolo|prazo|audi[êe]ncia|atualiza[çc][aã]o|espera|retorno)', text, re.IGNORECASE):
        intencoes.append("status_processo")
    if re.search(r'(documento|enviar|anexo|arquivo|pendente|faltando)', text, re.IGNORECASE):
        intencoes.append("documento")
    if re.search(r'(honor[aá]rios|pagamento|forma de pagamento|cobran[çc]a|permuta|desconto|proposta)', text, re.IGNORECASE):
        intencoes.append("pagamento")
    if re.search(r'(minuta|peti[cç][aã]o|modelo|aprovar|revis[aã]o|redigir|corrigir)', text, re.IGNORECASE):
        intencoes.append("documento_juridico")
    if re.search(r'(indica[cç][aã]o|especialista|encaminhar|refer[êe]ncia)', text, re.IGNORECASE):
        intencoes.append("indicacao")
    if re.search(r'(onboarding|cadastrar|cadastro|inscri[cç][aã]o|novo advogado|novo cliente)', text, re.IGNORECASE):
        intencoes.append("onboarding")
    if re.search(r'(revisar|revis[aã]o|corrigir|corrigi)', text, re.IGNORECASE):
        intencoes.append("revisao")
    if re.search(r'(lembrete|aviso|notifica[cç][aã]o|alerta)', text, re.IGNORECASE):
        intencoes.append("lembrete")
    if re.search(r'(cancelar|alterar|remarcar|excluir|deletar)', text, re.IGNORECASE):
        intencoes.append("cancelar_agendamento")
    if re.search(r'(perguntar|consultar|duvida|informa[cç][aã]o)', text, re.IGNORECASE):
        intencoes.append("duvida")
    resultado["intencao"] = intencoes

    # --- Status (pode expandir)
    if re.search(r'(pago|quitado|em aberto|aguardando|pendente|em andamento|conclu[ií]do|fechado|encerrado)', text, re.IGNORECASE):
        resultado["status"].append(re.search(r'(pago|quitado|em aberto|aguardando|pendente|em andamento|conclu[ií]do|fechado|encerrado)', text, re.IGNORECASE).group(1))

    # --- Cliente/Advogado identificado por menção direta
    if re.search(r'(cliente|usu[aá]rio|titular)', text, re.IGNORECASE):
        resultado["cliente"].append("mencionado")
    if re.search(r'(advogado|contratante|profissional)', text, re.IGNORECASE):
        resultado["advogado"].append("mencionado")

    return resultado

# Funções helpers para onboarding, pagamento, status, documentos, etc.
def extrair_nome(text):
    PALAVRAS_INVALIDAS = [
        'bom dia', 'boa tarde', 'boa noite', 'olá', 'oi', 'saudações',
        'hello', 'hi', 'good morning', 'good afternoon', 'good evening',
        'cnpj', 'cpf', 'sim', 'não', 'autônomo'
    ]
    nomes = analisar_texto(text)["nomes"]
    nome = None
    if nomes and len(nomes[0].split()) > 1:
        nome = nomes[0]
    else:
        nome_regex = re.search(r'(?:meu nome é|sou|aqui é|dr\.?|dra\.?)\s*([a-záéíóúâêôãõç]{2,}(?:\s+[a-záéíóúâêôãõç]{2,})+)', text, re.IGNORECASE)
        if nome_regex:
            nome = nome_regex.group(1).title()
        elif nomes:
            nome = nomes[0]
    if nome and nome.lower() in PALAVRAS_INVALIDAS:
        return None
    return nome

def extrair_oab(text):
    """Extrai número e estado da OAB, retornando (numero, uf) ou (None, None)."""
    # OAB 123456 SP, 123456/SP, 123456-SP, OAB/SP 123456
    match = re.search(r'(?:OAB[ /-]*)?(?:([A-Z]{2})[ /-]*)?(\d{4,8})(?:[ /-]*)?([A-Z]{2})?', text, re.IGNORECASE)
    if match:
        uf1, num, uf2 = match.groups()
        uf = uf1 or uf2
        if num and uf:
            return num, uf.upper()
    return None, None

def extrair_email(text):
    """Extrai o primeiro e-mail válido encontrado no texto."""
    email_regex = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if email_regex:
        return email_regex.group(0)
    return None

def extrair_nome_escritorio(text):
    """Extrai nome de escritório de advocacia."""
    if "autônomo" in text.lower() or "não tenho" in text.lower():
        return "Autônomo"
    # Tenta extrair pela entidade ORG do spaCy
    analise = analisar_texto(text)
    if analise["escritorio"]:
        return analise["escritorio"][0]
    
    # Regex para padrões como "Escritório de Advocacia X", "X Advogados"
    escritorio_regex = re.search(
        r'(escrit[oó]rio de advocacia\s+([a-zA-Z\s]+)|([a-zA-Z\s]+)\s+advogados)',
        text,
        re.IGNORECASE
    )
    if escritorio_regex:
        # Retorna o segundo ou terceiro grupo de captura, que contém o nome
        return (escritorio_regex.group(2) or escritorio_regex.group(3)).strip().title()
    return None

def extrair_area(text):
    # Tenta spaCy/regex padrão
    areas = analisar_texto(text)["areas_direito"]
    # Lista de áreas válidas em português
    AREAS_VALIDAS = [
        'Civil', 'Trabalhista', 'Família', 'Consumidor', 'Imobiliário',
        'Previdenciário', 'Penal', 'Empresarial', 'Tributário'
    ]
    if areas:
        # Filtra apenas áreas válidas em português
        filtradas = [a.title() for a in areas if a.title() in AREAS_VALIDAS]
        if filtradas:
            return list(set(filtradas))
    # Regex para áreas comuns
    area_regex = re.findall(r'(civil|trabalhista|fam[ií]lia|consumidor|imobili[aá]rio|previdenci[aá]rio|penal|empresarial|tribut[áa]rio)', text, re.IGNORECASE)
    filtradas = [a.title() for a in area_regex if a.title() in AREAS_VALIDAS]
    return list(set(filtradas))
def extrair_intencao(text): return analisar_texto(text)["intencao"]
def extrair_pagamento(text): return analisar_texto(text)["pagamentos"]
def extrair_status(text): return analisar_texto(text)["status"]
def extrair_canal(text): return analisar_texto(text)["canal"]
def extrair_documentos(text): return analisar_texto(text)["documentos"]
def extrair_lembretes(text): return analisar_texto(text)["checklist_docs"]
def extrair_numero_processo(text):
    """Extrai número de processo jurídico no formato CNJ ou outros formatos comuns."""
    # Formato CNJ: NNNNNNN-DD.YYYY.J.TR.OOOO
    cnj_match = re.search(r'\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}', text)
    if cnj_match:
        return cnj_match.group(0)
    
    # Formato mais simples, apenas números, com 15 a 25 dígitos
    simple_match = re.search(r'\b\d{15,25}\b', text)
    if simple_match:
        return simple_match.group(0)
        
    return None

# Dispatcher para fluxos de cliente
def dispatcher_fluxos_cliente(mensagem):
    """Dispatcher que testa todos os fluxos de cliente e retorna o primeiro que bater."""
    fluxos = [
        ("relato_caso", fluxo_relato_caso),
        ("consulta_andamento_cliente", fluxo_consulta_andamento_cliente),
        ("enviar_documento_cliente", fluxo_enviar_documento_cliente),
        ("agendar_consulta_cliente", fluxo_agendar_consulta_cliente),
        ("atualizar_cadastro_cliente", fluxo_atualizar_cadastro_cliente),
        # Adicione outros fluxos do cliente conforme você expandir
    ]
    for nome_fluxo, funcao_fluxo in fluxos:
        resultado = funcao_fluxo(mensagem)
        if resultado:
            return nome_fluxo, resultado
    return None, None

# Dispatcher para fluxos de advogado
def dispatcher_fluxos_advogado(mensagem):
    """Dispatcher que testa todos os fluxos de advogado e retorna o primeiro que bater."""
    fluxos = [
        ("onboarding_advogado", fluxo_onboarding_advogado),
        ("aprovacao_peticao", fluxo_aprovacao_peticao),
        ("alerta_prazo", fluxo_alerta_prazo),
        ("documento_juridico", fluxo_documento_juridico),
        ("revisao_documento", fluxo_revisao_documento),
        # Adicione outros fluxos do advogado conforme você expandir
    ]
    for nome_fluxo, funcao_fluxo in fluxos:
        resultado = funcao_fluxo(mensagem)
        if resultado:
            return nome_fluxo, resultado
    return None, None

# Exemplo de uso:
if __name__ == "__main__":
    texto = "Olá, meu nome é Joana Barbosa. OAB 123456 SP, preciso de uma petição para direito civil e quero agendar consulta por video-chamada. Posso pagar via PIX. Esqueci de enviar a procuração, desculpa!"
    print(analisar_texto(texto))
    print("Nome:", extrair_nome(texto))
    print("OAB:", extrair_oab(texto))
    print("Email:", extrair_email(texto))
    print("Áreas:", extrair_area(texto))
    print("Intenção:", extrair_intencao(texto))
    print("Pagamentos:", extrair_pagamento(texto))
    print("Documentos:", extrair_documentos(texto))
    print("Lembretes:", extrair_lembretes(texto))
