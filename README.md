# 🛡️ SentinelWeb - Sistema de Monitoramento de Sites e Segurança

**SentinelWeb** é um SaaS completo para monitoramento de sites com verificações de segurança em tempo real. Desenvolvido com FastAPI, Celery e TailwindCSS.

## 🚀 Funcionalidades

### ✅ Monitoramento Completo
- **Uptime Check**: Verifica se o site está online (HTTP 200)
- **Medição de Latência**: Tempo de resposta em milissegundos
- **SSL Monitor**: Valida certificado SSL e alerta sobre expirações
- **Port Scanner**: Detecta portas críticas abertas (FTP, SSH, MySQL, etc.)

### 📊 Dashboard Profissional
- Visualização em tempo real do status de todos os sites
- Estatísticas de uptime dos últimos 7 dias
- Alertas de SSL expirando em 30 dias
- Histórico completo de verificações

### 🔐 Segurança
- Autenticação JWT com cookies HTTPOnly
- Senhas com hash bcrypt
- Validação de dados com Pydantic
- Proteção contra exposição de portas críticas

---

## 🛠️ Stack Tecnológica

- **Backend**: FastAPI 0.109+ (Python 3.11+)
- **Workers**: Celery + Redis (processamento assíncrono)
- **Banco de Dados**: SQLite (MVP) / PostgreSQL (produção)
- **ORM**: SQLAlchemy 2.0
- **Frontend**: Jinja2 Templates + TailwindCSS (via CDN)
- **Autenticação**: JWT (python-jose) + Bcrypt (passlib)
- **HTTP Client**: HTTPX (moderno e assíncrono)

---

## 📦 Instalação e Execução

### Opção 1: Docker (Recomendado)

```bash
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

## 📄 Licença

Este projeto foi desenvolvido como MVP educacional. Sinta-se livre para usar e modificar.

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
