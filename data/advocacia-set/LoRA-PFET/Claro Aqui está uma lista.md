Claro! Aqui está uma lista prática de comandos úteis para uso em servidores Linux (como sua GPU AWS), incluindo checagem de RAM, processos, ambientes virtuais, e mais:

---

## 🔍 Checagem de RAM, CPU e Disco

```bash
# Ver uso de RAM e SWAP
free -h

# Ver uso de CPU, RAM e processos em tempo real
htop
# (Se não tiver, instale: sudo apt update && sudo apt install htop)

# Ver uso de disco
df -h

# Ver espaço ocupado por pastas (exemplo: na pasta atual)
du -sh *
```

---

## 🐍 Checagem de Processos

```bash
# Listar todos os processos Python rodando
ps aux | grep python

# Ver detalhes de um processo específico (exemplo: PID 1234)
ps -fp 1234

# Matar um processo (substitua <PID> pelo número do processo)
kill <PID>
# Forçar kill se necessário
kill -9 <PID>
```

---

## 🐍 Ambientes Virtuais Python

```bash
# Criar um novo ambiente virtual chamado 'venv'
python3 -m venv venv

# Ativar o ambiente virtual (no bash/zsh)
source venv/bin/activate

# Desativar o ambiente virtual
deactivate

# Instalar pacotes no ambiente virtual
pip install nome-do-pacote

# Listar pacotes instalados
pip list

# Gerar requirements.txt
pip freeze > requirements.txt

# Instalar tudo do requirements.txt
pip install -r requirements.txt
```

---

## 📝 Outras Dicas Úteis

```bash
# Verificar se uma porta está aberta (exemplo: 8000)
sudo lsof -i :8000

# Ver logs do sistema (últimas 30 linhas)
dmesg | tail -30

# Ver IP público da máquina
curl ifconfig.me

# Ver IPs locais
ip a
```

---

## 🛠️ Instalar pacotes úteis

```bash
# Instalar htop, tmux, unzip, curl, git
sudo apt update
sudo apt install htop tmux unzip curl git
```

---

## 🖥️ Usando tmux para manter sessões ativas

```bash
# Iniciar uma nova sessão tmux
tmux new -s minha_sessao

# (Dentro do tmux) Rodar seu comando normalmente
python3 llm_server.py

# Para sair do tmux sem encerrar o processo: Ctrl+b depois solte e pressione d

# Para voltar à sessão tmux
tmux attach -t minha_sessao

# Listar sessões tmux
tmux ls
```

🧹 Limpeza pesada de arquivos e cache

# Limpar cache do apt
sudo apt-get clean
sudo apt-get autoclean

# Limpar arquivos temporários do sistema
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*

# Limpar cache do usuário atual
rm -rf ~/.cache/*

# Limpar cache do pip
rm -rf ~/.cache/pip

# Limpar cache do HuggingFace/Transformers (ajuste o caminho se necessário)
rm -rf ~/.cache/huggingface
rm -rf ~/.cache/torch
rm -rf /opt/dlami/nvme/hf_cache/*

# Limpar logs antigos (cuidado!)
sudo journalctl --vacuum-time=7d
sudo rm -rf /var/log/*.gz /var/log/*.[0-9]

#Limpar cache do modelo:
rm -rf /opt/dlami/nvme/hf_cache/mistralai/Mistral-7B-Instruct-v0.2*

💾 Checagem de disco e arquivos grandes

# Ver uso de disco por partição
df -h

# Ver uso de disco por pasta (na pasta atual)
du -sh *

# Encontrar as 20 maiores pastas/arquivos a partir da raiz
sudo du -ahx / | sort -rh | head -20

# Encontrar arquivos maiores que 500MB
find / -type f -size +500M -exec ls -lh {} \; 2>/dev/null | sort -k 5 -rh | head -20

# Ver uso de disco por usuário
sudo du -sh /home/*

# Ver espaço ocupado por arquivos ocultos na home
du -sh ~/.*

🧰 Manutenção e processos

# Listar processos mais pesados (CPU/memória)
ps aux --sort=-%mem | head -20
ps aux --sort=-%cpu | head -20

# Matar todos os processos Python do usuário atual
pkill -u $USER python   

# Ver processos em estado "D" (esperando I/O, geralmente travados)
ps aux | awk '$8 ~ /D/ {print $0}'

# Limpar processos zumbis (normalmente o kernel faz isso, mas pode tentar)
kill -HUP -1

🛠️ Outras dicas de manutenção

# Verificar espaço livre em disco e inodes
df -h
df -i

# Verificar arquivos abertos por um processo (exemplo: PID 1234)
lsof -p 1234

# Verificar conexões de rede abertas
ss -tulnp

# Verificar uso de GPU (NVIDIA)
nvidia-smi

Aqui está uma lista de comandos úteis para instalar e verificar os requisitos em uma instância GPU da AWS:

### 1. **Instalação básica e verificação de GPU**
```bash
# Atualizar sistema
sudo apt-get update && sudo apt-get upgrade -y

# Instalar drivers NVIDIA (em instâncias como p3, g4, g5, etc.)
sudo apt-get install -y nvidia-driver-535  # ou versão mais recente

# Verificar se a GPU está reconhecida
nvidia-smi

# Verificar versão do CUDA (se instalado)
nvcc --version
```

### 2. **Instalar PyTorch com suporte a GPU**
```bash
# Instalar PyTorch com CUDA (versão compatível com seu hardware)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verificar se PyTorch reconhece a GPU
python3 -c "import torch; print(torch.cuda.is_available()); print(torch.__version__)"
```

### 3. **Instalar transformers e dependências**
```bash
# Instalar pacotes necessários
pip3 install transformers peft accelerate sentencepiece bitsandbytes

# Verificar instalação
python3 -c "from transformers import __version__; print(__version__)"
python3 -c "from peft import __version__; print(__version__)"
```

### 4. **Outras ferramentas úteis**
```bash
# Monitorar uso de GPU em tempo real
watch -n 1 nvidia-smi

# Verificar versão do Python
python3 --version

# Listar pacotes Python instalados
pip3 list

# Criar/ativar ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate
```

### 5. **Se precisar reinstalar do zero**
```bash
# Remover pacotes conflitantes
pip3 uninstall torch transformers peft -y

# Instalar versões específicas (exemplo)
pip3 install transformers==4.40.0 peft==0.10.0
```

### 6. **Verificar instalação completa**
```python
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, PeftConfig
import torch
print('Tudo instalado com sucesso!')
print(f'PyTorch CUDA: {torch.cuda.is_available()}')
"
```

### Observações:
1. Use `conda` se preferir gerenciamento de ambientes mais robusto
2. Em instâncias AWS, considere usar imagens DLAMI (Deep Learning AMI) que já vem com muitos pacotes pré-instalados
3. Sempre verifique a compatibilidade entre versões de PyTorch/CUDA/transformers

Quer que eu detalhe algum ponto específico?

#Abrir sessão no tmux:

tmux new -s llm
#Listar todas as sessões tmux ativas
tmux ls
#Para voltar a essa sessão:
tmux attach -t llm

