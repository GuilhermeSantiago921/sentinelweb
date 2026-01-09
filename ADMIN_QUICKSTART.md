# 🎯 PAINEL ADMINISTRATIVO SQLADMIN - GUIA RÁPIDO

## ✅ O QUE FOI CRIADO

### 1. **admin.py** (Completo)
Backend completo do painel com:
- ✅ Autenticação blindada (apenas superusers)
- ✅ UserAdmin (gestão de usuários)
- ✅ SiteAdmin (gestão de sites)
- ✅ PaymentAdmin (gestão financeira)
- ✅ MonitorLogAdmin (logs read-only)
- ✅ SystemConfigAdmin (configurações)

### 2. **templates/admin_dashboard.html**
Dashboard executivo com:
- ✅ KPIs: MRR, Churn Risk, Saúde, Fila Celery
- ✅ Gráficos: Planos e Status de Sites
- ✅ Tabela de estatísticas
- ✅ Feed de atividades

### 3. **main.py** (Atualizado)
- ✅ Importação do SQLAdmin
- ✅ SessionMiddleware configurado
- ✅ Admin registrado com autenticação
- ✅ Endpoint `/admin/api/dashboard-stats`

### 4. **setup_admin.py**
Script interativo para criar superusuário

### 5. **requirements.txt** (Atualizado)
- ✅ sqladmin[full]==0.16.1
- ✅ itsdangerous==2.1.2
- ✅ redis (já estava)

---

## 🚀 COMO USAR

### Passo 1: Criar Superusuário
```bash
cd /opt/sentinelweb
python setup_admin.py
```

**Forneça:**
- Email: admin@sentinelweb.com
- Empresa: SentinelWeb Admin
- Senha: (mínimo 8 caracteres)

### Passo 2: Iniciar Aplicação
```bash
# Desenvolvimento
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Produção (Docker)
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache web
docker compose -f docker-compose.prod.yml up -d
```

### Passo 3: Acessar Painel
**URL:** http://localhost:8000/admin

**Credenciais:** O email e senha do superusuário

---

## 📊 RECURSOS DO PAINEL

### Dashboard Principal
- 💰 **MRR:** (Pro × R$ 49) + (Agency × R$ 149)
- ⚠️ **Churn Risk:** Pagamentos vencidos
- ❤️ **Saúde:** % de sites online
- 📋 **Fila Celery:** Tasks pendentes no Redis

### Módulos Disponíveis
1. **👥 Usuários**
   - Lista, edita, busca por email/CPF
   - Filtros por plano e status
   - Badges coloridas (Free/Pro/Agency)

2. **🌐 Sites**
   - Status visual (🟢/🔴/⚪)
   - SSL com semáforo (🟢 >30d, 🟡 7-30d, 🔴 <7d)
   - Filtros e busca

3. **💰 Pagamentos**
   - Histórico completo Asaas
   - Status formatados
   - Valores em R$

4. **📝 Logs** (Read-only)
   - Todas as verificações
   - Erros e latências
   - Auditoria completa

5. **⚙️ Configurações**
   - Preços dos planos
   - API Keys mascaradas
   - Singleton (1 registro apenas)

---

## 🔧 FUTURAS IMPLEMENTAÇÕES

### Custom Actions (A fazer)
```python
# Em UserAdmin
@action("impersonate")
async def impersonate_user(self, ids):
    """Logar como cliente"""
    pass

# Em SiteAdmin
@action("force_scan")
async def force_scan(self, ids):
    """Re-scan manual imediato"""
    pass

# Em PaymentAdmin
@action("sync_asaas")
async def sync_payment(self, ids):
    """Sincronizar com API Asaas"""
    pass
```

---

## 🐛 TROUBLESHOOTING

### Problema: "No module named 'sqladmin'"
**Solução:**
```bash
pip install sqladmin[full] itsdangerous redis
```

### Problema: "Admin não aparece"
**Causa:** Superusuário não foi criado

**Verificação:**
```python
python -c "from database import SessionLocal; from models import User; \
db = SessionLocal(); \
print(db.query(User).filter(User.is_superuser == True).count())"
```

**Deve retornar:** `1` ou mais

### Problema: "Erro 403 - Acesso negado"
**Causa:** Usuário não é superuser

**Solução:** Execute no banco:
```sql
UPDATE users SET is_superuser = TRUE WHERE email = 'seu@email.com';
```

### Problema: "Dashboard stats erro 500"
**Causa:** Redis não está rodando

**Verificação:**
```bash
docker compose ps redis
# ou
redis-cli ping
```

---

## 📁 ARQUIVOS CRIADOS/MODIFICADOS

```
sentinelweb/
├── admin.py                        ← NOVO (500 linhas)
├── main.py                         ← MODIFICADO (adicionado SQLAdmin)
├── requirements.txt                ← MODIFICADO (sqladmin, itsdangerous)
├── setup_admin.py                  ← NOVO (script de setup)
├── templates/
│   └── admin_dashboard.html        ← NOVO (dashboard executivo)
└── ADMIN_SQLADMIN_COMPLETE.md      ← NOVO (documentação)
```

---

## ✨ DIFERENCIAL DESTE PAINEL

### VS Painel Anterior (Simples)
| Recurso | Anterior | SQLAdmin |
|---------|----------|----------|
| Framework | HTML puro | SQLAdmin Pro |
| CRUD | Manual | Automático |
| Filtros | Nenhum | Avançados |
| Busca | Básica | Full-text |
| KPIs | Estáticos | Dinâmicos |
| Gráficos | Nenhum | Chart.js |
| Auth | Básica | JWT + Session |
| Mobile | Não | Responsivo |

### Por que SQLAdmin?
- ✅ **Menos código:** 90% gerado automaticamente
- ✅ **Manutenção:** Atualizações no modelo = painel atualiza
- ✅ **UI Profissional:** Bootstrap 5 + ícones
- ✅ **Segurança:** Built-in CSRF, XSS protection
- ✅ **Extensível:** Custom actions, formatters, widgets

---

## 🎓 PRÓXIMOS PASSOS

1. **Testar o painel:**
   ```bash
   python setup_admin.py
   uvicorn main:app --reload
   ```

2. **Acessar:** http://localhost:8000/admin

3. **Explorar:**
   - Dashboard com KPIs
   - CRUD de usuários
   - CRUD de sites
   - Visualizar pagamentos

4. **Implementar Custom Actions** (próxima fase)

5. **Deploy em produção:**
   ```bash
   cd /opt/sentinelweb
   git pull
   docker compose -f docker-compose.prod.yml build web
   docker compose -f docker-compose.prod.yml up -d
   python setup_admin.py  # Criar superuser
   ```

---

## 📞 SUPORTE

**Documentação completa:** `ADMIN_SQLADMIN_COMPLETE.md`

**SQLAdmin Docs:** https://aminalaee.dev/sqladmin/

**Stack:**
- FastAPI + SQLAdmin + PostgreSQL
- Bootstrap 5 + Chart.js
- Redis + Celery

---

**Status:** ✅ PRONTO PARA USO

**Desenvolvido por:** Principal Software Architect
**Data:** 09/01/2026
