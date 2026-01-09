#!/bin/bash

# 🔍 DIAGNÓSTICO POSTGRESQL - SENTINELWEB
# Script para identificar problemas de autenticação PostgreSQL

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 DIAGNÓSTICO POSTGRESQL - SENTINELWEB"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar se está no diretório correto
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Erro: docker-compose.prod.yml não encontrado!"
    echo "Execute este script no diretório /opt/sentinelweb"
    exit 1
fi

echo "📋 PASSO 1: Verificando arquivos de configuração"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f ".env" ]; then
    echo "✅ Arquivo .env encontrado"
    echo ""
    echo "Credenciais PostgreSQL no .env:"
    grep -E "^(POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB|DATABASE_URL)=" .env || echo "⚠️ Variáveis não encontradas!"
else
    echo "❌ Arquivo .env NÃO encontrado!"
    exit 1
fi
echo ""

echo "📋 PASSO 2: Status dos containers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose -f docker-compose.prod.yml ps
echo ""

echo "📋 PASSO 3: Logs do container PostgreSQL (últimas 30 linhas)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose -f docker-compose.prod.yml logs --tail=30 db
echo ""

echo "📋 PASSO 4: Testando conexão ao PostgreSQL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Extrair credenciais do .env
DB_USER=$(grep "^POSTGRES_USER=" .env | cut -d '=' -f2)
DB_PASS=$(grep "^POSTGRES_PASSWORD=" .env | cut -d '=' -f2)
DB_NAME=$(grep "^POSTGRES_DB=" .env | cut -d '=' -f2)

echo "Testando conexão com:"
echo "  Usuário: $DB_USER"
echo "  Senha: ${DB_PASS:0:5}... (oculta)"
echo "  Database: $DB_NAME"
echo ""

# Teste de conexão
if docker compose -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
    echo "✅ Conexão PostgreSQL OK!"
    echo ""
    echo "Versão do PostgreSQL:"
    docker compose -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();"
    echo ""
    echo "Listando tabelas existentes:"
    docker compose -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c "\dt"
else
    echo "❌ Falha na conexão PostgreSQL!"
    echo ""
    echo "Isso confirma que a senha está incorreta ou há problema de configuração."
fi
echo ""

echo "📋 PASSO 5: Verificando variáveis de ambiente no container web"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose -f docker-compose.prod.yml exec -T web env | grep -E "(DATABASE_URL|POSTGRES)" || echo "⚠️ Variáveis não encontradas no container!"
echo ""

echo "📋 PASSO 6: Comparando DATABASE_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "No arquivo .env:"
grep "^DATABASE_URL=" .env
echo ""
echo "No container web:"
docker compose -f docker-compose.prod.yml exec -T web env | grep "^DATABASE_URL=" || echo "⚠️ DATABASE_URL não definida no container!"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 RESUMO DO DIAGNÓSTICO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificações finais
CONTAINER_RUNNING=$(docker compose -f docker-compose.prod.yml ps db --format json | jq -r '.[0].State' 2>/dev/null || echo "unknown")
ENV_EXISTS=$([ -f ".env" ] && echo "sim" || echo "não")

echo "✓ Container DB rodando: $CONTAINER_RUNNING"
echo "✓ Arquivo .env existe: $ENV_EXISTS"
echo ""

echo "🔧 SOLUÇÕES RECOMENDADAS:"
echo ""
echo "1️⃣ Se a senha está INCORRETA:"
echo "   bash fix_postgres_password.sh"
echo ""
echo "2️⃣ Se quer RESETAR completamente o banco:"
echo "   docker compose -f docker-compose.prod.yml down -v"
echo "   docker compose -f docker-compose.prod.yml up -d"
echo ""
echo "3️⃣ Se containers não estão rodando:"
echo "   docker compose -f docker-compose.prod.yml restart"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Diagnóstico completo!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
