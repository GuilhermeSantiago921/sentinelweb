#!/bin/bash

# 🔧 CORREÇÃO AUTOMÁTICA 502 BAD GATEWAY - SENTINELWEB
# Execute este script para corrigir o erro 502

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 CORREÇÃO AUTOMÁTICA 502 BAD GATEWAY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd /opt/sentinelweb || { echo -e "${RED}❌ Diretório /opt/sentinelweb não encontrado!${NC}"; exit 1; }

echo -e "${BLUE}[1/10] Diagnosticando problema...${NC}"
echo "Status atual dos containers:"
docker compose -f docker-compose.prod.yml ps
echo ""

echo -e "${BLUE}[2/10] Parando containers...${NC}"
docker compose -f docker-compose.prod.yml down
echo -e "${GREEN}✓ Containers parados${NC}"
echo ""

echo -e "${BLUE}[3/10] Removendo volumes antigos...${NC}"
docker volume rm sentinelweb_postgres_data 2>/dev/null || echo "Volume já removido"
echo -e "${GREEN}✓ Volumes limpos${NC}"
echo ""

echo -e "${BLUE}[4/10] Gerando nova senha PostgreSQL...${NC}"
NEW_PASS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
echo -e "${GREEN}✓ Nova senha gerada: ${NEW_PASS:0:8}***${NC}"
echo ""

echo -e "${BLUE}[5/10] Atualizando .env...${NC}"
sed -i.bak502 "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env
sed -i.bak502 "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASS@db:5432/sentinelweb|" .env
echo -e "${GREEN}✓ Arquivo .env atualizado${NC}"
echo ""

echo -e "${BLUE}[6/10] Recriando containers...${NC}"
docker compose -f docker-compose.prod.yml up -d
echo -e "${GREEN}✓ Containers iniciados${NC}"
echo ""

echo -e "${BLUE}[7/10] Aguardando aplicação ficar pronta (40 segundos)...${NC}"
for i in {40..1}; do
    printf "\r   Aguardando... %02d segundos restantes" $i
    sleep 1
done
echo ""
echo -e "${GREEN}✓ Tempo de espera concluído${NC}"
echo ""

echo -e "${BLUE}[8/10] Verificando status dos containers...${NC}"
docker compose -f docker-compose.prod.yml ps
echo ""

echo -e "${BLUE}[9/10] Testando aplicação na porta 8000...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Aplicação respondendo na porta 8000!${NC}"
    curl -s http://localhost:8000/health | jq . || curl http://localhost:8000/health
else
    echo -e "${YELLOW}⚠ Aplicação ainda não está respondendo...${NC}"
    echo "Logs do container web:"
    docker compose -f docker-compose.prod.yml logs --tail=30 web
fi
echo ""

echo -e "${BLUE}[10/10] Reiniciando Nginx...${NC}"
systemctl restart nginx
sleep 2
echo -e "${GREEN}✓ Nginx reiniciado${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ CORREÇÃO CONCLUÍDA!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📊 RESUMO:${NC}"
echo "• Nova senha PostgreSQL: $NEW_PASS"
echo "• Backup do .env anterior: .env.bak502"
echo ""
echo -e "${YELLOW}🧪 TESTES:${NC}"
echo ""
echo "1️⃣ Testar localmente:"
echo "   curl http://localhost:8000/health"
echo ""
echo "2️⃣ Testar via domínio:"
echo "   curl -I https://seudominio.com.br"
echo ""
echo "3️⃣ Ver logs em tempo real:"
echo "   docker compose -f docker-compose.prod.yml logs -f web"
echo ""
echo "4️⃣ Criar superusuário:"
echo "   docker compose -f docker-compose.prod.yml exec web python create_superuser.py"
echo ""
echo -e "${YELLOW}🔍 Se ainda houver erro 502:${NC}"
echo "   docker compose -f docker-compose.prod.yml logs web"
echo "   tail -50 /var/log/nginx/error.log"
echo ""
