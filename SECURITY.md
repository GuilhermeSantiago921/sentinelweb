# 🔒 SEGURANÇA E BOAS PRÁTICAS - SentinelWeb

## ⚠️ ANTES DE COLOCAR EM PRODUÇÃO

### 1. 🔑 Altere a SECRET_KEY

**NUNCA use a SECRET_KEY padrão em produção!**

```bash
# Gere uma chave segura
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Adicione no arquivo .env
SECRET_KEY=sua-chave-super-secreta-gerada-aqui
```

### 2. 🗄️ Migre para PostgreSQL

SQLite é ótimo para MVP, mas em produção use PostgreSQL:

```bash
# .env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/sentinelweb
```

**Vantagens:**
- ✅ Melhor performance com múltiplos workers
- ✅ Transações ACID completas
- ✅ Suporte a conexões concorrentes
- ✅ Backups mais robustos

### 3. 🔐 Configure HTTPS

**NUNCA rode em produção sem HTTPS!**

Use um dos seguintes:
- Nginx como reverse proxy com Let's Encrypt
- Cloudflare (proteção DDoS grátis)
- AWS ALB/ELB com certificado ACM
- Caddy (HTTPS automático)

Exemplo Nginx:
```nginx
server {
    listen 443 ssl http2;
    server_name seu-dominio.com;
    
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. 🛡️ Configure CORS Corretamente

No `main.py`, adicione:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://seu-dominio.com"],  # NÃO use "*" em produção
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 5. 🔒 Configurações de Cookie Seguras

No `auth.py`, ao setar o cookie:

```python
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,      # Previne XSS
    secure=True,        # Apenas HTTPS
    samesite="strict",  # Previne CSRF
    max_age=86400,
    domain=".seu-dominio.com"  # Se usar subdomínios
)
```

### 6. 🚫 Rate Limiting

Instale slowapi:
```bash
pip install slowapi
```

Configure no `main.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/login")
@limiter.limit("5/minute")  # Máximo 5 tentativas por minuto
async def login(request: Request, ...):
    ...
```

---

## 🔐 Configurações de Segurança do Celery

### No `celery_app.py`:

```python
celery_app.conf.update(
    # Previne execução de código arbitrário
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timeouts de segurança
    task_time_limit=300,        # Mata task após 5 min
    task_soft_time_limit=240,   # Aviso em 4 min
    
    # Não permite pickle (vulnerabilidade de segurança)
    task_always_eager=False,
)
```

---

## 🗄️ Segurança do Banco de Dados

### 1. Use Migrações (Alembic)

```bash
pip install alembic
alembic init alembic
```

### 2. Nunca exponha o SQLite em produção

Se usar SQLite em produção (não recomendado):
```bash
chmod 600 sentinelweb.db  # Apenas owner pode ler/escrever
```

### 3. Sanitize Inputs

O Pydantic já valida, mas sempre use prepared statements:
```python
# ✅ BOM - SQLAlchemy usa prepared statements automaticamente
sites = db.query(Site).filter(Site.domain == user_input).all()

# ❌ RUIM - SQL Injection!
# db.execute(f"SELECT * FROM sites WHERE domain = '{user_input}'")
```

---

## 🔍 Segurança do Scanner

### 1. Timeout é CRÍTICO

```python
# scanner.py já tem timeouts, mas sempre valide:
DEFAULT_TIMEOUT = 5  # Nunca mais que 10 segundos
```

### 2. Valide Domínios

```python
# schemas.py já valida, mas reforçando:
import re

def is_valid_domain(domain: str) -> bool:
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
    return bool(re.match(pattern, domain))
```

### 3. Limite de Sites por Usuário

```python
# No main.py, ao adicionar site:
MAX_SITES_PER_USER = 100

site_count = db.query(Site).filter(Site.owner_id == user.id).count()
if site_count >= MAX_SITES_PER_USER:
    raise HTTPException(400, "Limite de sites atingido")
```

---

## 🚨 Monitoramento e Alertas

### 1. Configure Logs Estruturados

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'time': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
```

### 2. Use Sentry para Rastreamento de Erros

```bash
pip install sentry-sdk[fastapi]
```

```python
import sentry_sdk

sentry_sdk.init(
    dsn="seu-dsn-do-sentry",
    traces_sample_rate=1.0,
)
```

### 3. Health Checks Robustos

```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Testa banco
        db.execute("SELECT 1")
        
        # Testa Redis
        from celery_app import celery_app
        celery_app.connection().ensure_connection(max_retries=3)
        
        return {"status": "healthy"}
    except:
        raise HTTPException(status_code=503, detail="Unhealthy")
```

---

## 📊 Performance e Escalabilidade

### 1. Use Conexão Pool

```python
# database.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # Conexões normais
    max_overflow=10,        # Conexões extras sob carga
    pool_pre_ping=True,     # Testa conexão antes de usar
    pool_recycle=3600,      # Recicla conexões a cada hora
)
```

### 2. Cache com Redis

```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=1)

def cache(expire=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(cache_key)
            
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expire, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 3. Índices no Banco

```python
# models.py - Adicione índices compostos
class Site(Base):
    __tablename__ = "sites"
    __table_args__ = (
        Index('idx_owner_status', 'owner_id', 'current_status'),
        Index('idx_domain_owner', 'domain', 'owner_id', unique=True),
    )
```

---

## 🧪 Testes de Segurança

### 1. SQL Injection
```bash
# Tente injetar SQL no domínio
curl -X POST http://localhost:8000/sites/add \
  -d "domain='; DROP TABLE sites; --"
  
# Deve ser bloqueado pela validação Pydantic
```

### 2. XSS
```bash
# Tente injetar JavaScript
curl -X POST http://localhost:8000/sites/add \
  -d "name=<script>alert('XSS')</script>"
  
# Jinja2 faz escape automático, mas valide no browser
```

### 3. CSRF
```bash
# Sem cookie válido, deve falhar
curl -X POST http://localhost:8000/sites/1/delete
# Esperado: 401 Unauthorized
```

### 4. Brute Force Login
```bash
# Tente múltiplos logins
for i in {1..100}; do
  curl -X POST http://localhost:8000/login \
    -d "email=test@test.com" \
    -d "password=wrong"
done

# Com rate limiting, deve bloquear após 5 tentativas
```

---

## 📋 Checklist de Produção

- [ ] SECRET_KEY alterada e segura
- [ ] HTTPS configurado (Let's Encrypt/Cloudflare)
- [ ] PostgreSQL configurado (não SQLite)
- [ ] CORS configurado corretamente
- [ ] Rate limiting ativado
- [ ] Logs estruturados (JSON)
- [ ] Sentry ou similar para erros
- [ ] Backups automáticos do banco
- [ ] Health checks configurados
- [ ] Firewall configurado (apenas portas 80/443)
- [ ] Redis com senha (requirepass)
- [ ] Celery com autenticação
- [ ] Variáveis de ambiente (não hardcoded)
- [ ] Docker secrets (se usar Docker)
- [ ] Monitoramento (Prometheus/Grafana)
- [ ] Alertas configurados (PagerDuty/OpsGenie)

---

## 🐳 Docker em Produção

### Use multi-stage builds:

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*
COPY . .
USER nobody  # Não rode como root!
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔥 Firewall (UFW)

```bash
# Permite apenas HTTP/HTTPS
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH (remova se não precisar)
sudo ufw enable
```

---

## 📞 Contato de Emergência

Em caso de vulnerabilidade descoberta:
1. **NÃO** poste publicamente
2. Envie detalhes para: security@seu-dominio.com
3. Aguarde 90 dias antes de divulgar

---

**Lembre-se: Segurança é um processo contínuo, não um estado final!** 🛡️
