# 🛡️ SentinelWeb - Sistema de Monitoramento de Sites

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)
[![Security](https://img.shields.io/badge/security-A+-green.svg)](SECURITY_AUDIT.md)

> 🚀 **Sistema Completo de Monitoramento e Segurança Web**  
> Monitore sites, valide SSL, detecte vulnerabilidades e receba alertas em tempo real!

---

## 📋 Índice

- [✨ Funcionalidades](#-funcionalidades)
- [🛠️ Stack Tecnológica](#️-stack-tecnológica)
- [⚡ Instalação Rápida](#-instalação-rápida)
- [🔒 Segurança](#-segurança)
- [📚 Documentação](#-documentação)
- [🤝 Contribuindo](#-contribuindo)
- [📄 Licença](#-licença)

---

---

## ✨ Funcionalidades

### 🌐 Monitoramento Completo de Sites
- ✅ **Uptime Check** - Verifica disponibilidade (HTTP 200)
- ⚡ **Medição de Latência** - Tempo de resposta em tempo real
- 🔐 **SSL Monitor** - Validação de certificados + alertas de expiração
- 🔓 **Port Scanner** - Detecta portas críticas expostas
- 📊 **WordPress Scanner** - Identifica plugins vulneráveis
- 🎨 **Google PageSpeed** - Análise de performance
- 👁️ **Visual Regression** - Detecta mudanças visuais no site

### ❤️ Heartbeat Monitoring
- 🔔 **Cron Job Monitoring** - Monitora execução de tarefas agendadas
- ⏱️ **Dead Man's Switch** - Alerta se tarefa não executar
- 📱 **Alertas Telegram** - Notificações instantâneas de falhas

### 💰 Sistema de Pagamentos
- 💳 **Integração Asaas** - Processamento de pagamentos completo
- 📊 **Planos de Assinatura** - Free, Básico, Pro, Enterprise
- 🔄 **Webhook Sync** - Sincronização automática de pagamentos
- 📧 **Notificações** - Emails de confirmação e faturas

### �️ Segurança
- 🔒 **Autenticação JWT** - Tokens seguros com HTTPOnly cookies
- 🔑 **Bcrypt** - Hash de senhas com salt
- 🚫 **Rate Limiting** - Proteção contra DDoS e brute force
- 📋 **Audit Logs** - Registro de todas as ações
- 🛑 **CORS** - Configuração de origens permitidas

### 📊 Dashboard Profissional
- 📈 **Métricas em Tempo Real** - Status de todos os sites
- 📉 **Gráficos de Performance** - Uptime dos últimos 7/30 dias
- 🎯 **Alertas Inteligentes** - SSL expirando, sites offline
- 📝 **Histórico Completo** - Todas as verificações salvas

---

## 🛠️ Stack Tecnológica

### Backend
- **Framework**: FastAPI 0.109+ (async/await)
- **Workers**: Celery + Redis (tarefas assíncronas)
- **ORM**: SQLAlchemy 2.0 (async)
- **Autenticação**: JWT (python-jose) + Bcrypt (passlib)
- **HTTP Client**: HTTPX (async)
- **Browser Automation**: Playwright

### Banco de Dados
- **Desenvolvimento**: SQLite
- **Produção**: PostgreSQL 15 Alpine
- **Cache**: Redis 7 Alpine
- **Connection Pooling**: QueuePool (size 20, max overflow 40)

### Frontend
- **Templates**: Jinja2
- **CSS**: TailwindCSS (via CDN)
- **Icons**: Heroicons
- **Charts**: Chart.js

### Infraestrutura
- **Containerização**: Docker + Docker Compose
- **Reverse Proxy**: Nginx (rate limiting + SSL)
- **SSL/TLS**: Let's Encrypt (Certbot)
- **Firewall**: UFW + Fail2Ban
- **Monitoring**: Healthchecks + Prometheus
- **Logging**: Structured JSON logs

### Integrações
- **Pagamentos**: Asaas API
- **Alertas**: Telegram Bot API
- **Performance**: Google PageSpeed Insights
- **Monitoramento**: Sentry (error tracking)

---

## ⚡ Instalação Rápida

### � Instalação Automatizada (Ubuntu)

O método mais rápido para colocar em produção:

```bash
# 1. Clone o repositório
git clone https://github.com/GuilhermeSantiago921/sentinelweb.git
cd sentinelweb

# 2. Execute o instalador automático (Ubuntu 20.04, 22.04, 24.04)
sudo bash install.sh
```

**O script instala automaticamente:**
- ✅ Docker & Docker Compose
- ✅ PostgreSQL 15 + Redis
- ✅ Nginx + SSL/TLS (Let's Encrypt)
- ✅ UFW Firewall + Fail2Ban
- ✅ Backups automáticos (diários)
- ✅ Gera credenciais fortes
- ✅ Cria superusuário

**Tempo:** 15-30 minutos  
**Requisitos:** Ubuntu Server + Domínio apontando para o IP

📖 **Guia Completo:** [INSTALL_GUIDE.md](INSTALL_GUIDE.md)

---

### 🐳 Docker Compose (Desenvolvimento)

```bash
# 1. Clone o repositório
git clone https://github.com/GuilhermeSantiago921/sentinelweb.git
cd sentinelweb

# 2. Configure o ambiente
cp .env.development.example .env

# 3. Suba os containers
docker compose up -d

# 4. Crie um superusuário
docker compose exec web python create_superuser.py

# 5. Acesse
# http://localhost:8000
```

---

### 💻 Instalação Local (Desenvolvimento)

```bash
# 1. Clone o repositório
git clone https://github.com/GuilhermeSantiago921/sentinelweb.git
cd sentinelweb

# 2. Crie ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure ambiente
cp .env.development.example .env

# 5. Instale Playwright browsers
playwright install chromium

# 6. Execute a aplicação
uvicorn main:app --reload

# 7. Em outro terminal, execute o Celery
celery -A celery_app worker --loglevel=info
celery -A celery_app beat --loglevel=info
```

---
# 1. Clone ou entre no diretório do projeto
cd sentinelweb

# 2. Construa e suba os containers
docker-compose up --build

# 3. Acesse a aplicação
# Web: http://localhost:8000
# Flower (Monitor Celery): http://localhost:5555
```

### Opção 2: Instalação Local

```bash
# 1. Crie um ambiente virtual
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure o arquivo .env
cp .env.example .env
# Edite o .env conforme necessário

# 4. Instale e inicie o Redis (necessário para Celery)
# MacOS:
brew install redis
brew services start redis

# Linux:
sudo apt-get install redis-server
sudo systemctl start redis

# Windows: Use Docker ou WSL2

# 5. Em um terminal, inicie o FastAPI
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 6. Em outro terminal, inicie o Celery Worker
celery -A celery_app worker --loglevel=info --concurrency=4

# 7. Em outro terminal, inicie o Celery Beat (agendador)
celery -A celery_app beat --loglevel=info

# 8. (Opcional) Monitor Celery Flower
celery -A celery_app flower --port=5555
```

---

## 🎯 Uso

### 1. Criar Conta
Acesse `http://localhost:8000` e clique em "Começar Agora"

### 2. Adicionar Sites
No dashboard, clique em "Adicionar Site" e insira:
- Domínio (ex: `google.com`)
- Nome amigável (opcional)
- Intervalo de verificação (1-60 minutos)

### 3. Monitorar
O sistema automaticamente:
- Verifica uptime a cada X minutos
- Valida certificado SSL
- Escaneia portas críticas
- Exibe alertas no dashboard

---

## 📁 Estrutura do Projeto

```
sentinelweb/
├── main.py                 # Aplicação FastAPI (rotas e configuração)
├── database.py            # Configuração do SQLAlchemy
├── models.py              # Modelos ORM (User, Site, MonitorLog)
├── schemas.py             # Schemas Pydantic (validação)
├── auth.py                # Sistema de autenticação JWT
├── scanner.py             # Engine de monitoramento (lógica de scan)
├── tasks.py               # Tarefas Celery (workers)
├── celery_app.py          # Configuração do Celery
├── requirements.txt       # Dependências Python
├── Dockerfile             # Imagem Docker
├── docker-compose.yml     # Orquestração de containers
├── .env.example           # Exemplo de variáveis de ambiente
├── .gitignore            # Arquivos ignorados pelo Git
├── README.md             # Este arquivo
└── templates/            # Templates HTML
    ├── base.html         # Template base
    ├── home.html         # Página inicial
    ├── login.html        # Login
    ├── register.html     # Cadastro
    ├── dashboard.html    # Dashboard principal
    ├── site_form.html    # Formulário de site
    └── site_detail.html  # Detalhes do site
```

---

## 🔧 Configuração Avançada

### Variáveis de Ambiente (.env)

```bash
# Banco de Dados
DATABASE_URL=sqlite:///./sentinelweb.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Segurança (MUDE EM PRODUÇÃO!)
SECRET_KEY=sua-chave-secreta-aqui

# Debug
DEBUG=True
```

### Migração para PostgreSQL

No arquivo `.env`, altere:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/sentinelweb
```

---

## 🎨 Customização

### Alterar Portas Monitoradas

Edite `scanner.py`, variável `CRITICAL_PORTS`:

```python
CRITICAL_PORTS = {
    21: "FTP",
    22: "SSH",
    3306: "MySQL",
    # Adicione suas portas aqui
}
```

### Alterar Intervalo de Verificação Global

Edite `celery_app.py`, seção `beat_schedule`:

```python
"scan-all-sites-every-5-minutes": {
    "task": "tasks.scan_all_sites",
    "schedule": 300.0,  # Altere aqui (em segundos)
},
```

---

## 🐛 Troubleshooting

### Redis não conecta
```bash
# Verifique se o Redis está rodando
redis-cli ping
# Deve retornar: PONG
```

### Celery não processa tasks
```bash
# Verifique os logs do worker
celery -A celery_app worker --loglevel=debug
```

### Permissões no SQLite
```bash
# Garanta permissões de escrita no diretório
chmod 777 .
```

---

## 📈 Melhorias Futuras (Roadmap)

- [ ] Notificações por email/Telegram quando site cai
- [ ] Gráficos de latência e uptime
- [ ] API REST completa para integração
- [ ] Suporte a múltiplos usuários por conta (times)
- [ ] Verificação de mudanças no conteúdo da página
- [ ] Integração com Slack/Discord
- [ ] App mobile (React Native)

---

---

## 👨‍💻 Autor

Desenvolvido com ❤️ usando FastAPI, Celery e TailwindCSS.

**Stack completa:**
- FastAPI (alta performance assíncrona)
- Celery + Redis (processamento em background)
- SQLAlchemy (ORM flexível)
- TailwindCSS (UI moderna sem build)
- Docker (deployment simplificado)

---

## 🙏 Suporte

Para dúvidas ou problemas:
1. Verifique os logs: `docker-compose logs -f`
2. Teste manualmente o scanner: `python scanner.py google.com`
3. Acesse o Flower: `http://localhost:5555`

---

**SentinelWeb** - Protegendo seus sites 24/7 🛡️
