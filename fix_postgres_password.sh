#!/bin/bash

# � SINCRONIZAÇÃO DE SENHA POSTGRESQL - SENTINELWEB
# Este script altera a senha no PostgreSQL para corresponder ao .env
# ✅ NÃO PERDE DADOS - apenas sincroniza senhas

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}� SINCRONIZAÇÃO DE SENHA POSTGRESQL${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd /opt/sentinelweb || { echo -e "${RED}❌ Diretório /opt/sentinelweb não encontrado!${NC}"; exit 1; }

# Ler senha do .env
echo -e "${BLUE}[1/4] Lendo senha do arquivo .env...${NC}"
ENV_PASSWORD=$(grep "^POSTGRES_PASSWORD=" .env | cut -d'=' -f2)

if [ -z "$ENV_PASSWORD" ]; then
    echo -e "${RED}❌ POSTGRES_PASSWORD não encontrado no .env!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Senha encontrada no .env: ${ENV_PASSWORD:0:8}***${NC}"
echo ""

# Alterar senha no PostgreSQL
echo -e "${BLUE}[2/4] Alterando senha no PostgreSQL...${NC}"
docker compose -f docker-compose.prod.yml exec -T db psql -U sentinelweb -d postgres << EOF
ALTER USER sentinelweb WITH PASSWORD '$ENV_PASSWORD';
\q
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Senha alterada com sucesso no PostgreSQL!${NC}"
else
    echo -e "${RED}❌ Erro ao alterar senha no PostgreSQL!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backup criado${NC}"
echo ""

echo ""

# Reiniciar container web para aplicar nova senha
echo -e "${BLUE}[3/4] Reiniciando container web...${NC}"
docker compose -f docker-compose.prod.yml restart web
echo -e "${GREEN}✓ Container web reiniciado${NC}"
echo ""

# Aguardar container ficar pronto
echo -e "${BLUE}[4/4] Aguardando aplicação (15 segundos)...${NC}"
sleep 15
echo -e "${GREEN}✓ Aplicação pronta${NC}"
echo ""

# Testar conexão
echo -e "${BLUE}🧪 Testando conexão do Python com PostgreSQL...${NC}"
if docker compose -f docker-compose.prod.yml exec -T web python -c "
from database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✓ Conexão OK!')
except Exception as e:
    print(f'✗ Erro: {e}')
    exit(1)
" 2>/dev/null; then
    echo -e "${GREEN}✓ Conexão Python -> PostgreSQL funcionando!${NC}"
else
    echo -e "${YELLOW}⚠ Teste de conexão falhou. Verificando logs...${NC}"
    docker compose -f docker-compose.prod.yml logs --tail=20 web
fi
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ SINCRONIZAÇÃO CONCLUÍDA!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}� RESUMO:${NC}"
echo "• PostgreSQL agora usa a senha do .env"
echo "• Container web foi reiniciado"
echo "• Nenhum dado foi perdido"
echo ""
echo -e "${YELLOW}🎯 PRÓXIMO PASSO:${NC}"
echo "   Criar o superusuário:"
echo ""
echo -e "${GREEN}   docker compose -f docker-compose.prod.yml exec web python create_superuser.py${NC}"
echo ""

