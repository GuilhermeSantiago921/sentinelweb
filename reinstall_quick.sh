#!/bin/bash
################################################################################
# SENTINELWEB - REINSTALAÇÃO RÁPIDA (CORRIGE PROBLEMA DE SENHA POSTGRESQL)
################################################################################
# Uso: sudo bash reinstall_quick.sh
#
# Este script:
# 1. Para todos os containers
# 2. Remove TODOS os volumes (APAGA DADOS!)
# 3. Gera nova senha PostgreSQL
# 4. Recria containers com senha correta
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

INSTALL_DIR="/opt/sentinelweb"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        SENTINELWEB - REINSTALAÇÃO RÁPIDA                    ║"
echo "║        ⚠️  ESTE SCRIPT APAGA TODOS OS DADOS!  ⚠️              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Execute como root: sudo bash reinstall_quick.sh${NC}"
    exit 1
fi

# Verificar diretório
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}Diretório $INSTALL_DIR não encontrado!${NC}"
    exit 1
fi

cd $INSTALL_DIR

echo ""
echo -e "${YELLOW}⚠️  ATENÇÃO: Este script irá:${NC}"
echo "   1. Parar todos os containers SentinelWeb"
echo "   2. REMOVER todos os volumes (PostgreSQL e Redis)"
echo "   3. APAGAR todos os dados do banco de dados"
echo "   4. Gerar nova senha PostgreSQL"
echo "   5. Recriar tudo do zero"
echo ""
echo -e "${RED}TODOS OS DADOS SERÃO PERDIDOS!${NC}"
echo ""

read -p "$(echo -e ${YELLOW}'Tem certeza que deseja continuar? (digite SIM para confirmar): '${NC})" CONFIRM

if [ "$CONFIRM" != "SIM" ]; then
    echo -e "${GREEN}Operação cancelada.${NC}"
    exit 0
fi

echo ""
echo -e "${CYAN}[1/7]${NC} Parando containers..."
docker compose -f docker-compose.prod.yml down 2>/dev/null || true

echo -e "${CYAN}[2/7]${NC} Removendo containers..."
docker ps -aq --filter "name=sentinelweb" | xargs -r docker rm -f 2>/dev/null || true

echo -e "${CYAN}[3/7]${NC} Removendo volumes..."
docker volume rm sentinelweb_postgres_data 2>/dev/null || true
docker volume rm sentinelweb_redis_data 2>/dev/null || true
docker volume ls -q | grep -i sentinelweb | xargs -r docker volume rm 2>/dev/null || true

echo -e "${CYAN}[4/7]${NC} Gerando nova senha PostgreSQL..."
NEW_POSTGRES_PASSWORD=$(openssl rand -hex 16)
NEW_REDIS_PASSWORD=$(openssl rand -hex 16)

# Atualizar .env
if [ -f ".env" ]; then
    # Backup do .env atual
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    
    # Atualizar senhas
    sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_POSTGRES_PASSWORD/" .env
    sed -i "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=$NEW_REDIS_PASSWORD/" .env
    sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_POSTGRES_PASSWORD@db:5432/sentinelweb|" .env
    sed -i "s|^REDIS_URL=.*|REDIS_URL=redis://:$NEW_REDIS_PASSWORD@redis:6379/0|" .env
    
    echo -e "${GREEN}   Nova POSTGRES_PASSWORD: $NEW_POSTGRES_PASSWORD${NC}"
fi

echo -e "${CYAN}[5/7]${NC} Reconstruindo imagens..."
docker compose -f docker-compose.prod.yml build --no-cache

echo -e "${CYAN}[6/7]${NC} Iniciando containers..."
docker compose -f docker-compose.prod.yml up -d

echo -e "${CYAN}[7/7]${NC} Aguardando PostgreSQL ficar pronto..."
sleep 15

MAX_WAIT=60
WAIT=0
while [ $WAIT -lt $MAX_WAIT ]; do
    if docker compose -f docker-compose.prod.yml exec -T db pg_isready -U sentinelweb > /dev/null 2>&1; then
        break
    fi
    echo -ne "\r   Aguardando... ${WAIT}s"
    sleep 3
    WAIT=$((WAIT + 3))
done
echo ""

# Testar conexão
if docker compose -f docker-compose.prod.yml exec -T db psql -U sentinelweb -d sentinelweb -c "SELECT 'OK';" 2>&1 | grep -q "OK"; then
    echo -e "${GREEN}✓ PostgreSQL conectado com sucesso!${NC}"
else
    echo -e "${RED}✗ Falha na conexão PostgreSQL${NC}"
    docker compose -f docker-compose.prod.yml logs --tail=20 db
    exit 1
fi

# Criar tabelas
echo ""
echo -e "${CYAN}Criando tabelas do banco...${NC}"
docker compose -f docker-compose.prod.yml exec -T web python -c "
from database import engine, Base
from models import User, Site, SiteCheck, MonitorLog, HeartbeatCheck, HeartbeatPing, SystemConfig, Payment
Base.metadata.create_all(bind=engine)
print('Tabelas criadas!')
" 2>/dev/null || echo "Aviso ao criar tabelas"

# Verificar status
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}     ✅ REINSTALAÇÃO CONCLUÍDA COM SUCESSO!          ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Nova POSTGRES_PASSWORD:${NC} $NEW_POSTGRES_PASSWORD"
echo -e "${YELLOW}Nova REDIS_PASSWORD:${NC}    $NEW_REDIS_PASSWORD"
echo ""
echo -e "${CYAN}Próximos passos:${NC}"
echo "   1. Criar superusuário:"
echo "      docker compose -f docker-compose.prod.yml exec web python create_superuser.py"
echo ""
echo "   2. Verificar status:"
echo "      docker compose -f docker-compose.prod.yml ps"
echo ""

# Perguntar se quer criar superusuário
read -p "$(echo -e ${YELLOW}'Deseja criar superusuário agora? (s/N): '${NC})" CREATE_USER
if [[ "$CREATE_USER" =~ ^[SsYy]$ ]]; then
    docker compose -f docker-compose.prod.yml exec web python create_superuser.py
fi

echo ""
echo -e "${GREEN}Pronto! 🚀${NC}"
