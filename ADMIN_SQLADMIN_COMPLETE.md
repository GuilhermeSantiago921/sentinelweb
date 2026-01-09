# 🎯 SentinelWeb - Painel Administrativo Enterprise

## 📋 Visão Geral

Este é um **painel administrativo de nível enterprise** construído com **SQLAdmin** para gestão completa do negócio SaaS.

### ✨ Recursos Implementados

#### 🔒 1. Autenticação Blindada
- Apenas superusuários (`is_superuser=True`) podem acessar `/admin`
- Validação JWT na sessão + verificação no banco de dados
- Sessões seguras com timeout de 24 horas
- Logout automático em caso de inatividade

#### 📊 2. Dashboard Executivo
- **MRR (Monthly Recurring Revenue):** Receita mensal recorrente calculada em tempo real
- **Churn Risk:** Usuários inadimplentes que podem cancelar
- **Saúde Operacional:** % de sites online vs offline
- **Fila Celery:** Tamanho da fila de processamento (Redis)
- **Gráficos Interativos:** Distribuição de planos e status dos sites
- **Atividade Recente:** Feed de eventos importantes do sistema

#### 👥 3. Gestão de Usuários (CRM)
- Visualização completa de todos os usuários
- Busca por email, empresa ou CPF/CNPJ
- Filtros por plano (Free/Pro/Agency) e status (Ativo/Inativo)
- Badges coloridas para identificação rápida de planos
- Edição de dados e permissões
- **🚀 Futuro:** Impersonate (logar como cliente), Ban/Unban

#### 🌐 4. Gestão de Sites (Ops)
- Lista todos os sites monitorados
- Status visual (🟢 Online, 🔴 Offline, ⚪ Desconhecido)
- Indicador de SSL (🟢 >30d, 🟡 7-30d, 🔴 <7d)
- Filtros por status, dono e intervalo de checagem
- Busca por domínio ou nome
- **🚀 Futuro:** Force Full Scan (re-scan manual imediato)

#### 💰 5. Gestão Financeira (ERP)
- Todas as transações do Asaas
- Status dos pagamentos (Pendente, Pago, Vencido, Reembolsado)
- Tipos de pagamento (Boleto, PIX, Cartão)
- Filtros por status, tipo e data
- Valores formatados em Real (R$)
- **🚀 Futuro:** Sincronizar com Asaas (atualizar status manualmente)

#### ⚙️ 6. Configurações do Sistema
- **Singleton:** Apenas 1 registro de configuração
- Preços dos planos (Free, Pro, Agency)
- Chaves de API mascaradas (Asaas, Telegram)
- Campos sensíveis protegidos com `type="password"`
- Não permite criação/exclusão (apenas edição)

#### 📝 7. Logs de Monitoramento (Auditoria)
- Histórico completo de todas as verificações
- Filtros por site, status e data
- Latência de resposta (ms)
- Códigos HTTP e mensagens de erro
- **Modo Read-Only:** Não permite edição ou exclusão

---

## 🚀 Instalação e Configuração

### 1. Instalar Dependências

```bash
cd /opt/sentinelweb
pip install -r requirements.txt
```

As seguintes bibliotecas serão instaladas:
- `sqladmin[full]==0.16.1` - Painel administrativo
- `itsdangerous==2.1.2` - Sessões seguras
- `redis==4.6.0` - Para stats da fila Celery

### 2. Criar Superusuário

Execute o script de setup:

```bash
python setup_admin.py
```

Você será solicitado a fornecer:
- **Email:** seu@email.com
- **Nome da Empresa:** Nome Administrativo
- **Senha:** (mínimo 8 caracteres)

**Exemplo:**
```
📝 Preencha os dados do superusuário:

Email: admin@sentinelweb.com
Nome da Empresa: Administração SentinelWeb
Senha: ********
Confirme a senha: ********

✅ SUPERUSUÁRIO CRIADO COM SUCESSO!
📧 Email: admin@sentinelweb.com
👑 Permissão: Superusuário
🔗 Acesse o painel em: http://localhost:8000/admin
```

### 3. Iniciar a Aplicação

```bash
# Desenvolvimento
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Produção (Docker)
docker compose -f docker-compose.prod.yml up -d
```

### 4. Acessar o Painel

Abra seu navegador e acesse:

**URL:** `http://localhost:8000/admin` (ou `https://seudominio.com/admin`)

**Login:**
- Email: O email cadastrado no setup
- Senha: A senha escolhida

---

## 🎨 Interface do Painel

### Dashboard Principal

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Dashboard Executivo                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  💰 MRR              ⚠️ Churn Risk      ❤️ Saúde    📋 Fila │
│  R$ 4.270           3 usuários        98.5%      12 tasks   │
│  ↑ 12.5%           inadimplentes     sites OK    pendentes  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  📈 Distribuição de Planos        📊 Sites por Status        │
│  [Gráfico Pizza]                  [Gráfico Barras]          │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  🕐 Atividade Recente                                        │
│  • Novo cadastro - usuario@empresa.com - há 5 min           │
│  • Pagamento recebido - R$ 149,00 - há 12 min               │
│  • Site offline - exemplo.com.br - há 18 min                │
└─────────────────────────────────────────────────────────────┘
```

### Menu Lateral

```
🏠 Dashboard
👥 Usuários
🌐 Sites
💰 Pagamentos
📝 Logs de Monitoramento
⚙️ Configurações
```

---

## 🔧 Customizações Futuras

### Custom Actions (A Implementar)

#### 1. **Impersonate User** (Usuários)
```python
@action("impersonate", "Logar como Usuário", confirmation="Deseja se passar por este usuário?")
async def impersonate_user(self, ids: List[int]) -> str:
    """Gera JWT do usuário e redireciona para /dashboard"""
    user_id = ids[0]
    token = create_access_token(data={"sub": str(user_id)})
    # Redirecionar para /dashboard com token na sessão
    return RedirectResponse(f"/dashboard?admin_token={token}")
```

#### 2. **Force Full Scan** (Sites)
```python
@action("force_scan", "🔄 Re-Scan Agora", confirmation="Forçar verificação imediata?")
async def force_scan(self, ids: List[int]) -> str:
    """Envia task Celery para re-scanear o site"""
    for site_id in ids:
        scan_site.apply_async(args=[site_id], countdown=0)
    return f"{len(ids)} site(s) adicionado(s) à fila de processamento"
```

#### 3. **Sync Payment Status** (Pagamentos)
```python
@action("sync_asaas", "🔄 Sincronizar com Asaas", confirmation="Atualizar status?")
async def sync_payment(self, ids: List[int]) -> str:
    """Consulta API do Asaas e atualiza status local"""
    from services.asaas import AsaasService
    
    asaas = AsaasService()
    updated = 0
    
    for payment_id in ids:
        payment = db.query(Payment).get(payment_id)
        status = await asaas.get_payment_status(payment.asaas_payment_id)
        payment.status = status
        updated += 1
    
    db.commit()
    return f"{updated} pagamento(s) atualizado(s)"
```

---

## 📊 Cálculo dos KPIs

### MRR (Monthly Recurring Revenue)
```python
# Preços fixos
PRO_PRICE = 49.0
AGENCY_PRICE = 149.0

# Conta usuários ativos por plano
pro_users = db.query(User).filter(
    User.plan_status == 'pro',
    User.is_active == True
).count()

agency_users = db.query(User).filter(
    User.plan_status == 'agency',
    User.is_active == True
).count()

# Calcula MRR
mrr = (pro_users * PRO_PRICE) + (agency_users * AGENCY_PRICE)
```

### ARPU (Average Revenue Per User)
```python
total_paying_users = pro_users + agency_users
arpu = mrr / total_paying_users if total_paying_users > 0 else 0
```

### Churn Risk
```python
# Usuários com pagamentos vencidos
churn_risk = db.query(Payment).filter(
    Payment.status == PaymentStatus.OVERDUE
).count()
```

### Saúde Operacional
```python
# % de sites online
total_sites = db.query(Site).filter(Site.is_active == True).count()
sites_online = db.query(Site).filter(
    Site.is_active == True,
    Site.current_status == 'online'
).count()

health_score = (sites_online / total_sites * 100) if total_sites > 0 else 100
```

### Fila Celery
```python
import redis

redis_client = redis.from_url(os.getenv("REDIS_URL"))
queue_size = redis_client.llen("celery")  # Tamanho da fila
```

---

## 🔒 Segurança

### Níveis de Acesso

| Rota | Acesso |
|------|--------|
| `/admin/*` | ✅ Apenas `is_superuser=True` |
| `/dashboard` | ✅ Usuários autenticados |
| `/` | 🌐 Público |

### Validações

1. **Login:** 
   - Email + Senha verificados no banco
   - Hash bcrypt da senha
   - `is_superuser` deve ser `True`

2. **Sessão:**
   - JWT armazenado em cookie seguro
   - Timeout de 24 horas
   - Renovação automática

3. **Campos Sensíveis:**
   - `asaas_api_key`: Mascarado (`type="password"`)
   - `telegram_bot_token`: Mascarado
   - `hashed_password`: Nunca exibido

---

## 🧪 Testes

### 1. Criar Superusuário
```bash
python setup_admin.py
```

### 2. Testar Login
```bash
curl -X POST http://localhost:8000/admin/login \
  -d "username=admin@sentinelweb.com&password=suasenha"
```

### 3. Verificar Dashboard Stats
```bash
curl http://localhost:8000/admin/api/dashboard-stats
```

**Resposta esperada:**
```json
{
  "mrr": 4270,
  "arpu": 89.58,
  "churn_risk": 3,
  "health_score": 98.5,
  "queue_size": 12,
  "total_users": 87,
  "total_sites": 243,
  "plan_free": 40,
  "plan_pro": 32,
  "plan_agency": 15,
  "sites_online": 239,
  "sites_offline": 3,
  "sites_unknown": 1
}
```

---

## 📚 Arquitetura

### Fluxo de Autenticação

```
┌─────────┐     POST /admin/login      ┌──────────────┐
│ Browser │ ────────────────────────> │ AdminAuth    │
└─────────┘                             │ .login()     │
                                        └──────────────┘
                                               │
                                               │ Valida email/senha
                                               │ Verifica is_superuser
                                               ▼
                                        ┌──────────────┐
                                        │ SessionLocal │
                                        │ (PostgreSQL) │
                                        └──────────────┘
                                               │
                                               │ Cria JWT
                                               ▼
                                        ┌──────────────┐
                                        │ request      │
                                        │ .session     │
                                        │ ["token"]    │
                                        └──────────────┘
```

### Stack Tecnológica

- **Backend:** FastAPI + SQLAdmin
- **ORM:** SQLAlchemy (Async)
- **Banco:** PostgreSQL 15
- **Cache:** Redis 7
- **Frontend:** Bootstrap 5 + Chart.js
- **Auth:** JWT + SessionMiddleware

---

## 🐛 Troubleshooting

### Erro: "No module named 'sqladmin'"
```bash
pip install sqladmin[full]
```

### Erro: "No module named 'itsdangerous'"
```bash
pip install itsdangerous
```

### Erro: "No module named 'redis'"
```bash
pip install redis
```

### Admin não aparece
Verifique se o superusuário foi criado:
```python
python -c "from database import SessionLocal; from models import User; db = SessionLocal(); print(db.query(User).filter(User.is_superuser == True).first())"
```

### Dashboard stats retorna erro 500
Verifique se o Redis está rodando:
```bash
docker compose ps redis
```

---

## 📖 Referências

- [SQLAdmin Documentation](https://aminalaee.dev/sqladmin/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Chart.js](https://www.chartjs.org/)
- [Bootstrap 5](https://getbootstrap.com/)

---

## 🎉 Conclusão

Você agora tem um **painel administrativo enterprise** completo para gerenciar todo o seu negócio SaaS!

**Recursos implementados:**
✅ Dashboard executivo com KPIs
✅ Gestão de usuários (CRM)
✅ Gestão de sites (Ops)
✅ Módulo financeiro (ERP)
✅ Configurações do sistema
✅ Logs de auditoria
✅ Autenticação blindada

**Próximos passos:**
- Implementar custom actions (Impersonate, Force Scan, Sync Asaas)
- Adicionar exportação de relatórios (CSV, PDF)
- Criar alertas automatizados no painel
- Implementar análise de tendências (IA)

---

**Desenvolvido com ❤️ por um Principal Software Architect**
