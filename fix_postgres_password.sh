#!/bin/bash

# 🔧 FIX POSTGRESQL PASSWORD - SENTINELWEB
# Script para corrigir problemas de senha do PostgreSQL

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 FIX POSTGRESQL PASSWORD - SENTINELWEB${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Verificar se está no diretório correto
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ Erro: docker-compose.prod.yml não encontrado!${NC}"
    echo "Execute este script no diretório /opt/sentinelweb"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Erro: arquivo .env não encontrado!${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  ATENÇÃO: Este script irá:${NC}"
echo "   1. Parar todos os containers"
echo "   2. Remover o volume do PostgreSQL (TODOS OS DADOS SERÃO PERDIDOS!)"
echo "   3. Gerar uma nova senha forte"
echo "   4. Atualizar o arquivo .env"
echo "   5. Recriar os containers"
echo "   6. Criar as tabelas do banco"
echo ""
echo -e "${RED}⚠️  TODOS OS DADOS DO BANCO SERÃO PERDIDOS!${NC}"
echo ""
read -p "Deseja continuar? (digite 'SIM' em maiúsculas): " confirm

if [ "$confirm" != "SIM" ]; then
    echo -e "${YELLOW}❌ Operação cancelada pelo usuário.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}[PASSO 1/8] Fazendo backup do .env atual${NC}"
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo -e "${GREEN}✓ Backup criado${NC}"
echo ""

echo -e "${BLUE}[PASSO 2/8] Parando containers${NC}"
docker compose -f docker-compose.prod.yml down
echo -e "${GREEN}✓ Containers parados${NC}"
echo ""

echo -e "${BLUE}[PASSO 3/8] Removendo volume PostgreSQL${NC}"
docker volume rm sentinelweb_postgres_data 2>/dev/null || echo "Volume não existia"
echo -e "${GREEN}✓ Volume removido${NC}"
echo ""

echo -e "${BLUE}[PASSO 4/8] Gerando nova senha forte${NC}"
NEW_PASSWORD=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
echo -e "${GREEN}✓ Nova senha gerada: ${NEW_PASSWORD:0:8}...${NC}"
echo ""

echo -e "${BLUE}[PASSO 5/8] Atualizando arquivo .env${NC}"
# Atualizar POSTGRES_PASSWORD
sed -i.bak "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$NEW_PASSWORD|" .env

# Atualizar DATABASE_URL
sed -i.bak "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASSWORD@db:5432/sentinelweb|" .env

echo "Novas configurações:"
grep -E "^(POSTGRES_PASSWORD|DATABASE_URL)=" .env
echo -e "${GREEN}✓ Arquivo .env atualizado${NC}"
echo ""

echo -e "${BLUE}[PASSO 6/8] Recriando containers${NC}"
docker compose -f docker-compose.prod.yml up -d
echo -e "${GREEN}✓ Containers iniciados${NC}"
echo ""

echo -e "${BLUE}[PASSO 7/8] Aguardando PostgreSQL ficar pronto (30 segundos)${NC}"
for i in {30..1}; do
    echo -ne "\rAguardando... $i segundos restantes "
    sleep 1
done
echo ""
echo -e "${GREEN}✓ Aguardou tempo necessário${NC}"
echo ""

echo -e "${BLUE}[PASSO 8/8] Testando conexão${NC}"
if docker compose -f docker-compose.prod.yml exec -T db psql -U sentinelweb -d sentinelweb -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Conexão PostgreSQL funcionando!${NC}"
else
    echo -e "${RED}❌ Ainda há problemas de conexão. Verifique os logs:${NC}"
    echo "   docker compose -f docker-compose.prod.yml logs db"
    exit 1
fi
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ POSTGRESQL CORRIGIDO COM SUCESSO!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📝 Próximos passos:${NC}"
echo ""
echo "1️⃣ Criar superusuário:"
echo "   docker compose -f docker-compose.prod.yml exec web python create_superuser.py"
echo ""
echo "2️⃣ Verificar status:"
echo "   docker compose -f docker-compose.prod.yml ps"
echo ""
echo "3️⃣ Ver logs:"
echo "   docker compose -f docker-compose.prod.yml logs -f web"
echo ""
echo -e "${YELLOW}🔐 Nova senha PostgreSQL:${NC} $NEW_PASSWORD"
echo -e "${YELLOW}⚠️  Guarde esta senha em local seguro!${NC}"
echo ""
echo "Backup do .env anterior salvo em: .env.backup.*"
echo ""
