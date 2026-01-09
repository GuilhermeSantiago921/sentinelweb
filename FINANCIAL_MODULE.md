# 💰 MÓDULO FINANCEIRO - INTEGRAÇÃO ASAAS

## ✅ STATUS: IMPLEMENTAÇÃO COMPLETA (FASE 1 e 2)

### 📋 RESUMO
Módulo financeiro completo com integração Asaas para gestão de pagamentos, incluindo:
- ✅ Modelos de dados (SystemConfig, Payment)
- ✅ Migração de banco de dados
- ✅ Rotas administrativas
- ✅ Interface completa no admin panel
- ✅ Dashboard com KPIs financeiros
- ⏳ API Asaas (stubbed - Fase 3)

---

## 🗄️ ESTRUTURA DO BANCO DE DADOS

### Tabela: `system_config` (Singleton)
Armazena configurações globais do sistema para integração Asaas.

```sql
CREATE TABLE system_config (
    id INTEGER PRIMARY KEY,
    asaas_api_token TEXT,                    -- Token da API Asaas
    asaas_webhook_secret VARCHAR(255),       -- Secret para validação de webhooks
    is_sandbox BOOLEAN DEFAULT 1,            -- Modo sandbox (teste)
    plan_free_price REAL DEFAULT 0.0,        -- Preço plano Free
    plan_pro_price REAL DEFAULT 49.0,        -- Preço plano Pro
    plan_agency_price REAL DEFAULT 149.0,    -- Preço plano Agency
    created_at DATETIME,
    updated_at DATETIME
);
```

**Padrão Singleton**: Apenas 1 linha na tabela, gerenciada automaticamente.

### Tabela: `payments`
Rastreia todo o ciclo de vida dos pagamentos.

```sql
CREATE TABLE payments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,                -- FK para users
    asaas_id VARCHAR(255) UNIQUE,            -- ID do pagamento no Asaas (pay_...)
    asaas_customer_id VARCHAR(255),          -- ID do cliente no Asaas
    value REAL NOT NULL,                     -- Valor bruto da cobrança
    status VARCHAR(50) NOT NULL,             -- PaymentStatus enum
    billing_type VARCHAR(50),                -- BillingType enum
    due_date DATETIME NOT NULL,              -- Data de vencimento
    payment_date DATETIME,                   -- Data do pagamento
    confirmed_date DATETIME,                 -- Data da confirmação
    invoice_url VARCHAR(500),                -- URL da fatura
    bank_slip_url VARCHAR(500),              -- URL do boleto
    pix_qr_code TEXT,                        -- QR Code PIX
    original_value REAL,                     -- Valor original (sem juros/desconto)
    interest_value REAL,                     -- Valor de juros
    discount_value REAL,                     -- Valor de desconto
    net_value REAL,                          -- Valor líquido recebido
    description TEXT,                        -- Descrição do pagamento
    external_reference VARCHAR(255),         -- Referência externa
    created_at DATETIME,
    updated_at DATETIME,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Índices para performance
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_asaas_id ON payments(asaas_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_due_date ON payments(due_date);
```

---

## 📊 ENUMS E STATUS

### PaymentStatus (12 estados)
```python
class PaymentStatus(enum.Enum):
    PENDING = "pending"                # Aguardando pagamento
    RECEIVED = "received"              # Pagamento recebido
    CONFIRMED = "confirmed"            # Pagamento confirmado
    OVERDUE = "overdue"                # Vencido
    REFUNDED = "refunded"              # Estornado
    RECEIVED_IN_CASH = "received_in_cash"  # Recebido em dinheiro
    REFUND_REQUESTED = "refund_requested"  # Estorno solicitado
    CHARGEBACK_REQUESTED = "chargeback_requested"  # Chargeback solicitado
    CHARGEBACK_DISPUTE = "chargeback_dispute"      # Disputa de chargeback
    AWAITING_CHARGEBACK_REVERSAL = "awaiting_chargeback_reversal"  # Aguardando reversão
    DUNNING_REQUESTED = "dunning_requested"  # Cobrança adicional solicitada
    DUNNING_RECEIVED = "dunning_received"    # Cobrança adicional recebida
```

### BillingType (6 tipos)
```python
class BillingType(enum.Enum):
    BOLETO = "boleto"              # Boleto bancário
    CREDIT_CARD = "credit_card"    # Cartão de crédito
    PIX = "pix"                    # PIX
    TRANSFER = "transfer"          # Transferência bancária
    DEPOSIT = "deposit"            # Depósito
    UNDEFINED = "undefined"        # Não definido
```

---

## 🎨 INTERFACE DO ADMIN

### 1. Página de Configuração (`/admin/config`)

**Seção 1: Integração Asaas**
- 🔑 Token da API (campo password)
- 🛡️ Webhook Secret
- ☑️ Checkbox: Modo Sandbox
- 📊 Status Badge: Configurado / Não Configurado
- 🌐 Base URL dinâmica (sandbox/produção)

**Seção 2: Preços dos Planos**
- 🎁 Plano Free (R$ 0,00)
- ⭐ Plano Pro (R$ 49,00)
- 🏢 Plano Agency (R$ 149,00)
- 💰 Preview de receita mensal

**Recursos:**
- Validação de campos
- Mensagens de sucesso/erro
- Links para documentação Asaas
- Design responsivo com Tailwind CSS

---

### 2. Página de Pagamentos (`/admin/payments`)

**KPI Cards (topo):**
- 💵 Receita Mensal (verde gradient)
- 💰 Receita Total (azul gradient)
- ✅ Pagamentos Recebidos (contador)
- ⏳ Pagamentos Pendentes (contador)
- ❌ Pagamentos Vencidos (contador)

**Filtros:**
- 📋 Todos
- ⏳ Pendentes (amarelo)
- ✅ Recebidos (verde)
- ✔️ Confirmados (azul)
- ❌ Vencidos (vermelho)

**Tabela de Pagamentos:**
| Coluna | Descrição |
|--------|-----------|
| ID | ID interno + ID Asaas (truncado) |
| Usuário | Nome + Email |
| Valor | Valor bruto + Valor líquido |
| Status | Badge colorido + alertas |
| Tipo | Ícone + Nome (PIX, Boleto, Cartão) |
| Vencimento | Data + Data de pagamento |
| Criado | Timestamp |
| Ações | Sync + Ver Fatura + Ver Boleto |

**Recursos:**
- 🔄 Botão de sincronização (AJAX)
- 📥 Exportar CSV
- 🎨 Color coding por status
- ⚠️ Alertas para vencimentos próximos
- 🔗 Links diretos para faturas/boletos
- 📱 Design responsivo

---

### 3. Dashboard Admin (atualizado)

**Novo Card Financeiro:**
```html
💰 Receita Mensal
R$ XXX,XX

Total: R$ YYY,YY
Ver Pagamentos →
```

- Card em destaque com gradient verde/teal
- Mostra receita do mês corrente
- Mostra receita total all-time
- Link direto para /admin/payments

---

## 🔌 ROTAS DA API

### GET `/admin/config`
Exibe formulário de configuração Asaas.

**Resposta:** HTML template com configurações atuais

---

### POST `/admin/config/update`
Salva configurações do Asaas.

**Body (Form):**
```
asaas_api_token: string (optional)
asaas_webhook_secret: string (optional)
is_sandbox: boolean (default: false)
plan_free_price: float (optional)
plan_pro_price: float (optional)
plan_agency_price: float (optional)
```

**Comportamento:**
- Apenas atualiza campos fornecidos
- Cria config se não existir
- Redirect para `/admin/config?success=1`

---

### GET `/admin/payments`
Lista todos os pagamentos com filtros.

**Query Params:**
- `status` (optional): Filtra por PaymentStatus

**Response:**
```python
{
    "payments": [...],  # Lista de Payment objects
    "stats": {
        "monthly_revenue": float,    # Receita do mês
        "total_revenue": float,      # Receita total
        "received": int,             # Qtd recebidos
        "pending": int,              # Qtd pendentes
        "overdue": int               # Qtd vencidos
    }
}
```

---

### POST `/admin/payments/{payment_id}/sync`
Sincroniza pagamento com Asaas API.

**Status:** ⚠️ STUBBED (retorna simulação)

**Response:**
```json
{
    "message": "Sync simulado - implemente integração real"
}
```

**TODO Fase 3:**
```python
# Implementar consulta real à API Asaas
config = db.query(SystemConfig).first()
headers = {"access_token": config.asaas_api_token}
response = requests.get(
    f"{config.asaas_base_url}/payments/{payment.asaas_id}",
    headers=headers
)
# Atualizar payment com dados da resposta
```

---

### GET `/admin/payments/export`
Exporta pagamentos para CSV.

**Response:** CSV file
```csv
ID,Asaas ID,Usuário,Email,Valor,Status,Tipo,Vencimento,Pagamento,Criado
1,pay_123456,João,joao@email.com,49.00,received,pix,2024-01-15,2024-01-14,2024-01-10
...
```

**Headers:**
```
Content-Type: text/csv
Content-Disposition: attachment; filename=payments_YYYYMMDD.csv
```

---

## 🧪 TESTES

### 1. Migração
```bash
docker-compose exec web python migrate_financial.py
```

**Output esperado:**
```
✅ system_config criada
✅ Configuração inicial inserida
✅ payments criada
✅ 4 índices criados
```

---

### 2. Criar Pagamentos de Teste
```bash
docker-compose exec web python create_sample_payments.py
```

**Output esperado:**
```
📊 Criando pagamentos de exemplo para 2 usuários...
✅ 10 pagamentos criados com sucesso!

📊 Resumo:
   - Recebidos/Confirmados: 5
   - Pendentes: 3
   - Vencidos: 2

💰 Receita Total: R$ 545.00
```

---

### 3. Validação de Interfaces

**Checklist:**
- ✅ `/admin/config` - Formulário de configuração carrega
- ✅ Salvar token funciona e redireciona com sucesso
- ✅ `/admin/payments` - Lista de pagamentos carrega
- ✅ KPIs mostram valores corretos
- ✅ Filtros por status funcionam
- ✅ Badges coloridos aparecem corretamente
- ✅ Botão "Exportar CSV" baixa arquivo
- ✅ Botão "Sync" executa AJAX (mostra simulação)
- ✅ Dashboard admin mostra novo card financeiro
- ✅ Valores de receita estão corretos

---

## 🔐 PROPRIEDADES E MÉTODOS ÚTEIS

### SystemConfig

```python
config = db.query(SystemConfig).first()

# URL base dinâmica
config.asaas_base_url
# → "https://sandbox.asaas.com/api/v3" (se sandbox)
# → "https://api.asaas.com/v3" (se produção)

# Verificar se está configurado
config.is_configured  # True se token presente
```

---

### Payment

```python
payment = db.query(Payment).first()

# Status checks
payment.is_paid         # True se RECEIVED ou CONFIRMED
payment.is_overdue      # True se vencido e não pago

# Cálculos de data
payment.days_until_due  # Dias até vencer (None se pago)

# UI helpers
payment.status_label    # "Recebido", "Pendente", "Vencido"
payment.status_color    # "green", "yellow", "red", "blue", "gray"
```

---

## 📦 ARQUIVOS CRIADOS/MODIFICADOS

### Novos Arquivos:
```
✅ migrate_financial.py              # Script de migração
✅ create_sample_payments.py         # Script de teste
✅ templates/admin/config.html       # Página de configuração
✅ templates/admin/payments.html     # Página de pagamentos
✅ FINANCIAL_MODULE.md               # Esta documentação
```

### Arquivos Modificados:
```
✅ models.py                         # +200 linhas (enums, SystemConfig, Payment)
✅ main.py                           # +200 linhas (6 rotas admin, KPIs dashboard)
✅ templates/admin/index.html        # Novo card financeiro + grid 5 colunas
```

---

## 🚀 PRÓXIMAS ETAPAS (FASE 3)

### 1. Cliente Asaas API
```python
# criar arquivo: services/asaas_client.py

import requests
from models import SystemConfig

class AsaasClient:
    def __init__(self, db):
        self.config = db.query(SystemConfig).first()
        self.base_url = self.config.asaas_base_url
        self.headers = {
            "access_token": self.config.asaas_api_token,
            "Content-Type": "application/json"
        }
    
    def create_payment(self, customer_id, value, due_date, billing_type):
        """Cria cobrança no Asaas"""
        # POST /payments
        pass
    
    def get_payment(self, payment_id):
        """Consulta status de um pagamento"""
        # GET /payments/{id}
        pass
    
    def create_customer(self, email, name, cpfCnpj):
        """Cria cliente no Asaas"""
        # POST /customers
        pass
```

---

### 2. Webhook Endpoint
```python
@app.post("/webhooks/asaas")
async def asaas_webhook(request: Request, db: Session = Depends(get_db)):
    """Recebe notificações do Asaas"""
    
    # 1. Validar assinatura do webhook
    signature = request.headers.get("asaas-signature")
    # ... validar com webhook_secret
    
    # 2. Processar evento
    data = await request.json()
    event = data.get("event")  # PAYMENT_RECEIVED, PAYMENT_CONFIRMED, etc.
    payment_id = data["payment"]["id"]
    
    # 3. Atualizar pagamento no banco
    payment = db.query(Payment).filter(Payment.asaas_id == payment_id).first()
    if payment:
        if event == "PAYMENT_RECEIVED":
            payment.status = PaymentStatus.RECEIVED
            payment.payment_date = datetime.now()
        # ... outros eventos
        
        db.commit()
        
        # 4. Enviar notificação ao usuário (email/Telegram)
        # ... implementar
    
    return {"ok": True}
```

---

### 3. Fluxo de Pagamento do Usuário

**Rota:** `/user/checkout`
```python
@app.post("/user/checkout")
async def user_checkout(
    plan: str,  # "pro" ou "agency"
    billing_type: str,  # "boleto", "pix", "credit_card"
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Obter preço do plano
    config = db.query(SystemConfig).first()
    value = config.plan_pro_price if plan == "pro" else config.plan_agency_price
    
    # 2. Criar cliente no Asaas (se não existir)
    asaas = AsaasClient(db)
    customer = asaas.create_customer(
        email=user.email,
        name=user.full_name,
        cpfCnpj=user.cpf
    )
    
    # 3. Criar cobrança no Asaas
    due_date = datetime.now() + timedelta(days=7)
    asaas_payment = asaas.create_payment(
        customer_id=customer["id"],
        value=value,
        due_date=due_date,
        billing_type=billing_type
    )
    
    # 4. Salvar no banco local
    payment = Payment(
        user_id=user.id,
        asaas_id=asaas_payment["id"],
        asaas_customer_id=customer["id"],
        value=value,
        status=PaymentStatus.PENDING,
        billing_type=BillingType(billing_type),
        due_date=due_date,
        invoice_url=asaas_payment["invoiceUrl"],
        bank_slip_url=asaas_payment.get("bankSlipUrl"),
        pix_qr_code=asaas_payment.get("pixQrCodeUrl")
    )
    db.add(payment)
    db.commit()
    
    # 5. Redirecionar para página de pagamento
    return RedirectResponse(f"/user/payment/{payment.id}")
```

---

### 4. Email/Telegram Notifications
```python
# Após confirmar pagamento via webhook:

# Email
send_email(
    to=user.email,
    subject="✅ Pagamento Confirmado - SentinelWeb",
    template="payment_confirmed.html",
    context={"user": user, "payment": payment}
)

# Telegram
send_telegram_message(
    chat_id=user.telegram_chat_id,
    text=f"✅ Pagamento confirmado!\n\n"
         f"Valor: R$ {payment.value:.2f}\n"
         f"Plano: {user.plan_status.upper()}\n"
         f"Obrigado pela confiança! 🚀"
)
```

---

## 📚 REFERÊNCIAS

### Asaas API Documentation
- **Base:** https://docs.asaas.com/
- **Autenticação:** https://docs.asaas.com/reference/autenticacao
- **Cobranças:** https://docs.asaas.com/reference/criar-nova-cobranca
- **Webhooks:** https://docs.asaas.com/reference/webhooks
- **Clientes:** https://docs.asaas.com/reference/criar-novo-cliente

### Endpoints Asaas
```
Production:  https://api.asaas.com/v3
Sandbox:     https://sandbox.asaas.com/api/v3

Header: access_token: $aact_YTU5YTE0M2M2N...
```

### Webhooks Events
```
PAYMENT_CREATED
PAYMENT_AWAITING_RISK_ANALYSIS
PAYMENT_APPROVED_BY_RISK_ANALYSIS
PAYMENT_REPROVED_BY_RISK_ANALYSIS
PAYMENT_UPDATED
PAYMENT_CONFIRMED
PAYMENT_RECEIVED
PAYMENT_OVERDUE
PAYMENT_DELETED
PAYMENT_RESTORED
PAYMENT_REFUNDED
PAYMENT_RECEIVED_IN_CASH_UNDONE
PAYMENT_CHARGEBACK_REQUESTED
PAYMENT_CHARGEBACK_DISPUTE
PAYMENT_AWAITING_CHARGEBACK_REVERSAL
PAYMENT_DUNNING_RECEIVED
PAYMENT_DUNNING_REQUESTED
```

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Database & Models ✅
- [x] Criar enums PaymentStatus e BillingType
- [x] Criar model SystemConfig (singleton)
- [x] Criar model Payment com relacionamentos
- [x] Implementar properties (is_paid, is_overdue, status_color)
- [x] Criar migration script
- [x] Executar migração e validar tabelas

### Fase 2: Admin Interface ✅
- [x] Criar rota GET /admin/config
- [x] Criar rota POST /admin/config/update
- [x] Criar template admin/config.html
- [x] Criar rota GET /admin/payments
- [x] Criar rota POST /admin/payments/{id}/sync (stub)
- [x] Criar rota GET /admin/payments/export
- [x] Criar template admin/payments.html
- [x] Atualizar dashboard admin com KPIs financeiros
- [x] Criar script create_sample_payments.py
- [x] Testar todas as interfaces

### Fase 3: API Integration ⏳
- [ ] Criar AsaasClient class
- [ ] Implementar create_payment()
- [ ] Implementar get_payment()
- [ ] Implementar create_customer()
- [ ] Criar webhook endpoint
- [ ] Validar webhook signature
- [ ] Processar eventos de pagamento
- [ ] Atualizar status automaticamente

### Fase 4: User Flow ⏳
- [ ] Criar página de checkout
- [ ] Integrar com Asaas API
- [ ] Exibir QR Code PIX
- [ ] Exibir link de boleto
- [ ] Processar cartão de crédito
- [ ] Enviar emails de confirmação
- [ ] Enviar notificações Telegram
- [ ] Atualizar plan_status do usuário

---

## 🎯 CONCLUSÃO

O **Módulo Financeiro** está **100% funcional** nas Fases 1 e 2:
- ✅ Backend completo (models, migrations, routes)
- ✅ Frontend completo (admin config, payments list, dashboard)
- ✅ Testes funcionais com dados de exemplo
- ✅ Export CSV funcional
- ✅ Color coding e UX profissional

**Próximo passo:** Fase 3 - Integração real com API Asaas para criar cobranças e processar webhooks.

---

**Desenvolvido por:** Copilot (Fintech Senior Developer Mode)
**Data:** Janeiro 2025
**Versão:** 1.0.0
