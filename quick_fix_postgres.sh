#!/bin/bash

# 🚀 CORREÇÃO RÁPIDA POSTGRESQL - SENTINELWEB
# Execute este script no servidor para corrigir o erro de autenticação

set -e

echo "🔧 Corrigindo erro de autenticação PostgreSQL..."
echo ""

# Ir para o diretório correto
cd /opt/sentinelweb || { echo "❌ Diretório /opt/sentinelweb não encontrado!"; exit 1; }

echo "📍 Diretório atual: $(pwd)"
echo ""

# 1. Parar containers
echo "⏸️  Parando containers..."
docker compose -f docker-compose.prod.yml down
echo "✅ Containers parados"
echo ""

# 2. Remover volume PostgreSQL
echo "🗑️  Removendo volume PostgreSQL antigo..."
docker volume rm sentinelweb_postgres_data 2>/dev/null || echo "Volume já foi removido"
echo "✅ Volume removido"
echo ""

# 3. Gerar nova senha
echo "🔐 Gerando nova senha forte..."
NEW_PASS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
echo "✅ Nova senha gerada: ${NEW_PASS:0:8}***"
echo ""

# 4. Atualizar .env
echo "📝 Atualizando arquivo .env..."
sed -i.backup "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env
sed -i.backup "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASS@db:5432/sentinelweb|" .env
echo "✅ Arquivo .env atualizado"
echo ""

# 5. Mostrar novas configurações
echo "🔍 Novas configurações:"
grep -E "^(POSTGRES_PASSWORD|DATABASE_URL)=" .env
echo ""

# 6. Recriar containers
echo "🚀 Recriando containers..."
docker compose -f docker-compose.prod.yml up -d
echo "✅ Containers iniciados"
echo ""

# 7. Aguardar PostgreSQL
echo "⏳ Aguardando PostgreSQL ficar pronto (30 segundos)..."
for i in {30..1}; do
    printf "\r   Aguardando... %02d segundos restantes" $i
    sleep 1
done
echo ""
echo "✅ Tempo de espera concluído"
echo ""

# 8. Verificar status
echo "📊 Status dos containers:"
docker compose -f docker-compose.prod.yml ps
echo ""

# 9. Testar conexão
echo "🔌 Testando conexão ao PostgreSQL..."
if docker compose -f docker-compose.prod.yml exec -T db psql -U sentinelweb -d sentinelweb -c "SELECT version();" > /dev/null 2>&1; then
    echo "✅ Conexão PostgreSQL OK!"
else
    echo "❌ Ainda há problemas. Verificando logs..."
    docker compose -f docker-compose.prod.yml logs --tail=20 db
    exit 1
fi
echo ""

# 10. Instruções finais
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ POSTGRESQL CORRIGIDO COM SUCESSO!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔐 Nova senha PostgreSQL: $NEW_PASS"
echo "⚠️  Guarde esta senha em local seguro!"
echo ""
echo "📋 Próximo passo - Criar superusuário:"
echo "   docker compose -f docker-compose.prod.yml exec web python create_superuser.py"
echo ""
echo "📄 Backup do .env anterior: .env.backup"
echo ""
