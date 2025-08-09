# 🧪 Testes E2E - Integrações Google

Este diretório contém scripts para testar as integrações Google (Sheets, Calendar, Gmail) de forma End-to-End.

## 📁 Arquivos

### 🎯 Scripts Principais
- **`test_e2e_integracoes.py`** - Teste E2E completo com validação das 3 APIs
- **`exemplos_validacao.py`** - Exemplos isolados de cada integração
- **`setup_google_creds.py`** - Configurador de credenciais Google

### 📊 Scripts de Teste Básico  
- **`test_fluxos_advogado_cliente.py`** - Teste básico de fluxos (sem validação Google)

## 🚀 Como Executar

### 1️⃣ Preparar Ambiente
```bash
cd /home/igor-caldas/PocketMKT/eval

# Configurar credenciais Google
python setup_google_creds.py

# Instalar dependências (se necessário)
pip install google-api-python-client google-auth
```

### 2️⃣ Executar Testes E2E Completos
```bash
# Teste completo com validação Google APIs
python test_e2e_integracoes.py
```

### 3️⃣ Testar Integrações Isoladamente
```bash
# Exemplos específicos de cada integração
python exemplos_validacao.py
```

### 4️⃣ Teste Básico (sem Google)
```bash
# Teste simples de fluxos
python test_fluxos_advogado_cliente.py
```

## 🔧 Estrutura dos Testes E2E

### **Passo 1: Enviar Requisição**
- Cliente: `POST /processar_atendimento`
- Advogado: `POST /mensagem`

### **Passo 2: Validar Retorno JSON**
```json
{
  "resposta": "Caso registrado com sucesso!",
  "id_planilha": "1BxiMVs0XRA5nF...",
  "id_evento": "abc123def456...",
  "email_enviado": true
}
```

### **Passo 3: Validar APIs Google**
- **Google Sheets**: Verificar se planilha foi criada e dados salvos
- **Google Calendar**: Confirmar se evento foi agendado
- **Gmail**: Checar se email foi enviado

## 📊 Cenários de Teste

### 🎯 Cliente - Relato Completo
```python
{
    "mensagem": "Sou Maria Silva, CPF 123.456.789-00, fui demitida sem justa causa...",
    "validacoes_esperadas": {
        "planilha": True,    # Dados salvos no Sheets
        "email": True,       # Confirmação enviada
        "dados_extraidos": True
    }
}
```

### 📅 Cliente - Agendamento
```python
{
    "mensagem": "Preciso agendar consulta para segunda-feira à tarde...", 
    "validacoes_esperadas": {
        "calendario": True,  # Evento criado
        "email": True,       # Confirmação enviada
        "planilha": True     # Registro salvo
    }
}
```

### 👨‍💼 Advogado - Onboarding
```python
{
    "mensagem": "Sou Dr. Ricardo, OAB/SP 123456, email ricardo@adv.com...",
    "validacoes_esperadas": {
        "planilha": True,    # Planilha do escritório criada
        "email": True,       # Email de boas-vindas
        "dados_extraidos": True
    }
}
```

## 📈 Sistema de Scoring

### **Pontuação Total: 100 pontos**

#### **Validação JSON (50%)**
- ✅ ID Planilha retornado: **15 pts**
- ✅ ID Evento retornado: **15 pts** 
- ✅ Status Email retornado: **10 pts**
- ✅ Dados extraídos: **10 pts**

#### **Validação Google APIs (50%)**
- ✅ Planilha criada no Sheets: **20 pts**
- ✅ Evento criado no Calendar: **20 pts**
- ✅ Email enviado via Gmail: **10 pts**

## 📋 Relatórios Gerados

### **CSV Consolidado**
- Nome: `teste_e2e_integracoes_YYYYMMDD_HHMMSS.csv`
- Colunas: Cenário, Score, IDs, Validações, Detalhes

### **Estatísticas**
```
📈 Score médio: 85.0/100
📊 Google Sheets: 3/4 validados (75%)
📅 Google Calendar: 2/4 validados (50%) 
📧 Gmail: 4/4 validados (100%)
```

## 🔧 Configuração de Credenciais

### **Credenciais Reais (Recomendado)**
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie projeto ou selecione existente
3. Ative APIs: Sheets, Calendar, Gmail
4. Crie conta de serviço
5. Baixe JSON como `/home/igor-caldas/PocketMKT/credentials.json`

### **Credenciais Mock (Para testes)**
```bash
python setup_google_creds.py
# Escolha opção 1 para criar arquivo mock
```

## 🐛 Troubleshooting

### **Flask não está rodando**
```bash
# Verificar se Flask está ativo
curl http://127.0.0.1:5000/teste
```

### **Credenciais Google inválidas**
```bash
# Recriar credenciais
python setup_google_creds.py
```

### **APIs Google não habilitadas**
- Google Sheets API
- Google Calendar API  
- Gmail API

## 📊 Interpretando Resultados

### **Score 80-100%**: ✅ Excelente
- Todas as integrações funcionando
- JSON retornado corretamente
- APIs Google validadas

### **Score 60-79%**: ⚠️ Bom com problemas
- Fluxos detectados corretamente
- Algumas integrações falhando

### **Score 0-59%**: ❌ Necessita correção
- Fluxos não detectados
- Integrações não funcionando
- Verificar logs do Flask

## 🔄 Fluxo de Desenvolvimento

1. **Teste básico**: `test_fluxos_advogado_cliente.py`
2. **Debug individual**: `exemplos_validacao.py`
3. **Validação completa**: `test_e2e_integracoes.py`
4. **Análise**: Revisar CSV gerado
5. **Correções**: Ajustar código Flask
6. **Repetir**: Até atingir score desejado

---

💡 **Dica**: Execute primeiro os exemplos isolados para entender como cada integração funciona, depois execute o teste E2E completo.
