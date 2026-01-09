# ⚙️ COMANDOS ÚTEIS - SentinelWeb

## 🚀 INICIALIZAÇÃO

### Docker
```bash
# Iniciar tudo
docker-compose up -d

# Iniciar com rebuild
docker-compose up --build -d

# Ver logs em tempo real
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f redis

# Parar tudo
docker-compose down

# Parar e remover volumes
docker-compose down -v
```

### Local
```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Desativar
deactivate

# Instalar dependências
pip install -r requirements.txt

# Atualizar dependências
pip install --upgrade -r requirements.txt

# Iniciar FastAPI
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Iniciar Celery Worker
celery -A celery_app worker --loglevel=info --concurrency=4

# Iniciar Celery Beat
celery -A celery_app beat --loglevel=info

# Iniciar Flower
celery -A celery_app flower --port=5555
```

---

## 🗄️ BANCO DE DADOS

### SQLite
```bash
# Abrir banco de dados
sqlite3 sentinelweb.db

# Comandos úteis no SQLite
.tables                 # Listar tabelas
.schema users          # Ver estrutura da tabela
SELECT * FROM users;   # Consultar dados
.quit                  # Sair
```

### Python Shell
```python
# Entrar no shell Python
python3

# Acessar o banco
from database import SessionLocal
from models import User, Site, MonitorLog

db = SessionLocal()

# Listar todos os usuários
users = db.query(User).all()
for user in users:
    print(f"{user.id}: {user.email}")

# Listar sites
sites = db.query(Site).all()
for site in sites:
    print(f"{site.domain} - {site.current_status}")

# Criar usuário manualmente (teste)
from auth import get_password_hash
new_user = User(
    email="teste@exemplo.com",
    hashed_password=get_password_hash("senha123"),
    company_name="Empresa Teste"
)
db.add(new_user)
db.commit()

# Fechar conexão
db.close()
exit()
```

---

## 🔧 CELERY

### Status e Monitoring
```bash
# Ver workers ativos
celery -A celery_app inspect active

# Ver workers registrados
celery -A celery_app inspect registered

# Ver estatísticas
celery -A celery_app inspect stats

# Ver tarefas agendadas
celery -A celery_app inspect scheduled

# Listar workers disponíveis
celery -A celery_app inspect ping

# Purgar todas as tasks da fila
celery -A celery_app purge
```

### Executar Tasks Manualmente
```python
# Python shell
python3

from tasks import scan_site, scan_all_sites

# Scan de um site específico
result = scan_site.delay(1)  # ID do site
print(f"Task ID: {result.id}")

# Aguardar resultado (bloqueante)
scan_result = result.get(timeout=30)
print(scan_result)

# Verificar status
print(result.state)

# Scan de todos os sites
scan_all_sites.delay()

exit()
```

---

## 🧪 TESTES

### Testar Scanner
```bash
# Teste manual do scanner
python3 scanner.py google.com
python3 scanner.py github.com
python3 scanner.py seusite.com.br
```

### Testar Setup
```bash
# Executar script de teste
python3 test_setup.py
```

### Teste de Carga (Básico)
```bash
# Instalar Apache Bench
sudo apt-get install apache2-utils  # Linux
brew install httpd                   # Mac

# Teste simples
ab -n 100 -c 10 http://localhost:8000/

# Com autenticação (após login)
ab -n 100 -c 10 -C "access_token=SEU_TOKEN" http://localhost:8000/dashboard
```

---

## 🔍 DEBUG

### Logs Detalhados
```bash
# FastAPI com reload e debug
uvicorn main:app --reload --log-level debug

# Celery com debug
celery -A celery_app worker --loglevel=debug

# Python com verbose
python3 -v main.py
```

### Verificar Portas
```bash
# Ver portas em uso
lsof -i :8000  # FastAPI
lsof -i :6379  # Redis
lsof -i :5555  # Flower

# Matar processo em porta específica
kill -9 $(lsof -ti:8000)
```

### Redis
```bash
# Conectar ao Redis
redis-cli

# Comandos úteis
PING              # Testar conexão
KEYS *            # Listar todas as chaves
GET chave         # Ver valor de uma chave
FLUSHALL          # Limpar tudo (CUIDADO!)
INFO              # Informações do servidor
MONITOR           # Monitorar comandos em tempo real
EXIT              # Sair
```

---

## 📊 MONITORAMENTO

### Flower (Web UI)
```bash
# Acessar Flower
open http://localhost:5555

# Ou iniciar com autenticação
celery -A celery_app flower --port=5555 --basic_auth=usuario:senha
```

### Health Check
```bash
# Verificar saúde da aplicação
curl http://localhost:8000/health

# Deve retornar: {"status":"healthy","timestamp":"..."}
```

### Logs em Arquivo
```bash
# Redirecionar logs para arquivo
uvicorn main:app --log-config logging.ini > app.log 2>&1 &

# Ver logs em tempo real
tail -f app.log

# Buscar erros
grep ERROR app.log
grep -i exception app.log
```

---

## 🔄 ATUALIZAÇÃO E MANUTENÇÃO

### Atualizar Código
```bash
# Puxar últimas mudanças (se usar Git)
git pull origin main

# Reinstalar dependências
pip install -r requirements.txt

# Reiniciar serviços (Docker)
docker-compose restart

# Reiniciar serviços (Local)
# Ctrl+C nos terminais e reiniciar
```

### Backup do Banco
```bash
# SQLite
cp sentinelweb.db sentinelweb_backup_$(date +%Y%m%d).db

# PostgreSQL (quando migrar)
pg_dump sentinelweb > backup_$(date +%Y%m%d).sql
```

### Limpar Dados Antigos
```python
# Python shell
from database import SessionLocal
from models import MonitorLog
from datetime import datetime, timedelta

db = SessionLocal()

# Deletar logs com mais de 30 dias
thirty_days_ago = datetime.utcnow() - timedelta(days=30)
deleted = db.query(MonitorLog).filter(
    MonitorLog.checked_at < thirty_days_ago
).delete()

db.commit()
print(f"Deletados {deleted} logs antigos")
db.close()
```

---

## 🐛 TROUBLESHOOTING

### Problema: "Connection refused" Redis
```bash
# Verificar se Redis está rodando
redis-cli ping

# Iniciar Redis
# Mac
brew services start redis

# Linux
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

### Problema: "Module not found"
```bash
# Verificar ambiente virtual ativo
which python3  # Deve apontar para venv

# Reinstalar dependências
pip install --force-reinstall -r requirements.txt
```

### Problema: "Port already in use"
```bash
# Encontrar processo usando a porta
lsof -ti:8000

# Matar processo
kill -9 $(lsof -ti:8000)

# Ou usar outra porta
uvicorn main:app --port 8001
```

### Problema: Celery não processa tasks
```bash
# 1. Verificar Redis
redis-cli ping

# 2. Verificar workers ativos
celery -A celery_app inspect active

# 3. Purgar fila
celery -A celery_app purge

# 4. Reiniciar worker
celery -A celery_app worker --loglevel=debug
```

### Problema: Banco de dados corrompido
```bash
# Recriar banco (PERDERÁ DADOS!)
rm sentinelweb.db

# Iniciar aplicação (recriará o banco)
python3 -c "from database import init_db; init_db()"
```

---

## 📦 DEPLOY

### Preparar para Produção
```bash
# 1. Criar arquivo .env
cp .env.example .env
nano .env  # Editar com valores de produção

# 2. Gerar SECRET_KEY segura
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Build Docker
docker-compose -f docker-compose.prod.yml build

# 4. Iniciar em produção
docker-compose -f docker-compose.prod.yml up -d

# 5. Ver logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Atualizar em Produção
```bash
# 1. Pull código
git pull origin main

# 2. Rebuild
docker-compose -f docker-compose.prod.yml up -d --build

# 3. Verificar health
curl https://seu-dominio.com/health
```

---

## 🔐 SEGURANÇA

### Gerar Chaves
```bash
# SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Password Hash
python3 -c "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('sua-senha'))"
```

### Verificar Portas Abertas
```bash
# Linux
sudo netstat -tulpn | grep LISTEN

# Mac
sudo lsof -iTCP -sTCP:LISTEN -n -P

# Apenas portas críticas
nmap localhost -p 21,22,23,3306,5432
```

---

## 📱 API via cURL

### Login e usar API
```bash
# 1. Login (salva cookie)
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=seu@email.com" \
  -d "password=sua-senha" \
  -c cookies.txt

# 2. Listar sites (usa cookie)
curl -X GET http://localhost:8000/api/sites \
  -b cookies.txt

# 3. Disparar scan
curl -X POST http://localhost:8000/api/scan-all \
  -b cookies.txt
```

---

## 🎯 COMANDOS MAIS USADOS

```bash
# Iniciar tudo (Docker)
docker-compose up -d && docker-compose logs -f

# Reiniciar um serviço
docker-compose restart web

# Ver status
docker-compose ps

# Entrar em container
docker-compose exec web bash

# Ver logs de erro
docker-compose logs web | grep ERROR

# Backup rápido
cp sentinelweb.db backup.db

# Teste rápido
python3 scanner.py google.com

# Status Celery
celery -A celery_app inspect active
```

---

**💡 Dica:** Adicione estes comandos aos seus aliases do shell para acesso rápido!

```bash
# Adicione ao ~/.zshrc ou ~/.bashrc
alias sentinel-start="docker-compose up -d"
alias sentinel-stop="docker-compose down"
alias sentinel-logs="docker-compose logs -f"
alias sentinel-test="python3 test_setup.py"
```
