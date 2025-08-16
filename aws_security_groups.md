🔐 Configuração de Segurança (CPU & GPU)
CPU (Servidor Principal — Flask / API / Painel)

Inbound (Regras de Entrada):

22/TCP → Origem: Seu IP residencial

80/TCP (HTTP) → Origem: 0.0.0.0/0

443/TCP (HTTPS) → Origem: 0.0.0.0/0

8000/TCP (Flask interno) → Origem: 0.0.0.0/0 (ou restrito só para a GPU, se quiser mais segurança)

Outbound (Regras de Saída):

Todos os protocolos → Destino: 0.0.0.0/0

GPU (Servidor LLM — Ollama / Modelos)

Inbound (Regras de Entrada):

22/TCP → Origem: Seu IP residencial

8000/TCP (Flask/LLM server) → Origem: Security Group da CPU

11434/TCP (Ollama service) → Origem: Security Group da CPU

Outbound (Regras de Saída):

Todos os protocolos → Destino: 0.0.0.0/0
