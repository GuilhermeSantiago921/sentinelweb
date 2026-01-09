# 🔄 Sincronização Automática de Pagamentos - Asaas Webhook

## ✅ O Que Foi Implementado

### 1. **Endpoint de Webhook** (`/webhooks/asaas`)
Recebe notificações em tempo real do Asaas quando o status de pagamentos muda.

**Eventos Tratados:**
- `PAYMENT_CREATED` - Pagamento criado
- `PAYMENT_UPDATED` - Pagamento atualizado
- `PAYMENT_CONFIRMED` - Pagamento confirmado (cartão de crédito)
- `PAYMENT_RECEIVED` - Pagamento recebido (PIX/Boleto)
- `PAYMENT_OVERDUE` - Pagamento vencido
- `PAYMENT_REFUNDED` - Pagamento estornado

**Funcionalidades:**
- ✅ Sincroniza status automaticamente com o banco de dados
- ✅ Faz upgrade automático do plano quando pagamento é confirmado
- ✅ Registra logs detalhados de cada notificação
- ✅ Tratamento robusto de erros
- ✅ Retorna sempre 200 OK para não causar retry infinito

---

### 2. **Sincronização Manual Melhorada** (`/admin/payments/{id}/sync`)
Agora faz sincronização real com a API do Asaas (não é mais simulada).

**Funcionalidades:**
- ✅ Consulta status real na API do Asaas
- ✅ Atualiza banco de dados local
- ✅ Faz upgrade automático do usuário se pago
- ✅ Mensagens de erro detalhadas
- ✅ Validação de configuração da API

---

## 🔧 Como Configurar o Webhook no Asaas

### Passo 1: Configurar URL Pública

O webhook precisa de uma URL pública acessível pela internet. Se você está rodando localmente, use **ngrok** para expor sua aplicação:

```bash
# Instalar ngrok (se não tiver)
brew install ngrok  # macOS
# ou baixe em: https://ngrok.com/download

# Expor porta 8000 (onde roda o SentinelWeb)
ngrok http 8000
```

O ngrok vai gerar uma URL pública como:
```
https://abc123.ngrok-free.app
```

---

### Passo 2: Configurar no Dashboard do Asaas

#### Sandbox (Testes):
1. Acesse: https://sandbox.asaas.com
2. Faça login com sua conta de testes
3. Vá em: **Configurações** → **Webhooks**
4. Clique em **"Adicionar URL de Webhook"**

#### Dados do Webhook:
```
URL: https://sua-url.ngrok-free.app/webhooks/asaas
(ou https://seu-dominio.com/webhooks/asaas em produção)

Eventos para selecionar:
☑️ PAYMENT_CREATED
☑️ PAYMENT_UPDATED
☑️ PAYMENT_CONFIRMED
☑️ PAYMENT_RECEIVED
☑️ PAYMENT_OVERDUE
☑️ PAYMENT_REFUNDED
☑️ PAYMENT_DELETED
☑️ PAYMENT_RESTORED

Status: Ativo ✅
```

5. Salve a configuração

---

### Passo 3: Testar o Webhook

#### Teste 1: Criar um Pagamento de Teste
```bash
# 1. Faça login no sistema
# 2. Vá em /upgrade
# 3. Escolha um plano (Pro ou Agency)
# 4. Selecione PIX ou Boleto
# 5. Clique em "Fazer Upgrade"
```

#### Teste 2: Simular Pagamento no Asaas
```bash
# No Dashboard do Asaas (Sandbox):
# 1. Vá em "Cobranças"
# 2. Encontre a cobrança que criou
# 3. Clique nas "..." → "Confirmar Pagamento"
# 4. Confirme a ação
```

#### Teste 3: Verificar Logs
```bash
# Acompanhe os logs do container:
docker-compose logs -f web

# Você deve ver:
# 📨 Webhook Asaas recebido: PAYMENT_RECEIVED
# ✅ Pagamento 21 sincronizado via webhook
# 🎉 Usuário user@email.com teve pagamento confirmado!
# 🚀 Upgrade: user@email.com → Plano Pro
```

#### Teste 4: Verificar Banco de Dados
```bash
# Entre no container:
docker-compose exec web bash

# Acesse o banco:
sqlite3 sentinelweb.db

# Verifique o status do pagamento:
SELECT id, asaas_id, status, payment_date FROM payments;

# Verifique o plano do usuário:
SELECT email, plan_status FROM users;
```

---

## 🧪 Teste Manual de Sincronização

Se o webhook não estiver funcionando, você pode sincronizar manualmente:

### Opção 1: Via Interface Admin
1. Acesse: `/admin/payments`
2. Encontre o pagamento
3. Clique no botão **🔄 Sync**
4. Aguarde a confirmação

### Opção 2: Via Python (Console)
```python
# Entre no container:
docker-compose exec web python

# No console Python:
from database import SessionLocal
from models import Payment
from asaas_api import AsaasAPI

db = SessionLocal()

# Busca pagamento por ID
payment = db.query(Payment).filter(Payment.id == 21).first()

# Sincroniza
asaas = AsaasAPI(db)
success = asaas.sync_payment(payment)

print(f"Sincronização: {'✅ OK' if success else '❌ Falhou'}")
print(f"Status atual: {payment.status.value}")
print(f"Pago: {payment.is_paid}")

db.close()
```

### Opção 3: Via API REST
```bash
# Faça login no admin primeiro, depois:
curl -X POST http://localhost:8000/admin/payments/21/sync \
  -H "Cookie: access_token=SEU_TOKEN_AQUI"
```

---

## 🔍 Debugging

### Webhook não está recebendo notificações

**1. Verifique se a URL está acessível:**
```bash
curl https://sua-url.ngrok-free.app/health
# Deve retornar: {"status":"healthy","timestamp":"..."}
```

**2. Teste o endpoint do webhook diretamente:**
```bash
curl -X POST http://localhost:8000/webhooks/asaas \
  -H "Content-Type: application/json" \
  -d '{
    "event": "PAYMENT_RECEIVED",
    "payment": {
      "id": "pay_abc123"
    }
  }'
```

**3. Verifique logs do Asaas:**
- No Dashboard do Asaas
- Vá em: Webhooks → Ver Logs
- Procure por erros 4xx ou 5xx

---

### Sincronização manual falha

**Erro: "Asaas API não configurada"**
```bash
# Solução: Configure a API em /admin/config
# 1. Acesse /admin/config
# 2. Preencha "Token da API"
# 3. Marque "Modo Sandbox" se estiver testando
# 4. Salve
```

**Erro: "Pagamento não encontrado"**
```bash
# Solução: Verifique se o asaas_id está correto
SELECT id, asaas_id FROM payments;
```

**Erro: "Connection timeout"**
```bash
# Solução: Verifique conectividade com API do Asaas
curl -H "access_token: SEU_TOKEN" https://sandbox.asaas.com/api/v3/payments
```

---

## 📊 Fluxo Completo

### Fluxo Automático (Webhook)
```
1. Usuário cria pagamento → Sistema salva no DB (status: PENDING)
2. Usuário paga PIX/Boleto → Asaas detecta pagamento
3. Asaas envia webhook → /webhooks/asaas
4. Sistema sincroniza → Atualiza status (RECEIVED)
5. Sistema faz upgrade → user.plan_status = 'pro'
6. (Opcional) Envia notificação → Telegram/Email
```

### Fluxo Manual (Admin)
```
1. Admin acessa → /admin/payments
2. Admin clica → Botão "Sync" no pagamento
3. Sistema consulta → API Asaas (/payments/{id})
4. Sistema atualiza → status no banco
5. Se pago → Faz upgrade do usuário
6. Retorna → Mensagem de sucesso
```

---

## 🚀 Próximos Passos

### Fase 1: Notificações ✅ (Já funciona via Telegram)
```python
# Em scanner.py já existe send_telegram_alert()
# Basta descomentar no webhook:

if payment.status in [PaymentStatus.RECEIVED, PaymentStatus.CONFIRMED]:
    user = db.query(User).filter(User.id == payment.user_id).first()
    if user and user.telegram_chat_id:
        from scanner import send_telegram_alert
        message = f"""
🎉 <b>PAGAMENTO CONFIRMADO!</b>

✅ Seu plano foi atualizado para <b>{user.plan_status.upper()}</b>!

💰 Valor: R$ {payment.value:.2f}
📅 Data: {payment.payment_date.strftime('%d/%m/%Y %H:%M')}

Aproveite todos os recursos! 🚀
        """
        send_telegram_alert(message, user.telegram_chat_id)
```

### Fase 2: Email de Confirmação ⏳
```python
# Implementar envio de email com:
# - Link da fatura
# - Detalhes do plano
# - Próxima cobrança (se recorrente)
```

### Fase 3: Histórico de Pagamentos do Usuário ⏳
```python
# Criar rota /user/payments
# Exibir histórico de faturas
# Permitir download de recibos
```

### Fase 4: Assinaturas Recorrentes ⏳
```python
# Migrar de pagamentos únicos para assinaturas
# Usar AsaasService em vez de AsaasAPI
# Cobranças automáticas mensais
```

---

## ✅ Checklist de Configuração

### Sandbox (Testes)
- [ ] Token API configurado em `/admin/config`
- [ ] Modo Sandbox habilitado
- [ ] Ngrok rodando (se local)
- [ ] Webhook configurado no Asaas Sandbox
- [ ] Teste de criação de pagamento
- [ ] Teste de confirmação manual no Asaas
- [ ] Logs do webhook funcionando

### Produção
- [ ] Token API de produção configurado
- [ ] Modo Sandbox desabilitado
- [ ] SSL/HTTPS configurado no servidor
- [ ] Webhook configurado no Asaas Produção
- [ ] Teste com pagamento real (valor baixo)
- [ ] Monitoramento de logs ativo
- [ ] Backup do banco de dados configurado

---

## 📞 Suporte

### Problemas com Webhook?
1. Verifique logs: `docker-compose logs -f web`
2. Teste URL pública: `curl https://sua-url/health`
3. Verifique configuração no Asaas Dashboard
4. Teste manualmente: Botão "Sync" em `/admin/payments`

### Problemas com Sincronização?
1. Verifique token API em `/admin/config`
2. Teste conectividade: `curl -H "access_token: TOKEN" https://sandbox.asaas.com/api/v3/payments`
3. Verifique `asaas_id` do pagamento no banco
4. Consulte logs de erro no console

---

## 📚 Referências

- **Asaas API Docs**: https://docs.asaas.com/reference/
- **Webhooks**: https://docs.asaas.com/docs/webhooks
- **Ngrok**: https://ngrok.com/docs
- **FastAPI Webhooks**: https://fastapi.tiangolo.com/advanced/websockets/

---

**🎉 Implementação Completa! Sistema agora sincroniza automaticamente com Asaas!**
