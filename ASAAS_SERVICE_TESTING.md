# 🧪 Guia de Teste - AsaasService

## 🚀 Como Testar o Serviço

### 1. Verificar Configuração

Acesse o painel administrativo:
```
http://localhost:8000/admin/config
```

Certifique-se de que:
- ✅ **Asaas API Token** está preenchido
- ✅ **Sandbox Mode** está ativado (para testes)

### 2. Obter Token de Autenticação

Faça login no sistema:
```
http://localhost:8000/login
```

Após login, abra o DevTools do navegador (F12) e vá em:
```
Application → Cookies → access_token
```

Copie o valor do cookie `access_token`.

### 3. Testar Criação de Assinatura

#### Via cURL (Terminal)

```bash
# Assinatura Pro com PIX
curl -X POST "http://localhost:8000/api/test/asaas/create-subscription?plan=pro&billing_type=PIX" \
  -H "Cookie: access_token=SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json"

# Assinatura Agency com Boleto
curl -X POST "http://localhost:8000/api/test/asaas/create-subscription?plan=agency&billing_type=BOLETO" \
  -H "Cookie: access_token=SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json"
```

#### Via Navegador (Mais Fácil)

1. Faça login no SentinelWeb
2. Cole esta URL no navegador:
```
http://localhost:8000/api/test/asaas/create-subscription?plan=pro&billing_type=PIX
```

3. Você verá uma resposta JSON com:
```json
{
  "success": true,
  "message": "Assinatura criada com sucesso!",
  "subscription": {
    "id": "sub_abc123",
    "customer_id": "cus_abc123",
    "plan": "pro",
    "value": 49.9,
    "billing_type": "PIX",
    "next_due_date": "2026-01-08",
    "status": "ACTIVE"
  },
  "payment_url": "https://sandbox.asaas.com/i/abc123",
  "instructions": "Acesse o link acima e escaneie o QR Code para pagar"
}
```

4. **Copie o `payment_url`** e acesse em uma nova aba
5. Você verá a página de pagamento do Asaas com:
   - QR Code PIX (se escolheu PIX)
   - Link para download do boleto (se escolheu BOLETO)

### 4. Testar Busca de Assinatura

```bash
# Substitua sub_abc123 pelo ID retornado no passo anterior
curl -X GET "http://localhost:8000/api/test/asaas/get-subscription/sub_abc123" \
  -H "Cookie: access_token=SEU_TOKEN_AQUI"
```

### 5. Testar Cancelamento

```bash
# ATENÇÃO: Isso cancela de verdade a assinatura no Asaas
curl -X DELETE "http://localhost:8000/api/test/asaas/cancel-subscription/sub_abc123" \
  -H "Cookie: access_token=SEU_TOKEN_AQUI"
```

---

## 📊 Verificar no Dashboard do Asaas

1. Acesse o Sandbox do Asaas:
```
https://sandbox.asaas.com
```

2. Faça login com suas credenciais

3. Vá em **Cobranças** → **Assinaturas**

4. Você verá todas as assinaturas criadas pelo teste!

---

## 🐛 Troubleshooting

### Erro: "Token da API Asaas não configurado"

**Solução:** Acesse `/admin/config` e preencha o token.

### Erro: "Configuração do sistema não encontrada"

**Solução:** Execute a migração:
```bash
docker-compose exec web python migrate_financial.py
```

### Erro: "CPF inválido"

**Solução:** O serviço usa o CPF/CNPJ do usuário. Se não tiver, precisa adicionar:
1. Acesse o dashboard
2. Preencha o modal de CPF/CNPJ
3. Tente criar a assinatura novamente

### Erro: "Timeout ao conectar com a API"

**Solução:** Verifique sua conexão com a internet. A API do Asaas precisa estar acessível.

---

## 📝 Logs Detalhados

O AsaasService imprime logs muito úteis no console:

```bash
# Ver logs em tempo real
docker-compose logs -f web
```

Você verá:
```
🔵 Asaas API Request: POST /subscriptions
📤 Payload: {'customer': 'cus_abc123', ...}
📥 Response Status: 200
📥 Response Body: {'id': 'sub_abc123', ...}
✅ Assinatura criada: sub_abc123
```

---

## 🎯 Próximos Passos

Após confirmar que tudo funciona:

1. ✅ **Integrar com fluxo de upgrade**
   - Substituir `/checkout` atual por AsaasService
   - Criar assinatura em vez de pagamento único

2. ✅ **Implementar Webhooks**
   - Endpoint `/webhooks/asaas`
   - Sincronização automática de status

3. ✅ **Salvar Assinaturas no Banco**
   - Criar modelo `Subscription`
   - Vincular ao usuário

4. ✅ **Email de Confirmação**
   - Enviar link de pagamento por email
   - Notificar quando pagamento for confirmado

---

**Happy Testing! 🚀**
