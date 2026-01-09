# 🚀 Deploy do Painel Administrativo SQLAdmin

## 📋 Checklist Pré-Deploy

Antes de fazer o deploy, verifique se todos os arquivos foram criados:

```bash
# Verifique os arquivos novos
ls -la admin.py
ls -la setup_admin.py
ls -la templates/admin_dashboard.html
ls -la ADMIN_SQLADMIN_COMPLETE.md
ls -la ADMIN_QUICKSTART.md
ls -la DEPLOY_ADMIN_PANEL.md

# Verifique as modificações
git status
```

**Arquivos esperados:**
- ✅ `admin.py` (NOVO)
- ✅ `setup_admin.py` (NOVO)
- ✅ `templates/admin_dashboard.html` (NOVO)
- ✅ `main.py` (MODIFICADO)
- ✅ `requirements.txt` (MODIFICADO)
- ✅ Documentação (3 arquivos MD)

---

## 1️⃣ **COMMIT NO GITHUB**

### Passo 1: Verificar Status
```bash
cd /Users/guilherme/Documents/Sistema\ de\ monitoramento/sentinelweb
git status
```

### Passo 2: Adicionar Arquivos
```bash
# Adiciona todos os arquivos novos e modificados
git add admin.py
git add setup_admin.py
git add templates/admin_dashboard.html
git add main.py
git add requirements.txt
git add ADMIN_SQLADMIN_COMPLETE.md
git add ADMIN_QUICKSTART.md
git add DEPLOY_ADMIN_PANEL.md
```

**OU** adicionar tudo de uma vez:
```bash
git add .
```

### Passo 3: Verificar o que será Commitado
```bash
git diff --cached --name-only
```

**Saída esperada:**
```
admin.py
setup_admin.py
templates/admin_dashboard.html
main.py
requirements.txt
ADMIN_SQLADMIN_COMPLETE.md
ADMIN_QUICKSTART.md
DEPLOY_ADMIN_PANEL.md
```

### Passo 4: Fazer Commit
```bash
git commit -m "feat: Painel administrativo enterprise com SQLAdmin

✨ Novos Recursos:
- Painel administrativo completo usando SQLAdmin
- Dashboard executivo com KPIs (MRR, Churn, Saúde, Fila Celery)
- Gestão de usuários (CRM) com filtros e busca
- Gestão de sites (Ops) com status visual
- Gestão financeira (ERP) integrada com Asaas
- Logs de monitoramento (auditoria read-only)
- Configurações do sistema (singleton)
- Autenticação blindada (apenas superusers)
- Gráficos interativos (Chart.js)

📦 Dependências Adicionadas:
- sqladmin[full]==0.16.1
- itsdangerous==2.1.2
- redis (já existente)

📚 Documentação:
- ADMIN_SQLADMIN_COMPLETE.md (guia completo)
- ADMIN_QUICKSTART.md (quickstart)
- DEPLOY_ADMIN_PANEL.md (deploy)
- setup_admin.py (script de setup)

🔒 Segurança:
- JWT + SessionMiddleware
- Validação is_superuser em todas as rotas /admin
- Campos sensíveis mascarados (API keys)

🎨 Interface:
- Bootstrap 5 responsivo
- Mobile-first design
- Gradientes e animações modernas"
```

### Passo 5: Push para GitHub
```bash
# Push para branch principal
git push origin main

# OU se estiver em outra branch
git push origin <nome-da-branch>
```

### Passo 6: Verificar no GitHub
Acesse: `https://github.com/<seu-usuario>/sentinelweb`

Você deverá ver:
- ✅ Commit novo no histórico
- ✅ Badge verde de commit bem-sucedido
- ✅ Todos os arquivos atualizados

---

## 2️⃣ **DEPLOY NO SERVIDOR DE PRODUÇÃO**

### 🔐 Conectar ao Servidor

```bash
# SSH no servidor VPS
ssh root@<SEU_IP_DO_SERVIDOR>

# OU com usuário específico
ssh usuario@<SEU_IP_DO_SERVIDOR>
```

---

### 📥 Atualizar o Código

```bash
# Navegar para o diretório do projeto
cd /opt/sentinelweb

# Fazer backup (segurança)
cp -r /opt/sentinelweb /opt/sentinelweb_backup_$(date +%Y%m%d_%H%M%S)

# Verificar branch atual
git branch

# Fazer pull das alterações
git pull origin main
```

**Saída esperada:**
```
Updating 6cdfa19..abc1234
Fast-forward
 admin.py                        | 500 ++++++++++++++++++++++++
 setup_admin.py                  | 150 ++++++++
 templates/admin_dashboard.html  | 350 +++++++++++++++++
 main.py                         | 120 +++++-
 requirements.txt                |   2 +
 ...
```

---

### 🐳 Reconstruir Container Docker

```bash
# Parar containers
docker compose -f docker-compose.prod.yml down

# Reconstruir imagem do web (forçando rebuild)
docker compose -f docker-compose.prod.yml build --no-cache web

# Subir containers novamente
docker compose -f docker-compose.prod.yml up -d
```

**Verificar se subiu corretamente:**
```bash
docker compose -f docker-compose.prod.yml ps
```

**Saída esperada:**
```
NAME                   STATUS          PORTS
sentinelweb-web-1      Up 5 seconds    0.0.0.0:8000->8000/tcp
sentinelweb-db-1       Up 6 seconds    5432/tcp
sentinelweb-redis-1    Up 6 seconds    6379/tcp
sentinelweb-celery-1   Up 5 seconds    
```

---

### 👑 Criar Superusuário

```bash
# Executar script de setup dentro do container
docker compose -f docker-compose.prod.yml exec web python setup_admin.py
```

**Interação esperada:**
```
============================================================
   SENTINELWEB - SETUP DO PAINEL ADMINISTRATIVO
============================================================

📝 Preencha os dados do superusuário:

Email: admin@seudominio.com
Nome da Empresa: SentinelWeb Admin
Senha: ********
Confirme a senha: ********

============================================================
✅ SUPERUSUÁRIO CRIADO COM SUCESSO!
============================================================

📧 Email: admin@seudominio.com
👑 Permissão: Superusuário

🔗 Acesse o painel em: https://seudominio.com/admin

============================================================
```

---

### 🧪 Testar a Aplicação

#### 1. Verificar Logs
```bash
# Ver logs do container web
docker compose -f docker-compose.prod.yml logs web --tail=50

# Acompanhar logs em tempo real
docker compose -f docker-compose.prod.yml logs -f web
```

**Procure por:**
- ✅ `Application startup complete`
- ✅ `Uvicorn running on http://0.0.0.0:8000`
- ❌ NENHUM erro de importação

#### 2. Testar Health Check
```bash
curl http://localhost:8000/
```

**Saída esperada:**
```json
{"status": "ok", "message": "SentinelWeb API is running"}
```

#### 3. Testar API de Stats do Admin
```bash
curl http://localhost:8000/admin/api/dashboard-stats
```

**Saída esperada:**
```json
{
  "mrr": 0,
  "arpu": 0,
  "churn_risk": 0,
  "health_score": 100,
  "queue_size": 0,
  "total_users": 1,
  "total_sites": 0,
  ...
}
```

#### 4. Acessar Painel Admin no Browser

**URL:** `https://seudominio.com/admin`

**Login:**
- Email: `admin@seudominio.com`
- Senha: A senha que você criou

**Verificações:**
- ✅ Página de login carrega
- ✅ Login funciona
- ✅ Dashboard com KPIs aparece
- ✅ Menu lateral tem todos os módulos
- ✅ Gráficos renderizam (Chart.js)

---

## 3️⃣ **VERIFICAÇÕES PÓS-DEPLOY**

### ✅ Checklist de Validação

```bash
# 1. Containers rodando
docker compose -f docker-compose.prod.yml ps

# 2. Sem erros nos logs
docker compose -f docker-compose.prod.yml logs web --tail=100 | grep -i error

# 3. Banco de dados conectado
docker compose -f docker-compose.prod.yml exec db psql -U sentinelweb -c "SELECT COUNT(*) FROM users;"

# 4. Redis conectado
docker compose -f docker-compose.prod.yml exec redis redis-cli PING

# 5. Celery rodando
docker compose -f docker-compose.prod.yml exec celery celery -A celery_app inspect active

# 6. Superusuário existe
docker compose -f docker-compose.prod.yml exec web python -c "
from database import SessionLocal
from models import User
db = SessionLocal()
superuser = db.query(User).filter(User.is_superuser == True).first()
print(f'✅ Superusuário: {superuser.email}' if superuser else '❌ Nenhum superuser!')
"
```

---

## 4️⃣ **CONFIGURAÇÃO DO NGINX (Se Aplicável)**

Se você usa Nginx como proxy reverso, verifique a configuração:

```bash
# Editar configuração do Nginx
nano /etc/nginx/sites-available/sentinelweb
```

**Adicione se necessário:**
```nginx
server {
    listen 80;
    server_name seudominio.com;

    # Redireciona HTTP para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seudominio.com;

    # SSL (certbot)
    ssl_certificate /etc/letsencrypt/live/seudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seudominio.com/privkey.pem;

    # Admin Panel (SQLAdmin)
    location /admin {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Para session cookies
        proxy_set_header Cookie $http_cookie;
        proxy_cookie_path / "/; HTTPOnly; Secure; SameSite=Lax";
    }

    # API de estatísticas
    location /admin/api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Resto da aplicação
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Testar e recarregar Nginx:**
```bash
nginx -t
systemctl reload nginx
```

---

## 5️⃣ **TROUBLESHOOTING**

### ❌ Erro: "No module named 'sqladmin'"

**Causa:** Dependências não instaladas no container

**Solução:**
```bash
# Rebuild forçando instalação de dependências
docker compose -f docker-compose.prod.yml build --no-cache web
docker compose -f docker-compose.prod.yml up -d
```

### ❌ Erro: "Admin auth error"

**Causa:** SECRET_KEY não configurada ou diferente

**Solução:**
```bash
# Verificar .env
cat /opt/sentinelweb/.env | grep SECRET_KEY

# Se não existir, gerar uma
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')" >> .env

# Restart
docker compose -f docker-compose.prod.yml restart web
```

### ❌ Erro: "Dashboard stats 500"

**Causa:** Redis não está acessível

**Solução:**
```bash
# Verificar Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli PING

# Se não responder, restart
docker compose -f docker-compose.prod.yml restart redis
```

### ❌ Admin não carrega CSS/JS

**Causa:** Arquivos estáticos não servidos

**Solução:**
```bash
# Verificar se o SQLAdmin está servindo estáticos
curl -I https://seudominio.com/admin/statics/css/tabler.min.css

# Se 404, verificar montagem de volumes
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

---

## 6️⃣ **ROLLBACK (SE NECESSÁRIO)**

Se algo der errado, volte para a versão anterior:

```bash
# Parar containers
docker compose -f docker-compose.prod.yml down

# Voltar commit
git log --oneline -5  # Ver últimos commits
git reset --hard <HASH_DO_COMMIT_ANTERIOR>

# Rebuild
docker compose -f docker-compose.prod.yml build --no-cache web
docker compose -f docker-compose.prod.yml up -d
```

**OU restaurar do backup:**
```bash
# Listar backups
ls -lh /opt/sentinelweb_backup_*

# Restaurar
rm -rf /opt/sentinelweb
cp -r /opt/sentinelweb_backup_20260109_143000 /opt/sentinelweb
cd /opt/sentinelweb
docker compose -f docker-compose.prod.yml up -d
```

---

## 7️⃣ **MONITORAMENTO PÓS-DEPLOY**

### Logs em Tempo Real
```bash
# Todos os serviços
docker compose -f docker-compose.prod.yml logs -f

# Apenas web
docker compose -f docker-compose.prod.yml logs -f web

# Apenas erros
docker compose -f docker-compose.prod.yml logs -f web | grep -i error
```

### Métricas de Sistema
```bash
# Uso de CPU/RAM dos containers
docker stats

# Espaço em disco
df -h

# Conexões ao banco
docker compose -f docker-compose.prod.yml exec db psql -U sentinelweb -c "
SELECT COUNT(*) as total_connections 
FROM pg_stat_activity 
WHERE datname = 'sentinelweb';
"
```

---

## 📊 **COMANDOS RÁPIDOS**

### Desenvolvimento Local
```bash
# Testar localmente antes do deploy
cd /Users/guilherme/Documents/Sistema\ de\ monitoramento/sentinelweb
source ../.venv/bin/activate
python setup_admin.py
uvicorn main:app --reload
# Acesse: http://localhost:8000/admin
```

### Produção (Resumo)
```bash
# No servidor
cd /opt/sentinelweb
git pull
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache web
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec web python setup_admin.py
docker compose -f docker-compose.prod.yml logs -f web
```

---

## 🎉 **DEPLOY CONCLUÍDO!**

Após seguir todos os passos, você terá:

✅ Código commitado no GitHub  
✅ Servidor de produção atualizado  
✅ Painel administrativo rodando em `/admin`  
✅ Superusuário criado e funcional  
✅ Dashboard com KPIs em tempo real  
✅ Todos os módulos (CRM, Ops, ERP) funcionando  

**Acesse:** `https://seudominio.com/admin`

---

## 📞 **SUPORTE**

**Documentação:**
- `ADMIN_SQLADMIN_COMPLETE.md` - Guia completo
- `ADMIN_QUICKSTART.md` - Quickstart
- `DEPLOY_ADMIN_PANEL.md` - Este arquivo

**Em caso de dúvidas:**
1. Verifique os logs: `docker compose logs -f web`
2. Consulte o troubleshooting acima
3. Valide o checklist pós-deploy

---

**Última atualização:** 09/01/2026  
**Versão:** 1.0.0  
**Status:** ✅ Pronto para Produção
