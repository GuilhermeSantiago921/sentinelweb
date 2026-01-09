# 🚀 INSTALAÇÃO RÁPIDA - SENTINELWEB

## Instalação Automatizada em Ubuntu

### 📋 Pré-requisitos

- ✅ **Servidor Ubuntu** (20.04, 22.04, ou 24.04)
- ✅ **Domínio** apontando para o servidor
- ✅ **Acesso root/sudo**

### ⚡ Instalação em 3 Comandos

```bash
# 1. Acesse seu servidor
ssh root@SEU_IP

# 2. Faça upload/clone dos arquivos para /opt/sentinelweb

# 3. Execute o instalador automático
cd /opt/sentinelweb
sudo bash install.sh
```

**Pronto!** O script instala tudo em 15-30 minutos:
- ✅ Docker & Docker Compose
- ✅ PostgreSQL 15
- ✅ Redis
- ✅ Nginx + SSL/TLS
- ✅ Firewall (UFW)
- ✅ Fail2Ban
- ✅ Backups automáticos

---

## 🔧 Método Alternativo: Instalação Local (Desenvolvimento)

### Pré-requisitos
- Python 3.11+
- Redis

### Passo a Passo

```bash
# 1. Entre no diretório
cd sentinelweb

# 2. Execute o script de setup (Mac/Linux)
./setup.sh

# Ou manualmente:
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. Configure o ambiente
cp .env.example .env

# 4. Inicie o Redis (se não estiver rodando)
# Mac:
brew services start redis

# Linux:
sudo systemctl start redis

# Windows/Docker:
docker run -d -p 6379:6379 redis:alpine

# 5. Abra 3 terminais e execute:

# Terminal 1 - FastAPI
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Celery Worker
celery -A celery_app worker --loglevel=info --concurrency=4

# Terminal 3 - Celery Beat
celery -A celery_app beat --loglevel=info

# (Opcional) Terminal 4 - Flower Monitor
celery -A celery_app flower --port=5555
```

---

## 📖 Primeiro Uso

### 1. Criar sua conta
1. Acesse `http://localhost:8000`
2. Clique em "Começar Agora"
3. Preencha:
   - Email: `seu@email.com`
   - Nome da Empresa: `Minha Agência`
   - Senha: mínimo 6 caracteres
   - Confirmar senha

### 2. Adicionar primeiro site
1. No dashboard, clique em "Adicionar Site"
2. Preencha:
   - **Domínio**: `google.com` (para testar)
   - **Nome**: `Google Test`
   - **Intervalo**: `5` minutos
3. Clique em "Adicionar Site"

### 3. Aguardar primeira verificação
- O sistema agenda automaticamente o scan
- Em ~10 segundos você verá os resultados
- O dashboard atualiza a cada 30 segundos

---

## 🎯 URLs Importantes

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Web App** | http://localhost:8000 | Interface principal |
| **API Docs** | http://localhost:8000/docs | Documentação Swagger |
| **Flower** | http://localhost:5555 | Monitor do Celery |
| **Health Check** | http://localhost:8000/health | Status da API |

---

## 🧪 Testando Manualmente

### Testar o Scanner
```bash
# Ative o venv primeiro
source venv/bin/activate

# Teste o scanner diretamente
python scanner.py google.com

# Deve retornar:
# 🔍 Escaneando google.com...
# ✅ Online: Sim
# Status HTTP: 200
# Latência: XXms
# SSL Válido: ✅
# etc...
```

### Testar Redis
```bash
redis-cli ping
# Deve retornar: PONG
```

### Testar Celery
```bash
# No Python:
python3

>>> from tasks import scan_site
>>> result = scan_site.delay(1)  # ID do site
>>> result.get(timeout=10)
```

---

## 🐛 Problemas Comuns

### "Connection refused" no Redis
```bash
# Verifique se o Redis está rodando
redis-cli ping

# Se não estiver, inicie:
brew services start redis  # Mac
sudo systemctl start redis # Linux
docker run -d -p 6379:6379 redis:alpine  # Docker
```

### "Module not found"
```bash
# Reinstale as dependências
pip install -r requirements.txt
```

### Celery não processa
```bash
# Verifique se o worker está rodando
celery -A celery_app inspect active

# Reinicie o worker com logs detalhados
celery -A celery_app worker --loglevel=debug
```

### Porta 8000 já em uso
```bash
# Use outra porta
uvicorn main:app --port 8001

# Ou mate o processo
lsof -ti:8000 | xargs kill -9
```

---

## 🛑 Parando os Serviços

### Docker
```bash
docker-compose down
```

### Local
```bash
# Pressione Ctrl+C em cada terminal
# Ou:
pkill -f uvicorn
pkill -f celery
```

---

## 📊 Monitorando

### Logs em Tempo Real (Docker)
```bash
docker-compose logs -f
docker-compose logs -f web       # Só FastAPI
docker-compose logs -f celery_worker  # Só Worker
```

### Verificar Status dos Containers
```bash
docker-compose ps
```

### Acessar o Flower (Monitor Visual)
```
http://localhost:5555
```
- Veja tasks em execução
- Histórico de tarefas
- Performance dos workers

---

## 🎨 Próximos Passos

1. **Adicione mais sites** para monitorar
2. **Configure alertas** (implementação futura)
3. **Ajuste intervalos** de verificação
4. **Analise os logs** no Flower
5. **Customize** as portas monitoradas em `scanner.py`

---

## 💡 Dicas

- ✅ Use intervalos maiores (15-30min) em produção para economizar recursos
- ✅ O dashboard atualiza automaticamente a cada 30 segundos
- ✅ Clique em "Escanear Agora" para forçar verificação imediata
- ✅ Sites inativos não são verificados (economiza processamento)
- ✅ Os logs são salvos no banco para análise histórica

---

**Tudo pronto! Seu SentinelWeb está funcionando! 🛡️**

Para suporte, verifique o README.md principal ou os logs detalhados.
