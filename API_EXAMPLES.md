# 🔌 EXEMPLOS DE USO DA API - SentinelWeb

Este arquivo contém exemplos de como usar a API REST do SentinelWeb.

## 🔐 Autenticação

Todas as rotas protegidas requerem um token JWT no header ou cookie.

### Registrar Usuário

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=teste@exemplo.com" \
  -d "password=senha123" \
  -d "password_confirm=senha123" \
  -d "company_name=Minha Empresa"
```

### Login

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=teste@exemplo.com" \
  -d "password=senha123" \
  -c cookies.txt
```

**Nota:** O cookie do token é salvo em `cookies.txt`

---

## 📊 API Endpoints (JSON)

### 1. Listar Todos os Sites

```bash
curl -X GET http://localhost:8000/api/sites \
  -b cookies.txt \
  -H "Content-Type: application/json"
```

**Resposta:**
```json
[
  {
    "id": 1,
    "domain": "google.com",
    "name": "Google",
    "is_active": true,
    "current_status": "online",
    "last_latency": 123.45,
    "ssl_days_remaining": 90,
    "ssl_valid": true,
    "check_interval": 5
  }
]
```

### 2. Detalhes de um Site

```bash
curl -X GET http://localhost:8000/api/sites/1 \
  -b cookies.txt \
  -H "Content-Type: application/json"
```

### 3. Disparar Scan de Todos os Sites

```bash
curl -X POST http://localhost:8000/api/scan-all \
  -b cookies.txt \
  -H "Content-Type: application/json"
```

**Resposta:**
```json
{
  "message": "Scan agendado para todos os sites"
}
```

### 4. Health Check (Público)

```bash
curl -X GET http://localhost:8000/health
```

**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-06T10:30:00"
}
```

---

## 🐍 Python Client Example

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Login
session = requests.Session()
response = session.post(f"{BASE_URL}/login", data={
    "email": "teste@exemplo.com",
    "password": "senha123"
})

if response.status_code == 200:
    print("✅ Login realizado!")
    
    # 2. Listar sites
    sites = session.get(f"{BASE_URL}/api/sites").json()
    print(f"📊 Sites cadastrados: {len(sites)}")
    
    for site in sites:
        print(f"\n🌐 {site['name']}")
        print(f"   Status: {site['current_status']}")
        print(f"   Latência: {site['last_latency']}ms")
        print(f"   SSL: {site['ssl_days_remaining']} dias")
    
    # 3. Disparar scan
    scan_result = session.post(f"{BASE_URL}/api/scan-all").json()
    print(f"\n✅ {scan_result['message']}")
else:
    print("❌ Falha no login")
```

---

## 🧪 JavaScript/Fetch Example

```javascript
const BASE_URL = 'http://localhost:8000';

// 1. Login
async function login(email, password) {
  const formData = new URLSearchParams();
  formData.append('email', email);
  formData.append('password', password);
  
  const response = await fetch(`${BASE_URL}/login`, {
    method: 'POST',
    body: formData,
    credentials: 'include' // Importante para cookies
  });
  
  return response.ok;
}

// 2. Listar Sites
async function getSites() {
  const response = await fetch(`${BASE_URL}/api/sites`, {
    credentials: 'include'
  });
  
  return await response.json();
}

// 3. Disparar Scan
async function triggerScan() {
  const response = await fetch(`${BASE_URL}/api/scan-all`, {
    method: 'POST',
    credentials: 'include'
  });
  
  return await response.json();
}

// Uso
(async () => {
  await login('teste@exemplo.com', 'senha123');
  const sites = await getSites();
  console.log('Sites:', sites);
  
  const result = await triggerScan();
  console.log('Scan:', result);
})();
```

---

## 📱 Webhook/Integração

### Monitorar via Webhook (Implementação Futura)

```bash
# POST para receber alertas
curl -X POST https://seu-webhook.com/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "site": "exemplo.com",
    "status": "offline",
    "timestamp": "2024-01-06T10:30:00",
    "message": "Site está fora do ar"
  }'
```

---

## 🔧 Celery API (Direto)

### Python - Disparar Task Diretamente

```python
from tasks import scan_site, scan_all_sites

# Scan de um site específico
result = scan_site.delay(site_id=1)
print(f"Task ID: {result.id}")

# Aguardar resultado (bloqueante)
scan_result = result.get(timeout=30)
print(scan_result)

# Scan de todos os sites
scan_all_sites.delay()
```

---

## 📊 Acessando o Banco Direto

```python
from database import SessionLocal
from models import Site, User, MonitorLog
from sqlalchemy import func

db = SessionLocal()

# Total de sites por usuário
user_id = 1
total = db.query(Site).filter(Site.owner_id == user_id).count()
print(f"Total de sites: {total}")

# Sites offline
offline = db.query(Site).filter(
    Site.current_status == "offline"
).all()

for site in offline:
    print(f"⚠️  {site.domain} está offline")

# Média de latência das últimas 24h
from datetime import datetime, timedelta
yesterday = datetime.utcnow() - timedelta(days=1)

avg_latency = db.query(func.avg(MonitorLog.latency_ms)).filter(
    MonitorLog.checked_at >= yesterday
).scalar()

print(f"Latência média: {avg_latency}ms")

db.close()
```

---

## 🔍 Testando o Scanner Diretamente

```python
from scanner import full_scan, check_uptime, check_ssl_certificate

# Scan completo
result = full_scan("google.com")
print(f"Online: {result.is_online}")
print(f"Latência: {result.latency_ms}ms")
print(f"SSL: {result.ssl_days_remaining} dias")
print(f"Portas abertas: {result.open_ports}")

# Apenas uptime
is_online, status, latency = check_uptime("github.com")
print(f"GitHub: {status} - {latency}ms")

# Apenas SSL
ssl_info = check_ssl_certificate("google.com")
print(f"SSL válido: {ssl_info['valid']}")
print(f"Dias restantes: {ssl_info['days_remaining']}")
```

---

## 🎯 Dicas para Integração

1. **Use sessões** para manter cookies entre requisições
2. **Implemente retry** para requests que podem falhar
3. **Cache** os resultados por alguns segundos
4. **Rate limiting**: Não faça mais que 10 req/segundo
5. **Webhooks**: Para receber alertas em tempo real (implementar)

---

Para mais informações, acesse a documentação interativa:
**http://localhost:8000/docs** (Swagger UI)
