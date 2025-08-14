#Problemas gerais

- Como a llm não é chamada quando os fluxos são ativados, o assistente acaba ficando "seco" só funcional. Cria planilhas, cria eventos aleatoriamente sem nem confirar com o advogado contratante. Está parecendo uma metralhadora de criar eventos, enviar emails, criar documentos, mas não está repondendo de forma educada. Talvez poderia ter um mecanismo de retorno quando a função é feita com sucesso (ex. atualização/criação de planilha/criação de evento/) além, disso deveria ativar o assistente para confirmar com o advogado se quer criar tantas coisas só com um simples comando. O assistente deveria confirmar com o advogado antes da criação de eventos por exemplo. perguntar coisas básicas educadamente ao final das tarefas, por exemplo, "precisa de mais alguma coisa?" seria muito bom. 

- Acho que a LLM deve ser ativada mais vezes, não só como fallback quando o fluxo falhar, se não fica engessado e parecendo um robô.



1. fluxo_onboarding_advogado → Coleta dados para configurar CRM: nome, OAB, especialidade, escritório e como organiza seus clientes (por área, urgência, data etc.). 
Nesta função o bot deve coletar dados do advogado para configurar seu CRM, deve pegar ome, OAB, especialidade, escritório e como organiza seus clientes (por área, urgência, data etc.) e de que forma (se é planilha, se é alguma plataforma especializada, se é à mão ou mesmo se não organiza contatos). O bot vai auxiliar o advogado a organizar sua vida planejar os clientes (se for manualmente, recebendo cliente por cliente pelas mensagens do advogado. Se o advogado utilizar algum serviço já de crm, o assistente pode pedí-lo para exportar uma planilha em CSV para que ela faça o CRM do advogado. 

Essa etapa é muito importante, a montagem do CRM em planilha, pois ela servirá de banco de dados da Assistente virtual. Qualquer atualização de atendimento ao cliente, de processo ou de consulta, ela usará essa planilha. 

2. fluxo_aprovacao_peticao → Registra petição aprovada. 
   Teste: "A petição está aprovada, vou protocolar." 



3. fluxo_alerta_prazo → Gera lembrete de prazo/audiência.
   Teste: "Prazo do recurso de Frderico Alves vence na semana que vem, não se esqueça de me lembrar na segunda-feira."
Essa função deve criar alertas de lembretes na própria planilha do CRM (entendeu, a planilha do CRM é o carro chefe do app ela vai ser o banco de dados e vai comandar o que o assistente vai avisar ou não, o que é urgente de ser avisado no dia ou não. Ela devve ter a consciencia de que dia é hoje e tudo para ficar sempre afiada com as tarefas que o advogado precisa priorizar."

- checa lembretes nas planilhas por data/urgência/ e envia mensagem para o advogado. 
- Cria lembretes à pedido do advogado.
- Cria lembretes a partir de eventos no Google (exemplo, Amanhã tem a audiência do caso do MAtheus)
 

4. fluxo_honorarios → Registra valores de honorários do cliente no CRM.
   Teste: "Os honorários são de R$ 5.000,00."
- registra o valor de honorários combinado na planilha do CRM

5. fluxo_documento_juridico → Envia ou armazena modelo de documento.
   Teste: "Preciso de um modelo de contrato de prestação de serviços."
- função para auxiliar o advogado no seu dia a dia, o assistente deve redigir modelos de documentos pedidos pelo advogado. Se for a primeira vez ele armazena esse documento em uma pasta do google drive chamada "modelos de documentos". O assistente também deve checar se o documento pedido pelo advogado já nao está nessa pasta antes de redigir e enviá-lo para o advogado. 

6. fluxo_envio_documento_cliente → Salva documento para cliente.
   Teste: "Enviar cópia da petição ao João MArcos Silva."
   Envia cópia de documento para cliente epecífico. O assitente só pelo nome completo do cliente ou outro dado como o número do processo, procura o cliente na planilha de CRM identifica o contato e envia o documento que o advogado pediu para o cliente (a pasta dos documentos de cada cliente ficam no drive em uma pasta como o nome completo do cliente) o assistente também armazena o documento do respectivo cliente na pasta. 
   
7. fluxo_consulta_andamento → Consulta andamento processual.
   Teste: "Verificar andamento do processo 0000000-00.0000.0.00.0000."
Consulta o andamento do processo nas informações da planilha do CRM e retorna a informação para o advogado.

8. fluxo_pagamento_fora_padrao → Registra pagamento fora do combinado.
   Teste: "O cliente pagou um valor menor que o acordado."
Identifica pagamento do cliente, compara com o que foi combinado (todas as informações na planilha do CRM) e avisa o advogado se o cliente pagou menos ou fora do combinado. 

9. fluxo_indicacao → Registra cliente indicado.
   Teste: "O João me indicou a Maria como cliente."
Registra indicações de clientes na planilha do CRM 

10. fluxo_documento_pendente → Marca documento pendente.
    Teste: "Falta o comprovante de endereço."
- Identifica se o cliente enviou todos os documentos para o cadastro (Documento de identificação com foto, e comprovante de endereço)  e, se não, marca como documento pendente.
Aceita 
- Registra documentos pendentes de clientes no CRM à pedido do advogado.

11. fluxo_revisao_documento → Solicita revisão.
    Teste: "Preciso que revise essa contestação."
- Assistente recebe texto de documento via chat e faz revisão ortográfica e de erros gramaticais e retorna para o advogado o texto revisado. pelo chat ou pelo email pergunta a preferÊncia de envio para o advogado.

12. fluxo_status_negociacao → Registra status de negociação.
    Teste: "Negociação está em fase final." identifica em qque fase da negociação está a conversa com o cliente e registra na planilha de CRM.

13. fluxo_decisao_permuta → Atualiza decisão sobre permuta no CRM.
    Teste: "Cliente aceitou a permuta." 

14. fluxo_sumiço_cliente → Marca cliente inativo.
    Teste: "Cliente sumiu desde semana passada."
Na planilha do crm

15. fluxo_update_clientes_aguardando → Atualiza clientes aguardando.
    Teste: "Atualizar lista de clientes aguardando retorno."
Atualiza lista de clientes do CRM

16. fluxo_update_documento_pendente → Atualiza status de documentos.
    Teste: "Atualizar situação dos documentos pendentes de João Henrique Rocha."

17. fluxo_nao_atendimento_area → Marca caso como não atendido por área.
    Teste: "Este caso do Marcos Amadeu é criminal. Não atuo em direito criminal."
MArca no CRM que não atua em área criminal e busca na lista de advogados parceiros de indicação se tem alguém da área. Sugere ao advogado contratante alguem da lista para indicar para o cliente, com a confirmação, indica para o cliente o advogado da lista de parceiros. 

18. fluxo_status_multiplos_processos → Registra status de múltiplos processos.
    Teste: "Verificar processos 123 e 456."
Identifica e busca na planilha de processos e retorna status. 

19. fluxo_notificacao_cliente → Envia notificação ao cliente.
    Teste: "Avisar cliente que audiência foi marcada."
Acha numero do cliente e nome na planilha e envia mensagem que o advogado pediu para avisar. Como se fosse uma secretária. 

20. fluxo_alterar_cancelar_agendamento → Atualiza/cancela compromisso.
    Teste: "Cancelar reunião de amanhã."
- cancela eventos no google calendar, sempre confirmar nome do evento data e hora antes de cancelar.

21. fluxo_resumo_estatisticas → Gera relatório.
    Teste: "Quantos casos foram fechados este mês?"
Procura nas planilhas e retorna o resultado. 

22. fluxo_lembrete_audiencia → Cria lembrete de audiência.
    Teste: "Me lembrar da audiência dia 20."

23. fluxo_enviar_resumo_caso → Envia resumo de caso.
    Teste: "Me envie o resumo do caso do cliente João." Identifica o resumo de caso na planilha CRM do respectivo cliente e manda para o advogado. 


👤 Fluxos do Cliente (`tipo_usuario = cliente`):
1. relato_caso → Registra relato e salva no CRM.
   Cliente: "Fui demitido sem justa causa e quero meus direitos."
2. consulta_andamento_cliente → Solicita dados para consulta processual.
   Cliente: "Quero saber o andamento do meu processo."
3. agendar_consulta_cliente → Cria evento no Calendar.
   Cliente: "Quero agendar reunião amanhã às 15h."
4. enviar_documento_cliente → Salva documento no Drive e CRM.
   Cliente: Envia arquivo ou foto.
5. fluxo_nao_detectado → Resposta padrão.
   Cliente: Mensagem fora dos fluxos acima.

