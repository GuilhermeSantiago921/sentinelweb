# 🚀 DEPLOY ADMIN PANEL - CORREÇÕES COMPLETAS

## ❌ Erros Identificados e Corrigidos

### Erro #1: `ModuleNotFoundError: No module named 'jwt'`
- **Causa:** Linha 16 tinha `import jwt` mas PyJWT não está instalado
- **Solução:** Removido import jwt (não é necessário, usa python-jose via auth.py)

### Erro #2: `ImportError: cannot import name 'async_session_maker'`
- **Causa:** AdminAuth usava async mas database.py é síncrono
- **Solução:** Convertido AdminAuth para síncrono usando SessionLocal

### Erro #3: `ImportError: cannot import name 'verify_token'`
- **Causa:** admin.py importava verify_token mas auth.py tem decode_token
- **Solução:** Substituído verify_token por decode_token + validação

---

## ✅ CORREÇÕES APLICADAS NO CÓDIGO LOCAL

Todos os 3 erros foram corrigidos em `admin.py`:
- ✅ Removido `import jwt`
- ✅ Convertido para SessionLocal (síncrono)
- ✅ Substituído verify_token por decode_token

---

## 📦 DEPLOY PARA SERVIDOR

Siga estes passos **NA SUA MÁQUINA LOCAL** primeiro:

### 1️⃣ Commit e Push das Mudanças

```bash
cd /Users/guilherme/Documents/Sistema\ de\ monitoramento/sentinelweb

# Adicionar admin.py ao Git
git add admin.py

# Commit
git commit -m "fix: Resolve all admin panel import errors (jwt, async_session_maker, verify_token)"

# Push para GitHub
git push origin main
```

**⚠️ IMPORTANTE:** Você DEVE fazer isso na sua máquina local para que as mudanças cheguem ao servidor!

---

### 2️⃣ Atualizar no Servidor

Agora conecte ao servidor e atualize:

```bash
# Conectar ao servidor
ssh root@SEU_IP_DO_SERVIDOR

# Ir para o diretório
cd /opt/sentinelweb

# Fazer backup do arquivo atual
cp admin.py admin.py.backup_antes_fix

# Puxar mudanças do GitHub
git pull origin main

# Verificar se admin.py foi atualizado
grep -n "import jwt" admin.py
# Não deve retornar nada (sem import jwt)

grep -n "decode_token" admin.py
# Deve mostrar linha com decode_token
```

---

### 3️⃣ Rebuild e Restart dos Containers

```bash
cd /opt/sentinelweb

# Parar containers
docker compose -f docker-compose.prod.yml down

# Rebuild da imagem web (sem cache)
docker compose -f docker-compose.prod.yml build --no-cache web

# Iniciar todos os containers
docker compose -f docker-compose.prod.yml up -d

# Aguardar 30 segundos
sleep 30

# Verificar status
docker compose -f docker-compose.prod.yml ps
```

---

### 4️⃣ Verificar Logs

```bash
# Ver logs do container web
docker compose -f docker-compose.prod.yml logs --tail=50 web

# Não deve haver mais erros de import!
# Deve mostrar:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

---

### 5️⃣ Testar Aplicação

```bash
# Testar endpoint de saúde
curl http://localhost:8000/health

# Deve retornar algo como:
# {"status":"healthy","timestamp":"..."}

# Testar via HTTPS
curl -I https://seudominio.com.br

# Deve retornar: HTTP/2 200
```

---

### 6️⃣ Reiniciar Nginx (se necessário)

```bash
# Se o HTTPS não funcionar, reinicie o Nginx
systemctl restart nginx

# Verificar status
systemctl status nginx
```

---

### 7️⃣ Criar Superusuário Admin

```bash
cd /opt/sentinelweb

docker compose -f docker-compose.prod.yml exec web python setup_admin.py
```

Informe:
- **Nome completo:** Seu nome
- **Email:** seu@email.com
- **Senha:** Uma senha forte

---

### 8️⃣ Acessar Painel Admin

Abra seu navegador:

```
https://seudominio.com.br/admin
```

Faça login com as credenciais criadas no passo 7.

---

## 🔍 VERIFICAÇÃO COMPLETA

Execute este checklist para garantir que tudo está funcionando:

### ✅ Checklist de Verificação

```bash
cd /opt/sentinelweb

# 1. Containers estão rodando?
docker compose -f docker-compose.prod.yml ps
# Todos devem estar "Up" e "healthy"

# 2. Web container sem erros?
docker compose -f docker-compose.prod.yml logs --tail=100 web | grep -i error
# Não deve retornar erros de import

# 3. Endpoint /health responde?
curl http://localhost:8000/health
# Deve retornar JSON com "healthy"

# 4. HTTPS funciona?
curl -I https://seudominio.com.br
# Deve retornar HTTP/2 200

# 5. Admin panel carrega?
curl -I https://seudominio.com.br/admin
# Deve retornar HTTP/2 200 ou 302 (redirect para login)
```

---

## 🚨 TROUBLESHOOTING

### Problema: Git pull falha com "uncommitted changes"

```bash
cd /opt/sentinelweb

# Descartar mudanças locais no servidor
git reset --hard HEAD

# Puxar novamente
git pull origin main
```

### Problema: Container web continua crashando

```bash
# Ver logs completos
docker compose -f docker-compose.prod.yml logs web

# Rebuild completo sem cache
docker compose -f docker-compose.prod.yml build --no-cache

# Restart
docker compose -f docker-compose.prod.yml up -d
```

### Problema: 502 Bad Gateway

```bash
# Verificar se porta 8000 responde
curl http://localhost:8000/health

# Reiniciar Nginx
systemctl restart nginx

# Verificar logs do Nginx
tail -50 /var/log/nginx/error.log
```

### Problema: Admin panel não carrega (404)

```bash
# Verificar se admin.py está sendo importado
docker compose -f docker-compose.prod.yml exec web python -c "import admin; print('OK')"

# Se der erro, verificar main.py
docker compose -f docker-compose.prod.yml exec web grep "from admin import" main.py
```

---

## 📊 RESUMO DOS ARQUIVOS ALTERADOS

| Arquivo | Alteração | Status |
|---------|-----------|--------|
| `admin.py` linha 16 | Removido `import jwt` | ✅ Corrigido |
| `admin.py` linha 22 | `verify_token` → `decode_token` | ✅ Corrigido |
| `admin.py` linhas 28-119 | Async → Sync (SessionLocal) | ✅ Corrigido |

---

## 🎉 APÓS O DEPLOY BEM-SUCEDIDO

Você terá acesso ao **Painel Admin Enterprise** com:

### 📊 Dashboard Executivo
- **MRR (Monthly Recurring Revenue):** Receita mensal recorrente
- **ARPU (Average Revenue Per User):** Receita média por usuário
- **Churn Risk:** Usuários em risco de cancelamento
- **Operational Health:** Saúde operacional dos sistemas

### 👥 Gestão de Usuários (CRM)
- Lista completa com filtros por plano e status
- Badges visuais de status (ativo, trial, vencido)
- Busca por email e CPF/CNPJ
- Feature "impersonate user" (login como usuário)

### 🌐 Gestão de Sites (OPS)
- Status visual de uptime
- Informações de SSL/TLS
- Botão "Force Scan" para verificação manual
- Filtros por status e domínio

### 💰 Gestão de Pagamentos (ERP)
- Histórico completo de transações
- Integração com Asaas
- Filtros por status e data
- Formatação de valores em R$

### ⚙️ Configuração do Sistema
- Singleton de configuração global
- Mascaramento de API keys
- Edição de parâmetros críticos

---

## 📞 SUPORTE

Se após seguir todos os passos ainda houver problemas:

1. Verifique os logs: `docker compose -f docker-compose.prod.yml logs -f web`
2. Verifique o status: `docker compose -f docker-compose.prod.yml ps`
3. Teste localmente: `docker compose up` (sem -f prod)

---

**Versão:** 1.0.0  
**Data:** 09/01/2026  
**Autor:** SentinelWeb Team  
**Status:** ✅ Pronto para Deploy
