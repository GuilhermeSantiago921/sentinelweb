# 🔔 Configuração do Webhook Asaas - Sincronização Automática

## ✅ Problema Resolvido

**Situação anterior:** Pagamentos não sincronizavam automaticamente com o sistema.

**Solução implementada:** 
1. ✅ Webhook endpoint `/webhooks/asaas` criado
2. ✅ Sincronização automática ativa
3. ✅ Notificações Telegram integradas
4. ✅ Seu pagamento **ID 26** foi sincronizado manualmente e está ativo!

---

## 📋 Status Atual

### Seu Pagamento
- **ID:** 26
- **Status:** ✅ RECEBIDO (received)
- **Valor:** R$ 49,00
- **Plano:** Pro - Ativado com sucesso!
- **Asaas ID:** pay_l30j7aj5j9vz25to

### Webhook
- **Endpoint:** `POST /webhooks/asaas`
- **Status:** ✅ Implementado e ativo
- **Funcionalidades:**
  - Sincronização automática de pagamentos
  - Upgrade automático de plano
  - Notificação via Telegram (se configurado)
  - Logs detalhados

---

## 🚀 Como Configurar o Webhook no Asaas

Para que **futuros pagamentos** sincronizem automaticamente, você precisa configurar o webhook no dashboard do Asaas:

### Passo 1: Acessar Dashboard Asaas

1. Acesse: https://www.asaas.com (ou https://sandbox.asaas.com se estiver em modo sandbox)
2. Faça login com suas credenciais
3. No menu lateral, procure por **"Integrações"** ou **"Configurações"**
4. Clique em **"Webhooks"**

### Passo 2: Criar Novo Webhook

1. Clique em **"Adicionar Webhook"** ou **"Nova URL"**
2. Preencha os campos:

#### **URL do Webhook**

**Se estiver rodando localmente (localhost):**
```
Você precisa expor com ngrok primeiro (veja Passo 3)
```

**Se estiver em produção (servidor):**
```
https://seu-dominio.com/webhooks/asaas
```

#### **Eventos a Selecionar**

Marque os seguintes eventos:

- ✅ `PAYMENT_RECEIVED` - Pagamento recebido
- ✅ `PAYMENT_CONFIRMED` - Pagamento confirmado
- ✅ `PAYMENT_OVERDUE` - Pagamento vencido
- ✅ `PAYMENT_DELETED` - Pagamento cancelado
- ✅ `PAYMENT_RESTORED` - Pagamento restaurado
- ✅ `PAYMENT_UPDATED` - Pagamento atualizado

#### **Autenticação** (Opcional)
- Você pode deixar em branco por enquanto
- Se quiser mais segurança, configure um token no campo `asaas_webhook_secret` no Admin → Configurações

3. Clique em **"Salvar"**

### Passo 3: Expor Localhost com ngrok (Apenas para Desenvolvimento Local)

Se você está rodando o sistema **localmente** (localhost:8000), precisa expor a aplicação com o ngrok:

#### Instalação do ngrok

**macOS:**
```bash
brew install ngrok
```

**Ou baixe direto:**
```bash
# Acesse: https://ngrok.com/download
# Faça login e copie o token de autenticação
```

#### Usar ngrok

1. **Inicie o túnel:**
```bash
ngrok http 8000
```

2. **Copie a URL gerada** (exemplo):
```
Forwarding: https://a1b2-3c4d-5e6f.ngrok.io -> http://localhost:8000
```

3. **Configure no Asaas:**
```
https://a1b2-3c4d-5e6f.ngrok.io/webhooks/asaas
```

4. **Mantenha o ngrok rodando** enquanto testar

⚠️ **IMPORTANTE:** A URL do ngrok muda toda vez que você reinicia! Para URL fixa, use o plano pago do ngrok ou deploy em um servidor.

---

## 🧪 Testar o Webhook

### Opção 1: Teste Manual no Asaas Dashboard

1. Acesse o dashboard do Asaas
2. Vá em **Integrações → Webhooks**
3. Clique no webhook que você criou
4. Clique em **"Testar Webhook"** ou **"Enviar Teste"**
5. Verifique os logs do sistema:

```bash
docker-compose logs -f web | grep -i webhook
```

Você deve ver algo como:
```
📨 Webhook Asaas recebido: PAYMENT_RECEIVED
✅ Pagamento 26 sincronizado! Novo status: received
```

### Opção 2: Fazer um Pagamento Real (Sandbox)

1. Acesse `/upgrade` no sistema
2. Escolha um plano
3. Gere um boleto ou PIX de teste
4. No dashboard do Asaas (sandbox), marque o pagamento como **"Recebido"** manualmente
5. O webhook será disparado automaticamente
6. Verifique os logs:

```bash
docker-compose logs -f web | grep -i "pagamento\|webhook"
```

---

## 📊 Monitorar Webhooks

### Ver Logs em Tempo Real

```bash
# Terminal 1: Logs do sistema
docker-compose logs -f web

# Terminal 2: Filtrar apenas webhooks
docker-compose logs -f web | grep -i webhook
```

### Logs Esperados (Sucesso)

```
📨 Webhook Asaas recebido: PAYMENT_RECEIVED
📦 Payload: {'event': 'PAYMENT_RECEIVED', 'payment': {...}}
✅ Pagamento encontrado: ID=26, Status atual=pending
✅ Pagamento 26 sincronizado! Novo status: received
📱 Notificação Telegram enviada para usuario@email.com
```

### Logs de Erro (Falha)

```
⚠️  Webhook sem dados de pagamento
⚠️  Pagamento pay_xxx não encontrado no banco
❌ Erro ao sincronizar pagamento 26
```

---

## 🔧 Solução de Problemas

### ❌ Webhook não está sendo chamado

**Possíveis causas:**

1. **URL incorreta no Asaas**
   - Verifique se a URL está correta
   - Certifique-se que termina com `/webhooks/asaas`
   - Teste com curl:
   ```bash
   curl -X POST http://localhost:8000/webhooks/asaas \
     -H "Content-Type: application/json" \
     -d '{"event":"PAYMENT_RECEIVED","payment":{"id":"test"}}'
   ```

2. **ngrok não está rodando** (localhost)
   - Inicie o ngrok: `ngrok http 8000`
   - Atualize a URL no Asaas com a nova URL do ngrok

3. **Firewall bloqueando** (produção)
   - Libere a porta 443 (HTTPS)
   - Permita IPs do Asaas no firewall

4. **SSL inválido** (produção)
   - Certifique-se que o certificado SSL está válido
   - Use Let's Encrypt: `certbot --nginx`

### ❌ Webhook está sendo chamado mas não sincroniza

**Verifique:**

1. **Logs do sistema:**
```bash
docker-compose logs web --tail 50 | grep -i webhook
```

2. **Asaas ID está correto:**
```bash
docker-compose exec web python -c "
from database import SessionLocal
from models import Payment
db = SessionLocal()
payment = db.query(Payment).filter(Payment.asaas_id == 'SEU_ASAAS_ID').first()
print(f'Encontrado: {payment is not None}')
db.close()
"
```

3. **API do Asaas está configurada:**
- Acesse: `/admin/config`
- Verifique se o `asaas_api_token` está preenchido
- Teste com: `GET /test/asaas`

### ❌ Pagamento sincronizou mas plano não atualizou

**Verifique:**

1. **Status do pagamento:**
```bash
docker-compose exec web python -c "
from database import SessionLocal
from models import Payment, User
db = SessionLocal()
payment = db.query(Payment).filter(Payment.id == 26).first()
user = db.query(User).filter(User.id == payment.user_id).first()
print(f'Status pagamento: {payment.status.value}')
print(f'Plano usuário: {user.plan_status}')
db.close()
"
```

2. **Sincronize manualmente:**
- Acesse: `/admin/payments`
- Clique em **"Sincronizar"** no pagamento
- Ou use o script:
```bash
docker-compose exec web python -c "
from database import SessionLocal
from models import Payment
from asaas_api import AsaasAPI
db = SessionLocal()
payment = db.query(Payment).filter(Payment.id == 26).first()
asaas = AsaasAPI(db)
asaas.sync_payment(payment)
db.close()
"
```

---

## 📱 Notificações Telegram

O webhook também envia notificações via Telegram automaticamente quando um pagamento é confirmado!

### Mensagem Enviada:

```
🎉 PAGAMENTO CONFIRMADO

💰 Valor: R$ 49,00
📦 Plano: Pro
👤 Cliente: seu@email.com
🏢 Empresa: Sua Empresa
⏰ Data: 08/01/2026 14:30:00
🆔 ID: pay_l30j7aj5j9vz25to

✅ O plano foi ativado automaticamente!
```

### Configurar Telegram:

1. Configure seu `telegram_chat_id` no perfil
2. Siga as instruções em: `TELEGRAM_SETUP.md`
3. O webhook enviará automaticamente quando pagamentos forem confirmados

---

## 🎯 Resumo - Próximos Passos

### ✅ JÁ FEITO:
- [x] Webhook implementado no código
- [x] Sistema reiniciado
- [x] Seu pagamento ID 26 sincronizado manualmente
- [x] Plano Pro ativado com sucesso!

### 📋 VOCÊ PRECISA FAZER:

#### **Para Ambiente Local (Desenvolvimento):**
1. [ ] Instalar ngrok: `brew install ngrok`
2. [ ] Iniciar ngrok: `ngrok http 8000`
3. [ ] Copiar URL gerada
4. [ ] Configurar no Asaas Dashboard → Webhooks
5. [ ] URL: `https://xxx.ngrok.io/webhooks/asaas`
6. [ ] Testar com pagamento sandbox

#### **Para Ambiente de Produção:**
1. [ ] Deploy em servidor com domínio
2. [ ] Configurar SSL (Let's Encrypt)
3. [ ] Acessar Asaas Dashboard → Webhooks
4. [ ] URL: `https://seu-dominio.com/webhooks/asaas`
5. [ ] Selecionar eventos: PAYMENT_*
6. [ ] Salvar e testar

---

## 📞 Suporte

### Problema com o Webhook?

```bash
# Ver logs do webhook
docker-compose logs -f web | grep webhook

# Testar endpoint manualmente
curl -X POST http://localhost:8000/webhooks/asaas \
  -H "Content-Type: application/json" \
  -d '{"event":"PAYMENT_RECEIVED","payment":{"id":"pay_test"}}'
```

### Sincronizar Pagamento Manualmente

1. **Via Interface Admin:**
   - Acesse: `/admin/payments`
   - Encontre o pagamento
   - Clique em **"Sincronizar"**

2. **Via Script:**
```bash
docker-compose exec web python -c "
from database import SessionLocal
from models import Payment
from asaas_api import AsaasAPI
db = SessionLocal()
payment = db.query(Payment).filter(Payment.id == SEU_ID).first()
asaas = AsaasAPI(db)
asaas.sync_payment(payment)
print(f'Status: {payment.status.value}')
db.close()
"
```

---

## ✅ Checklist de Configuração

- [x] Webhook implementado no código
- [x] Sistema reiniciado
- [x] Pagamento sincronizado manualmente
- [ ] ngrok instalado (se local)
- [ ] ngrok rodando (se local)
- [ ] Webhook configurado no Asaas Dashboard
- [ ] Eventos PAYMENT_* selecionados
- [ ] Teste realizado com sucesso
- [ ] Logs mostrando "Webhook recebido"
- [ ] Telegram configurado (opcional)

---

**Parabéns! Seu pagamento foi sincronizado e o sistema está pronto para sincronizações automáticas! 🎉**

Qualquer dúvida, verifique os logs: `docker-compose logs -f web`
