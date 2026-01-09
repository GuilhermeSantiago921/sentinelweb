# 📱 Configuração de Alertas via Telegram - SentinelWeb

Este guia explica como configurar notificações via Telegram no SentinelWeb para receber alertas em tempo real sobre:
- ⛔ Sites offline (quedas)
- ✅ Sites recuperados (voltaram ao ar)
- 🔔 Heartbeats atrasados (scripts/cron jobs não executaram)
- 💰 Pagamentos recebidos via Asaas

---

## 🎯 Visão Geral

O processo de configuração tem **3 etapas simples**:

1. **Criar um bot no Telegram** (1 minuto)
2. **Obter seu Chat ID** (1 minuto)
3. **Configurar no SentinelWeb** (30 segundos)

**Tempo total: ~3 minutos** ⏱️

---

## 🤖 Passo 1: Criar seu Bot no Telegram

### 1.1. Abrir o BotFather

1. Abra o **aplicativo Telegram** (ou acesse https://web.telegram.org)
2. Na busca, digite: `@BotFather`
3. Abra o chat oficial do **BotFather** (verificado com ✅)
4. Clique em **Iniciar** ou envie `/start`

### 1.2. Criar o Bot

No chat com o BotFather, envie o comando:

```
/newbot
```

**O BotFather vai pedir:**

1️⃣ **Nome do bot** (pode ser qualquer nome):
```
SentinelWeb Monitor
```
*ou escolha outro nome de sua preferência*

2️⃣ **Username do bot** (deve terminar com `bot`):
```
sentinelweb_monitor_bot
```
*ou outro disponível, ex: `meusite_monitor_bot`*

### 1.3. Copiar o Token de Acesso

✅ Se tudo der certo, o BotFather enviará uma mensagem assim:

```
Done! Congratulations on your new bot.

Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789

Keep your token secure and store it safely.
```

**🔑 COPIE ESSE TOKEN!** Você vai usá-lo no próximo passo.

**⚠️ IMPORTANTE:**
- Nunca compartilhe esse token publicamente
- Qualquer pessoa com ele pode controlar seu bot
- Se vazar, revogue-o enviando `/revoke` ao BotFather

---

## � Passo 2: Obter seu Chat ID

### 2.1. Iniciar Conversa com o Bot

1. Abra o **Telegram**
2. Busque pelo username do seu bot (ex: `@sentinelweb_monitor_bot`)
3. Clique em **Iniciar** ou envie `/start`
4. Envie qualquer mensagem (ex: "Olá")

### 2.2. Descobrir o Chat ID

Existem **3 formas** de obter seu Chat ID:

#### 🥇 **Opção A: Bot UserInfo (MAIS FÁCIL)**

1. Busque por `@userinfobot` no Telegram
2. Clique em **Iniciar**
3. Ele enviará automaticamente suas informações:
   ```
   Id: 123456789
   First name: Seu Nome
   Username: @seu_username
   ```
4. **COPIE O NÚMERO DO `Id`** (ex: `123456789`)

⚠️ **IMPORTANTE:** Certifique-se de copiar o ID da SUA CONTA PESSOAL, não o ID do bot que você criou!

#### 🥈 **Opção B: JSON ID Bot (ALTERNATIVA)**

1. Busque por `@getidsbot` no Telegram
2. Envie `/start`
3. Ele responderá com seu ID:
   ```
   Your user ID: 123456789
   ```
4. **COPIE O NÚMERO**

#### 🥉 **Opção C: Via API do Telegram (MANUAL)**

1. Certifique-se que enviou uma mensagem para seu bot
2. Abra no navegador (substitua `<SEU_TOKEN>` pelo token do passo 1):
   ```
   https://api.telegram.org/bot<SEU_TOKEN>/getUpdates
   ```

3. Procure por `"chat":{"id":` no JSON retornado:
   ```json
   {
     "result": [{
       "message": {
         "chat": {
           "id": 123456789,  ← ESSE É SEU CHAT ID
           "first_name": "Seu Nome"
         }
       }
     }]
   }
   ```

4. **COPIE O NÚMERO DO `id`**

---

## ⚙️ Passo 3: Configurar no SentinelWeb

### 3.1. Acessar seu Perfil

1. Acesse o SentinelWeb: **http://localhost:8000**
2. Faça **login** com suas credenciais
3. Clique em **"Perfil"** no menu superior

### 3.2. Configurar Chat ID

1. Role até a seção **"Notificações via Telegram"**
2. Cole seu **Chat ID** no campo (ex: `123456789`)
3. (Opcional) Atualize o **Nome da Empresa** e **CPF/CNPJ**
4. Clique em **"Salvar Alterações"**

### 3.3. 🧪 Testar a Conexão

Após salvar, você pode testar se está funcionando:

**Opção 1: Botão de Teste (Interface)**
1. Na página de perfil, clique em **"Enviar mensagem de teste"**
2. Verifique o Telegram - você deve receber:

```
🧪 TESTE DE NOTIFICAÇÃO

✅ Seu SentinelWeb está configurado corretamente!

👤 Usuário: seu@email.com
🏢 Empresa: Sua Empresa
⏰ Data/Hora: 08/01/2026 15:30:45 UTC

Você receberá alertas quando seus sites ficarem offline ou voltarem ao ar.
```

**Opção 2: Teste via API**
```bash
# Obtenha seu token de acesso (login via API)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"seu@email.com","password":"sua_senha"}'

# Use o token retornado para testar Telegram
curl -X POST http://localhost:8000/api/test-telegram \
  -H "Authorization: Bearer SEU_TOKEN_JWT"
```

**✅ Se recebeu a mensagem, está funcionando!**

---

## 🚨 Tipos de Alertas que Você Receberá

### 1️⃣ Site OFFLINE (Queda Detectada)

```
🚨 ALERTA - SITE FORA DO AR

🌐 Site: Meu Site Cliente
🔗 Domínio: cliente.com.br
⏰ Horário: 08/01/2026 15:45:12 UTC
❌ Status: OFFLINE (500)
📝 Erro: Internal Server Error
⏱️ Latência: timeout
```

**Quando dispara:**
- Site estava online
- Passou para offline (HTTP status não é 2xx/3xx)
- Timeout de conexão
- Erro de DNS
- Certificado SSL inválido

### 2️⃣ Site RECUPERADO (Voltou ao Ar)

```
✅ RECUPERAÇÃO - SITE VOLTOU

🌐 Site: Meu Site Cliente
🔗 Domínio: cliente.com.br
⏰ Horário: 08/01/2026 16:10:33 UTC
✅ Status: ONLINE (200)
⚡ Latência: 145ms
🔄 Tempo offline: 25 minutos
```

**Quando dispara:**
- Site estava offline
- Voltou a ficar online (HTTP status 2xx/3xx)
- Respondeu com sucesso

### 3️⃣ Heartbeat Atrasado (Cron/Script Não Executou)

```
⚠️ HEARTBEAT ATRASADO

📌 Nome: Backup Diário
⏰ Último ping: 08/01/2026 03:00:00 UTC
🕐 Esperado a cada: 24 horas
⏳ Atraso: 2 horas e 30 minutos

Verifique se o script/cron job está executando corretamente.
```

**Quando dispara:**
- Script/cron job não enviou ping no período esperado
- Ultrapassou o período de tolerância (grace period)

### 4️⃣ Pagamento Recebido (Asaas Gateway)

```
🎉 PAGAMENTO CONFIRMADO

💰 Valor: R$ 49,00
📦 Plano: Pro
👤 Cliente: cliente@email.com
🏢 Empresa: Minha Empresa
⏰ Data: 08/01/2026 14:30:00 UTC
🆔 ID: pay_1234567890

✅ O plano foi ativado automaticamente!
```

**Quando dispara:**
- Webhook do Asaas notifica pagamento confirmado
- Status muda para RECEIVED ou CONFIRMED
- Upgrade de plano automático

---

## 🔧 Solução de Problemas

### ❌ "Erro ao enviar mensagem de teste"

#### **Problema 1: Token Inválido**
```bash
# Verifique se o token está correto no arquivo .env
cat .env | grep TELEGRAM_BOT_TOKEN

# Deve mostrar algo como:
# TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNO...
```

**Solução:**
- Copie o token completo do BotFather (sem espaços)
- Certifique-se que não quebrou em múltiplas linhas
- Reinicie o sistema após alterar

#### **Problema 2: Chat ID Incorreto**
- Chat ID deve ser apenas números (ex: `123456789`)
- Não adicione espaços ou caracteres especiais
- Certifique-se que iniciou conversa com o bot antes

#### **Problema 3: Bot Não Iniciado**
1. Abra o Telegram
2. Busque seu bot pelo username
3. Clique em **"Iniciar"** ou envie `/start`
4. Envie qualquer mensagem
5. Tente o teste novamente

#### **Problema 4: Variável de Ambiente Não Carregada**
```bash
# Se usar Docker, verifique se a variável foi carregada:
docker-compose exec web env | grep TELEGRAM

# Deve mostrar:
# TELEGRAM_BOT_TOKEN=1234567890:ABC...

# Se não aparecer, edite docker-compose.yml:
services:
  web:
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
```

**Depois reinicie:**
```bash
docker-compose down
docker-compose up -d
```

### ❌ "Não estou recebendo alertas automáticos"

**Checklist completo:**

- [ ] ✅ Token configurado no sistema?
- [ ] ✅ Chat ID configurado no perfil?
- [ ] ✅ Mensagem de teste funcionou?
- [ ] ✅ Site monitorado está ativo?
- [ ] ✅ Celery Worker está rodando?
  ```bash
  docker-compose ps
  # Todos devem estar "Up"
  ```
- [ ] ✅ Logs do Celery sem erros?
  ```bash
  docker-compose logs celery_worker | tail -50
  ```
- [ ] ✅ Site realmente mudou de status (online→offline)?

**Teste forçar mudança de status:**
```bash
# Pare temporariamente um site para forçar alerta
# Ou edite o domínio para um inválido como "site-inexistente.com"
```

### ❌ "Forbidden: bot was blocked by the user"

**Causa:** Você bloqueou o bot no Telegram.

**Solução:**
1. Abra o Telegram
2. Busque pelo seu bot
3. Clique no nome do bot no topo
4. Clique em **"Desbloquear"** ou **"Restart"**
5. Envie `/start` novamente
6. Teste novamente no SentinelWeb

### ❌ "Forbidden: bots can't send messages to bots"

**Causa:** Você configurou o Chat ID do próprio bot ao invés do seu Chat ID pessoal.

**Solução:**
1. O Chat ID deve ser da **sua conta pessoal do Telegram**, não do bot
2. Use o `@userinfobot` para obter SEU Chat ID (da sua conta)
3. Certifique-se de iniciar conversa com o bot que você criou ANTES
4. Atualize o Chat ID no perfil do SentinelWeb
5. Teste novamente

**Como diferenciar:**
- ✅ **Chat ID pessoal**: Número de 9-10 dígitos (ex: 123456789)
- ❌ **Chat ID de bot**: Geralmente começa com números altos ou negativos

### ❌ "Bad Request: chat not found"

**Causa:** Chat ID incorreto ou bot não foi iniciado.

**Solução:**
1. Verifique se o Chat ID está correto (só números)
2. Certifique-se que iniciou conversa com o bot primeiro
3. Tente obter o Chat ID novamente usando `@userinfobot`

---

## 📊 Monitoramento e Logs

### Ver Logs de Alertas Enviados

```bash
# Docker - Logs do Celery Worker
docker-compose logs celery_worker | grep -i telegram

# Saída esperada (sucesso):
# ✅ Alerta Telegram enviado para chat_id 123456789
# 🚨 Enviando alerta de QUEDA para cliente.com.br

# Saída de erro (investigar):
# ❌ Erro ao enviar Telegram: Invalid token
# ❌ Erro ao enviar Telegram: Chat not found
```

### Ver Tasks em Execução (Flower)

Se você configurou o Flower (ferramenta de monitoramento do Celery):

1. Acesse: **http://localhost:5555**
2. Clique em **"Tasks"**
3. Procure por `scan_site` e `check_heartbeats`
4. Veja os logs detalhados de cada execução

### Testar Envio Manual (Debug)

```python
# Abra o shell Python no container
docker-compose exec web python

# No shell Python:
from scanner import send_telegram_alert

# Teste o envio
result = send_telegram_alert(
    "🧪 Teste manual de alerta",
    "123456789"  # Substitua pelo seu Chat ID
)

print(f"Resultado: {result}")
# Deve retornar True se funcionou
```

---

## 🔒 Segurança

### Boas Práticas

1. **Nunca compartilhe seu Token**
   - Não faça commit do `.env` no Git
   - Use `.gitignore` para excluir `.env`

2. **Proteja seu Chat ID**
   - Não exponha publicamente
   - Qualquer pessoa com ele pode enviar mensagens

3. **Revogue tokens comprometidos**
   ```
   Envie /revoke no BotFather
   Depois crie um novo bot
   ```

4. **Use variáveis de ambiente**
   - Nunca hardcode tokens no código
   - Use sempre `.env` ou secrets do Docker

---

## 🌐 Testando em Produção

### Usar Variáveis de Ambiente do Servidor

Se estiver em produção (AWS, Heroku, etc):

```bash
# Definir variável no sistema
export TELEGRAM_BOT_TOKEN="seu_token_aqui"

# Ou no Docker Compose:
docker-compose up -d \
  -e TELEGRAM_BOT_TOKEN="seu_token_aqui"
```

### Telegram Web (sem app)

Você pode usar o Telegram pelo navegador:
- https://web.telegram.org

Funciona igual ao aplicativo!

---

## 📞 Suporte

### Problemas com o Telegram?

- **Documentação oficial**: https://core.telegram.org/bots
- **FAQ do BotFather**: Envie `/help` para `@BotFather`

### Problemas com o SentinelWeb?

1. Verifique os logs:
   ```bash
   docker-compose logs -f celery_worker
   ```

2. Teste manualmente a função:
   ```python
   from scanner import send_telegram_alert
   
   send_telegram_alert(
       "Teste manual",
       "seu_chat_id"
   )
   ```

3. Verifique se o requests está instalado:
   ```bash
   pip list | grep requests
   ```

---

## ✅ Checklist Final

- [ ] Bot criado no BotFather
- [ ] Token copiado e guardado
- [ ] Token adicionado ao `.env`
- [ ] Chat ID obtido
- [ ] Chat ID configurado no perfil
- [ ] Teste enviado com sucesso
- [ ] Sistema reiniciado
- [ ] Pronto para receber alertas!

---

**Parabéns! Seu sistema de alertas via Telegram está configurado! 🎉**

Agora você será notificado instantaneamente quando algo acontecer com seus sites monitorados.
