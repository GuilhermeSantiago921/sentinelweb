# 🚨 SOLUÇÃO: 502 Bad Gateway - SENTINELWEB

## 📋 Diagnóstico do Erro 502

O erro **502 Bad Gateway** significa que o Nginx não consegue se comunicar com a aplicação FastAPI.

---

## 🔍 DIAGNÓSTICO RÁPIDO - Execute no servidor:

```bash
cd /opt/sentinelweb && \
echo "=== STATUS DOS CONTAINERS ===" && \
docker compose -f docker-compose.prod.yml ps && \
echo "" && \
echo "=== LOGS DO CONTAINER WEB (últimas 50 linhas) ===" && \
docker compose -f docker-compose.prod.yml logs --tail=50 web && \
echo "" && \
echo "=== LOGS DO NGINX (últimas 20 linhas) ===" && \
tail -20 /var/log/nginx/error.log && \
echo "" && \
echo "=== TESTANDO PORTA 8000 ===" && \
curl -I http://localhost:8000/health 2>&1 || echo "Porta 8000 não responde!" && \
echo "" && \
echo "=== VERIFICANDO PROCESSOS ===" && \
docker compose -f docker-compose.prod.yml exec web ps aux | grep -E "(python|uvicorn)" || echo "Nenhum processo encontrado"
```

---

## ⚡ CORREÇÃO RÁPIDA - Execute tudo de uma vez:

```bash
cd /opt/sentinelweb && \
echo "Parando containers..." && \
docker compose -f docker-compose.prod.yml down && \
echo "Removendo volumes antigos..." && \
docker volume rm sentinelweb_postgres_data 2>/dev/null || true && \
echo "Gerando nova senha PostgreSQL..." && \
NEW_PASS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32) && \
echo "Nova senha: $NEW_PASS" && \
sed -i.backup "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env && \
sed -i.backup "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASS@db:5432/sentinelweb|" .env && \
echo "Recriando containers..." && \
docker compose -f docker-compose.prod.yml up -d && \
echo "Aguardando 40 segundos..." && \
sleep 40 && \
echo "" && \
echo "=== STATUS DOS CONTAINERS ===" && \
docker compose -f docker-compose.prod.yml ps && \
echo "" && \
echo "=== TESTANDO APLICAÇÃO ===" && \
curl -s http://localhost:8000/health | jq . || curl http://localhost:8000/health && \
echo "" && \
echo "✅ Aplicação rodando! Teste no navegador agora."
```

---

## 📝 PASSO A PASSO (se preferir executar manualmente):

### 1. Verificar status dos containers
```bash
cd /opt/sentinelweb
docker compose -f docker-compose.prod.yml ps
```

**Esperado:** Todos os containers devem estar **Up** e **healthy**.

### 2. Ver logs do container web
```bash
docker compose -f docker-compose.prod.yml logs --tail=100 web
```

**Procure por:**
- ❌ Erros de conexão ao banco
- ❌ Erros de importação Python
- ❌ Porta já em uso
- ❌ Timeout

### 3. Verificar se a porta 8000 responde
```bash
curl http://localhost:8000/health
```

**Esperado:**
```json
{"status": "healthy", "database": "connected", "redis": "connected"}
```

### 4. Se não responder, reiniciar o container web
```bash
docker compose -f docker-compose.prod.yml restart web
sleep 10
curl http://localhost:8000/health
```

### 5. Se ainda não funcionar, rebuild completo
```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build
sleep 30
docker compose -f docker-compose.prod.yml logs -f web
```

### 6. Verificar logs do Nginx
```bash
tail -50 /var/log/nginx/error.log
```

**Procure por:**
- `connect() failed (111: Connection refused)`
- `upstream timed out`
- `no live upstreams`

### 7. Testar configuração do Nginx
```bash
nginx -t
```

**Esperado:** `syntax is ok` e `test is successful`

### 8. Reiniciar Nginx
```bash
systemctl restart nginx
systemctl status nginx
```

---

## 🔧 SOLUÇÕES ESPECÍFICAS

### Problema: Container web não inicia

**Causa:** Erro de banco de dados ou dependências

**Solução:**
```bash
cd /opt/sentinelweb

# Ver erro completo
docker compose -f docker-compose.prod.yml logs web

# Se for erro de banco, executar correção do PostgreSQL
docker compose -f docker-compose.prod.yml down -v
NEW_PASS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASS@db:5432/sentinelweb|" .env
docker compose -f docker-compose.prod.yml up -d
sleep 30
```

### Problema: Container web para logo após iniciar

**Causa:** Erro na aplicação

**Solução:**
```bash
# Ver logs detalhados
docker compose -f docker-compose.prod.yml logs --tail=200 web

# Entrar no container para debug
docker compose -f docker-compose.prod.yml exec web bash
# Dentro do container:
python -c "from database import engine; print(engine)"
exit

# Se houver erro de importação, rebuild
docker compose -f docker-compose.prod.yml build --no-cache web
docker compose -f docker-compose.prod.yml up -d
```

### Problema: Porta 8000 não responde

**Causa:** Container não está expondo a porta

**Solução:**
```bash
# Verificar se porta está em uso
netstat -tulpn | grep 8000

# Verificar mapeamento de portas
docker compose -f docker-compose.prod.yml ps

# Se necessário, parar tudo e reiniciar
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Problema: Nginx não encontra upstream

**Causa:** Nginx tentando conectar antes do container estar pronto

**Solução:**
```bash
# Aguardar containers ficarem prontos
sleep 30

# Reiniciar Nginx
systemctl restart nginx

# Testar
curl -I https://seudominio.com.br
```

### Problema: Timeout ao conectar

**Causa:** Healthcheck falhando ou aplicação muito lenta

**Solução:**
```bash
cd /opt/sentinelweb

# Aumentar timeout no docker-compose.prod.yml
nano docker-compose.prod.yml

# Procure por 'healthcheck' e ajuste:
# timeout: 10s
# retries: 5
# start_period: 60s

# Depois:
docker compose -f docker-compose.prod.yml up -d
```

---

## 🔍 CHECKLIST DE VERIFICAÇÃO

Execute item por item:

```bash
cd /opt/sentinelweb

# ✓ 1. Containers rodando?
docker compose -f docker-compose.prod.yml ps

# ✓ 2. Container web saudável?
docker compose -f docker-compose.prod.yml ps web | grep healthy

# ✓ 3. Porta 8000 responde?
curl -s http://localhost:8000/health | jq .

# ✓ 4. Banco conectado?
docker compose -f docker-compose.prod.yml exec web python -c "from database import engine; engine.connect(); print('OK')"

# ✓ 5. Redis conectado?
docker compose -f docker-compose.prod.yml exec redis redis-cli ping

# ✓ 6. Nginx rodando?
systemctl status nginx | grep active

# ✓ 7. Nginx pode acessar upstream?
nginx -t

# ✓ 8. Firewall permite portas?
ufw status | grep -E "(80|443|8000)"
```

Se TODOS os itens acima estiverem OK, o erro 502 deve sumir!

---

## 🚀 RESET COMPLETO (Última opção)

Se nada funcionar, reset total:

```bash
cd /opt/sentinelweb

# 1. Parar tudo
docker compose -f docker-compose.prod.yml down -v

# 2. Limpar containers órfãos
docker container prune -f

# 3. Limpar volumes não usados
docker volume prune -f

# 4. Remover volume específico
docker volume rm sentinelweb_postgres_data 2>/dev/null || true

# 5. Atualizar senhas no .env
NEW_PASS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASS@db:5432/sentinelweb|" .env

# 6. Rebuild completo
docker compose -f docker-compose.prod.yml build --no-cache

# 7. Subir aplicação
docker compose -f docker-compose.prod.yml up -d

# 8. Aguardar 60 segundos
echo "Aguardando 60 segundos..."
for i in {60..1}; do
    printf "\r%02d segundos restantes..." $i
    sleep 1
done
echo ""

# 9. Verificar status
docker compose -f docker-compose.prod.yml ps

# 10. Ver logs
docker compose -f docker-compose.prod.yml logs --tail=50 web

# 11. Testar
curl http://localhost:8000/health

# 12. Reiniciar Nginx
systemctl restart nginx

# 13. Testar HTTPS
curl -I https://seudominio.com.br
```

---

## 📊 APÓS CORREÇÃO

### Criar superusuário:
```bash
docker compose -f docker-compose.prod.yml exec web python create_superuser.py
```

### Monitorar logs em tempo real:
```bash
docker compose -f docker-compose.prod.yml logs -f web
```

### Verificar saúde contínua:
```bash
watch -n 2 'curl -s http://localhost:8000/health | jq .'
```

---

## 🎯 RESUMO DAS CAUSAS COMUNS

| Erro | Causa | Solução |
|------|-------|---------|
| Container web não inicia | Erro de banco | Resetar PostgreSQL |
| Container para logo após start | Erro na aplicação | Ver logs detalhados |
| Porta 8000 não responde | Porta não exposta | Verificar docker-compose.yml |
| Nginx connection refused | Container não pronto | Aguardar + reiniciar Nginx |
| Timeout | Healthcheck falhando | Aumentar timeout |

---

**Execute o DIAGNÓSTICO RÁPIDO primeiro para identificar o problema exato!**
