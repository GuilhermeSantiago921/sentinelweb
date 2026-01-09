# 🚀 COMANDOS PARA EXECUTAR NO SERVIDOR SSH

---

## 🚨 CORRIGIR ERRO 502 BAD GATEWAY

### ⚡ SOLUÇÃO MAIS RÁPIDA - Copie e cole tudo de uma vez:

```bash
cd /opt/sentinelweb && \
docker compose -f docker-compose.prod.yml down -v && \
docker volume rm sentinelweb_postgres_data 2>/dev/null || true && \
NEW_PASS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32) && \
echo "🔐 Nova senha PostgreSQL: $NEW_PASS" && \
sed -i.bak502 "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env && \
sed -i.bak502 "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASS@db:5432/sentinelweb|" .env && \
echo "📝 .env atualizado" && \
docker compose -f docker-compose.prod.yml up -d && \
echo "⏳ Aguardando 40 segundos..." && \
sleep 40 && \
echo "📊 Status dos containers:" && \
docker compose -f docker-compose.prod.yml ps && \
echo "" && \
echo "🧪 Testando aplicação:" && \
curl -s http://localhost:8000/health | jq . 2>/dev/null || curl http://localhost:8000/health && \
echo "" && \
echo "🔄 Reiniciando Nginx..." && \
systemctl restart nginx && \
sleep 2 && \
echo "" && \
echo "✅ CORREÇÃO CONCLUÍDA!" && \
echo "" && \
echo "📋 Próximo passo - Criar superusuário:" && \
echo "   docker compose -f docker-compose.prod.yml exec web python create_superuser.py"
```

---

## 🔧 CORRIGIR ERRO DE AUTENTICAÇÃO POSTGRESQL

### ⚡ SOLUÇÃO MAIS RÁPIDA - Copie e cole tudo de uma vez:

```bash
cd /opt/sentinelweb && \
docker compose -f docker-compose.prod.yml down && \
docker volume rm sentinelweb_postgres_data 2>/dev/null || true && \
NEW_PASS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32) && \
echo "Nova senha PostgreSQL: $NEW_PASS" && \
sed -i.backup "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env && \
sed -i.backup "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASS@db:5432/sentinelweb|" .env && \
echo "Verificando .env:" && \
grep -E "^(POSTGRES_PASSWORD|DATABASE_URL)=" .env && \
docker compose -f docker-compose.prod.yml up -d && \
echo "Aguardando 30 segundos..." && \
sleep 30 && \
echo "Status dos containers:" && \
docker compose -f docker-compose.prod.yml ps && \
echo "Testando conexão..." && \
docker compose -f docker-compose.prod.yml exec -T db psql -U sentinelweb -d sentinelweb -c "SELECT 1;" && \
echo "✅ SUCESSO! Agora execute: docker compose -f docker-compose.prod.yml exec web python create_superuser.py"
```

---

## 📋 OU execute passo a passo (ERRO 502):

### Passo 1: Ir para o diretório
```bash
cd /opt/sentinelweb
```

### Passo 2: Diagnosticar
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=50 web
curl http://localhost:8000/health
```

### Passo 3: Parar containers
```bash
docker compose -f docker-compose.prod.yml down -v
```

### Passo 4: Remover volume PostgreSQL
```bash
docker volume rm sentinelweb_postgres_data
```

### Passo 5: Gerar nova senha
```bash
NEW_PASS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
echo "Nova senha: $NEW_PASS"
```

### Passo 6: Atualizar .env
```bash
sed -i.backup "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env
sed -i.backup "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASS@db:5432/sentinelweb|" .env
```

### Passo 7: Verificar mudanças
```bash
cat .env | grep POSTGRES
```

### Passo 8: Recriar containers
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Passo 9: Aguardar 40 segundos
```bash
sleep 40
```

### Passo 10: Verificar status
```bash
docker compose -f docker-compose.prod.yml ps
```

### Passo 11: Testar aplicação
```bash
curl http://localhost:8000/health
```

### Passo 12: Reiniciar Nginx
```bash
systemctl restart nginx
```

### Passo 13: Testar HTTPS
```bash
curl -I https://seudominio.com.br
```

### Passo 14: Criar superusuário
```bash
docker compose -f docker-compose.prod.yml exec web python create_superuser.py
```

---

## 🎯 RECOMENDAÇÃO

Use a **SOLUÇÃO MAIS RÁPIDA** para o erro que você está enfrentando:

- **502 Bad Gateway** → Use o primeiro comando (Corrigir erro 502)
- **Erro de autenticação PostgreSQL** → Use o segundo comando

Ambos executam tudo automaticamente!

---

## ✅ Após executar com sucesso

Você deverá ver:
- ✅ Containers recriados
- ✅ PostgreSQL rodando
- ✅ Aplicação respondendo na porta 8000
- ✅ Nginx funcionando
- ✅ Pronto para criar superusuário

Então execute:
```bash
docker compose -f docker-compose.prod.yml exec web python create_superuser.py
```

E forneça:
- Nome completo: Seu Nome
- Email: guilhermesantiago921@gmail.com
- Senha: (escolha uma senha forte)

---

## 🔍 DIAGNÓSTICO ADICIONAL

Se ainda houver problemas:

```bash
# Ver logs detalhados
docker compose -f docker-compose.prod.yml logs web

# Ver logs do Nginx
tail -50 /var/log/nginx/error.log

# Verificar processos dentro do container
docker compose -f docker-compose.prod.yml exec web ps aux

# Testar conexão ao banco
docker compose -f docker-compose.prod.yml exec web python -c "from database import engine; engine.connect(); print('OK')"
```

---

## 📚 Documentação Completa

- `FIX_502_ERROR.md` - Solução completa para erro 502
- `POSTGRES_FIX_GUIDE.md` - Solução para erros PostgreSQL
- `INSTALL_GUIDE.md` - Guia completo de instalação

