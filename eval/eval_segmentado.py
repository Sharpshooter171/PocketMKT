import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# Caminho local do snapshot completo (use para tokenizer e modelo)
SNAPSHOT_PATH = "/home/ubuntu/.cache/huggingface/hub/models--mistralai--Mistral-7B-Instruct-v0.2/snapshots/63a8b081895390a26e140280378bc85ec8bce07a"
LORA_DIR = "mistral-finetune-advocacia-45k/checkpoint-3750"

tokenizer = AutoTokenizer.from_pretrained(SNAPSHOT_PATH)
tokenizer.pad_token = tokenizer.eos_token
bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
base_model = AutoModelForCausalLM.from_pretrained(SNAPSHOT_PATH, quantization_config=bnb_config, device_map="auto")
model = PeftModel.from_pretrained(base_model, LORA_DIR)

def responder(prompt, max_new_tokens=80):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0,
            top_p=0.9,
            repetition_penalty=1.8,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )
    resposta = tokenizer.decode(output[0], skip_special_tokens=True)
    resposta = resposta.split("[FIM]")[0].strip()  # Pega só até o token de parada
    return resposta

# System prompts por segmento
SYSTEM_ONBOARDING = (
    "Você é um assistente virtual que faz a triagem inicial em um escritório de advocacia. Sempre cumprimente o usuário, colete nome completo e motivo do contato. Nunca forneça informações jurídicas, técnicas ou invente dados. Encaminhe dúvidas técnicas para o advogado responsável. Use respostas curtas, diretas, profissionais e acolhedoras. Se o cliente já informou nome e motivo, agradeça, NÃO repita perguntas e informe os próximos passos, incluindo agendamento, se necessário."
)
SYSTEM_CLIENTE = (
    "Você é um assistente virtual de triagem para um escritório de advocacia. O cliente já está cadastrado. Responda apenas dúvidas administrativas, de agenda, documentos pendentes e rotinas do escritório. Nunca forneça opiniões jurídicas, detalhes técnicos, leis ou prazos. Não invente procedimentos. Se a dúvida for técnica, explique que o advogado responderá posteriormente. Use frases curtas, profissionais, acolhedoras e SEM repetir a coleta de dados. Reconheça informações já fornecidas pelo cliente e oriente sobre próximos passos."
)
SYSTEM_ADVOGADO = (
    "Você é um assistente virtual que auxilia advogados em rotinas administrativas do escritório. Responda apenas dúvidas sobre documentos, prazos, agenda, estatísticas e fluxo de atendimento. Nunca dê opiniões jurídicas nem trate de casos específicos de clientes. Se a dúvida for jurídica, encaminhe ao setor responsável. Use sempre respostas curtas, claras e objetivas."
)

# Prompts de eval segmentados
eval_cases = [
    # Onboarding
    (SYSTEM_ONBOARDING, "Oi, sou Mariana Oliveira. Quero saber o andamento do meu processo. [FIM]"),
    (SYSTEM_ONBOARDING, "Olá, perdi meus documentos e preciso de orientação. [FIM]"),
    (SYSTEM_ONBOARDING, "Bom dia, aqui é Rafael. Gostaria de atualizar meus dados cadastrais. [FIM]"),
    (SYSTEM_ONBOARDING, "Preciso de um advogado para um caso trabalhista urgente! [FIM]"),
    (SYSTEM_ONBOARDING, "Fala aí! Quero agendar consulta sobre divórcio. [FIM]"),
    (SYSTEM_ONBOARDING, "Volto depois... [FIM]"),
    (SYSTEM_ONBOARDING, "kkk esqueci de informar meu nome! [FIM]"),
    (SYSTEM_ONBOARDING, "🤷‍♂️ perdi a hora do atendimento, o que faço? [FIM]"),
    # Cliente cadastrado
    (SYSTEM_CLIENTE, "Preciso cancelar uma consulta. [FIM]"),
    (SYSTEM_CLIENTE, "Já enviei meus documentos, o que falta? [FIM]"),
    (SYSTEM_CLIENTE, "Qual o horário de funcionamento? [FIM]"),
    (SYSTEM_CLIENTE, "Tem cobrança pendente no meu cadastro? [FIM]"),
    (SYSTEM_CLIENTE, "Pode remarcar meu atendimento pra sexta? [FIM]"),
    (SYSTEM_CLIENTE, "O advogado já recebeu meu contrato? [FIM]"),
    (SYSTEM_CLIENTE, "Oi... [FIM]"),
    (SYSTEM_CLIENTE, "Obg pelo suporte! [FIM]"),
    (SYSTEM_CLIENTE, "Preciso falar urgente com o financeiro. [FIM]"),
    (SYSTEM_CLIENTE, "Agradecido, valeu! [FIM]"),
    # Advogado
    (SYSTEM_ADVOGADO, "Como aprovo uma petição do cliente? [FIM]"),
    (SYSTEM_ADVOGADO, "Atualize a lista de clientes aguardando contato. [FIM]"),
    (SYSTEM_ADVOGADO, "Preciso de alerta de prazo para petição. [FIM]"),
    (SYSTEM_ADVOGADO, "Como reviso documentos antes do envio? [FIM]"),
    (SYSTEM_ADVOGADO, "Quero receber notificação de audiência. [FIM]"),
    (SYSTEM_ADVOGADO, "Agendamento alterado com sucesso? [FIM]"),
    (SYSTEM_ADVOGADO, "Pode me enviar o resumo estatístico do mês? [FIM]"),
    (SYSTEM_ADVOGADO, "Oi, tudo certo? [FIM]"),
    (SYSTEM_ADVOGADO, "Preciso cancelar um agendamento. [FIM]"),
    (SYSTEM_ADVOGADO, "Volto depois... [FIM]"),
    # Edge cases
    (SYSTEM_CLIENTE, "Qual o prazo para recurso de apelação? [FIM]"),
    (SYSTEM_CLIENTE, "Pode me dar um parecer sobre meu caso? [FIM]"),
    (SYSTEM_CLIENTE, "Advogado, o que devo fazer para recorrer? [FIM]"),
    (SYSTEM_CLIENTE, "Qual seu nome? [FIM]"),
    (SYSTEM_CLIENTE, "Você pode consultar processos no tribunal? [FIM]"),
    (SYSTEM_CLIENTE, "Como está o tempo aí? [FIM]"),
    (SYSTEM_CLIENTE, "Me recomenda um filme? [FIM]"),
    (SYSTEM_CLIENTE, "Tem vaga de estacionamento? [FIM]"),
    (SYSTEM_CLIENTE, "Qdo vai ser minha audiência? [FIM]"),
    (SYSTEM_CLIENTE, "Urgente urgente! Preciso saber do andamento! [FIM]"),
    (SYSTEM_CLIENTE, "Não recebi retorno ainda, o que está havendo? [FIM]"),
    # Ruídos/gírias/erros
    (SYSTEM_CLIENTE, "blz, quero remarcar 👍 [FIM]"),
    (SYSTEM_CLIENTE, "Obg, vcs são nota 10! [FIM]"),
    (SYSTEM_CLIENTE, "Fala, doutor! Pode ver pra mim? [FIM]"),
    (SYSTEM_CLIENTE, "Pra que serve essa audiência msm? [FIM]"),
    (SYSTEM_CLIENTE, "Tô perdido aqui kkkk [FIM]"),
    (SYSTEM_CLIENTE, "🤔 pode ver se falta doc? [FIM]"),
]

with open("eval_results_segmentado.txt", "w", encoding="utf-8") as f:
    for i, (system_prompt, usuario) in enumerate(eval_cases):
        prompt = f"{system_prompt}\nUsuário: {usuario}\nAtendente:"
        resposta = responder(prompt)
        print(f"\nPrompt {i+1}:\nUsuário: {usuario}\nResposta: {resposta}\n{'-'*40}")
        f.write(f"Prompt {i+1}:\nUsuário: {usuario}\nResposta: {resposta}\n{'-'*40}\n")
