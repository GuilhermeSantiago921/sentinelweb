#!/bin/bash
################################################################################
# SENTINELWEB - SCRIPT DE CORREÇÃO RÁPIDA
################################################################################
# Corrige problemas comuns de instalação
# Uso: sudo bash fix.sh
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  SENTINELWEB - CORREÇÃO RÁPIDA${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd /opt/sentinelweb

echo -e "${YELLOW}[1/5]${NC} Parando containers..."
sg docker -c "sudo -u sentinelweb docker compose -f docker-compose.prod.yml down -v"

echo -e "${YELLOW}[2/5]${NC} Limpando volumes antigos..."
docker volume prune -f

echo -e "${YELLOW}[3/5]${NC} Puxando código atualizado do GitHub..."
# Remover arquivos que podem causar conflito
rm -f fix.sh TROUBLESHOOTING.md
# Resetar mudanças locais e puxar
sudo -u sentinelweb git reset --hard HEAD
sudo -u sentinelweb git pull origin main

echo -e "${YELLOW}[4/5]${NC} Reconstruindo e iniciando containers..."
sg docker -c "sudo -u sentinelweb docker compose -f docker-compose.prod.yml up -d --build"

echo -e "${YELLOW}[5/5]${NC} Aguardando containers ficarem prontos (60s)..."
sleep 60

echo ""
echo -e "${GREEN}✓ Correção concluída!${NC}"
echo ""
echo -e "${BLUE}Status dos containers:${NC}"
sg docker -c "sudo -u sentinelweb docker compose -f docker-compose.prod.yml ps"

echo ""
echo -e "${YELLOW}Agora tente criar as tabelas:${NC}"
echo ""
echo -e "sg docker -c 'sudo -u sentinelweb docker compose -f docker-compose.prod.yml exec web python -c \""
echo -e "from database import engine, Base"
echo -e "from models import User, Site, MonitorLog, HeartbeatCheck, SystemConfig, Payment"
echo -e "Base.metadata.create_all(bind=engine)"
echo -e "print('Tabelas criadas!')"
echo -e "\"'"
echo ""
