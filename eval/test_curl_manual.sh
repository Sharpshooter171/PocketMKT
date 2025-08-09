#!/bin/bash

# Script de testes manuais com curl para PocketMKT
# Uniforme: todas as chamadas usam POST /processar_atendimento

BASE_URL="http://127.0.0.1:5000"
ENDPOINT="${BASE_URL}/processar_atendimento"

echo "🚀 TESTES MANUAIS - PocketMKT"
echo "=============================="

# Teste de conectividade
echo "🔍 1. Testando conectividade..."
curl -s "${BASE_URL}/teste" | python3 -m json.tool
echo ""

# Teste Cliente - Relato de caso
echo "👥 2. Teste Cliente - Relato de caso trabalhista"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Fui demitido ontem sem justa causa, quero saber meus direitos.",
    "numero": "11999990001",
    "escritorio_id": "ESCRITORIO_TESTE",
    "tipo_usuario": "cliente"
  }' | python3 -m json.tool
echo ""

# Teste Cliente - Agendamento
echo "📅 3. Teste Cliente - Agendamento de consulta"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Gostaria de agendar uma consulta com o advogado para semana que vem.",
    "numero": "11999990001", 
    "escritorio_id": "ESCRITORIO_TESTE",
    "tipo_usuario": "cliente"
  }' | python3 -m json.tool
echo ""

# Teste Advogado - Onboarding
echo "👨‍💼 4. Teste Advogado - Onboarding"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Sou Ricardo Silva, OAB 123456 SP, ricardo@adv.com, especialista em trabalhista.",
    "numero": "11988887777",
    "escritorio_id": "ESCRITORIO_TESTE", 
    "tipo_usuario": "advogado"
  }' | python3 -m json.tool
echo ""

# Teste Advogado - Alerta de prazo
echo "⏰ 5. Teste Advogado - Alerta de prazo"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Quais prazos vencem nesta semana?",
    "numero": "11988887777",
    "escritorio_id": "ESCRITORIO_TESTE",
    "tipo_usuario": "advogado"
  }' | python3 -m json.tool
echo ""

# Teste Status das APIs Google
echo "📊 6. Status das integrações Google"
curl -s "${BASE_URL}/status" | python3 -m json.tool
echo ""

echo "✅ Testes manuais concluídos!"
echo "💡 Para mais testes, execute: python test_fluxos_advogado_cliente.py"
