# 🔧 SOLUÇÃO: Erro de Autenticação PostgreSQL

## 📋 Erro Encontrado

```
❌ Erro ao criar superusuário: (psycopg2.OperationalError) 
connection to server at "db" (172.20.0.3), port 5432 failed: 
FATAL: password authentication failed for user "sentinelweb"
```

## 🔍 Causa do Problema

A senha do PostgreSQL configurada no arquivo `.env` **não corresponde** à senha que foi definida quando o banco de dados foi criado pela primeira vez. Isso pode acontecer por:

1. ✗ Senha foi alterada manualmente no `.env` mas o banco não foi recriado
2. ✗ Volume do Docker mantém configuração antiga
3. ✗ Variável `DATABASE_URL` está inconsistente com `POSTGRES_PASSWORD`

## 🎯 Soluções Disponíveis

### ✅ SOLUÇÃO 1: Diagnóstico Automático (Recomendado)

Execute no servidor para identificar o problema exato:

```bash
cd /opt/sentinelweb
bash diagnose_postgres.sh
```

Este script irá:
- ✓ Verificar arquivos de configuração
- ✓ Status dos containers
- ✓ Logs do PostgreSQL
- ✓ Testar conexão
- ✓ Comparar variáveis de ambiente
- ✓ Sugerir solução específica

---

### ✅ SOLUÇÃO 2: Correção Automática (Mais Rápida)

⚠️ **ATENÇÃO: Isso irá APAGAR todos os dados do banco!**

```bash
cd /opt/sentinelweb
bash fix_postgres_password.sh
```

Este script irá:
1. Fazer backup do `.env`
2. Parar containers
3. Remover volume PostgreSQL
4. Gerar nova senha forte
5. Atualizar `.env`
6. Recriar containers
7. Testar conexão

Depois execute:
```bash
docker compose -f docker-compose.prod.yml exec web python create_superuser.py
```

---

### ✅ SOLUÇÃO 3: Correção Manual Passo a Passo

Se preferir fazer manualmente:

#### Passo 1: Verificar configurações atuais
```bash
cd /opt/sentinelweb
cat .env | grep POSTGRES
```

#### Passo 2: Ver logs do banco
```bash
docker compose -f docker-compose.prod.yml logs db | tail -50
```

#### Passo 3: Parar containers
```bash
docker compose -f docker-compose.prod.yml down
```

#### Passo 4: Remover volume PostgreSQL
```bash
docker volume rm sentinelweb_postgres_data
```

#### Passo 5: Gerar nova senha
```bash
NEW_PASS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
echo "Nova senha: $NEW_PASS"
```

#### Passo 6: Atualizar .env
```bash
# Editar manualmente
nano .env

# Ou usar sed
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASS@db:5432/sentinelweb|" .env
```

#### Passo 7: Verificar se foi alterado
```bash
cat .env | grep POSTGRES
```

#### Passo 8: Recriar containers
```bash
docker compose -f docker-compose.prod.yml up -d
```

#### Passo 9: Aguardar PostgreSQL ficar pronto
```bash
sleep 30
docker compose -f docker-compose.prod.yml ps
```

#### Passo 10: Testar conexão
```bash
docker compose -f docker-compose.prod.yml exec db psql -U sentinelweb -d sentinelweb -c "SELECT version();"
```

Se der certo, você verá a versão do PostgreSQL!

#### Passo 11: Criar superusuário
```bash
docker compose -f docker-compose.prod.yml exec web python create_superuser.py
```

---

### ✅ SOLUÇÃO 4: Manter Dados (Avançado)

Se você **NÃO PODE PERDER OS DADOS**, tente sincronizar a senha:

#### Opção A: Descobrir a senha atual do banco
```bash
cd /opt/sentinelweb

# Tentar conectar sem senha (se permitido)
docker compose -f docker-compose.prod.yml exec db psql -U postgres -c "\du"

# Ou verificar logs da primeira inicialização
docker compose -f docker-compose.prod.yml logs db | grep -i password
```

#### Opção B: Alterar senha no PostgreSQL
```bash
# Conectar como postgres (superusuário)
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d sentinelweb

# Dentro do PostgreSQL:
ALTER USER sentinelweb WITH PASSWORD 'NOVA_SENHA_AQUI';
\q

# Atualizar .env com a mesma senha
nano .env
```

---

## 📊 Verificação Pós-Correção

### 1. Status dos Containers
```bash
cd /opt/sentinelweb
docker compose -f docker-compose.prod.yml ps
```

Todos devem estar **Up** e **healthy**.

### 2. Teste de Conexão
```bash
docker compose -f docker-compose.prod.yml exec db psql -U sentinelweb -d sentinelweb -c "\dt"
```

Deve listar as tabelas (ou vazio se banco novo).

### 3. Health Check da Aplicação
```bash
curl http://localhost:8000/health
```

Deve retornar status `healthy`.

### 4. Logs da Aplicação
```bash
docker compose -f docker-compose.prod.yml logs -f web
```

Não deve haver erros de conexão ao banco.

---

## 🚨 Prevenção Futura

### ✓ Sempre manter .env sincronizado
```bash
# Ao mudar POSTGRES_PASSWORD, também mude DATABASE_URL
# Exemplo:
POSTGRES_PASSWORD=nova_senha_aqui
DATABASE_URL=postgresql://sentinelweb:nova_senha_aqui@db:5432/sentinelweb
```

### ✓ Fazer backup antes de mudanças
```bash
cp .env .env.backup
```

### ✓ Não mudar senha sem recriar volume
Se mudar a senha no `.env`, você DEVE recriar o volume PostgreSQL:
```bash
docker compose -f docker-compose.prod.yml down -v
docker compose -f docker-compose.prod.yml up -d
```

### ✓ Usar secrets manager em produção
Para produção real, considere usar:
- Docker secrets
- Vault do HashiCorp
- AWS Secrets Manager
- Azure Key Vault

---

## 📞 Scripts Disponíveis

| Script | Descrição | Uso |
|--------|-----------|-----|
| `diagnose_postgres.sh` | Identifica o problema | `bash diagnose_postgres.sh` |
| `fix_postgres_password.sh` | Corrige automaticamente | `bash fix_postgres_password.sh` |

---

## 🎯 Resumo Rápido

**Para resolver AGORA:**

```bash
# No servidor via SSH:
cd /opt/sentinelweb

# Opção 1: Diagnóstico primeiro
bash diagnose_postgres.sh

# Opção 2: Correção direta (APAGA DADOS!)
bash fix_postgres_password.sh

# Depois criar superusuário
docker compose -f docker-compose.prod.yml exec web python create_superuser.py
```

---

**Atualizado:** 09/01/2026  
**Status:** Testado e funcional ✅
