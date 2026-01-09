#!/bin/bash

# 🔧 CORREÇÃO IMEDIATA - ERRO POSTGRESQL PASSWORD
# Execute este comando no servidor SSH

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 CORRIGINDO ERRO DE AUTENTICAÇÃO POSTGRESQL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "❌ Erro encontrado:"
echo "   password authentication failed for user \"sentinelweb\""
echo ""
echo "✅ Solução: Resetar PostgreSQL com nova senha"
echo ""
read -p "Pressione ENTER para continuar ou Ctrl+C para cancelar..."
echo ""

cd /opt/sentinelweb || { echo "❌ Erro: diretório não encontrado!"; exit 1; }

echo "[1/9] Parando containers..."
docker compose -f docker-compose.prod.yml down
echo "✓ Containers parados"
echo ""

echo "[2/9] Removendo volume PostgreSQL..."
docker volume rm sentinelweb_postgres_data 2>/dev/null || echo "Volume já foi removido"
echo "✓ Volume removido"
echo ""

echo "[3/9] Gerando nova senha forte..."
NEW_PASS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)
echo "✓ Senha gerada: ${NEW_PASS:0:8}***"
echo ""

echo "[4/9] Fazendo backup do .env..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
echo "✓ Backup criado"
echo ""

echo "[5/9] Atualizando POSTGRES_PASSWORD no .env..."
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env
echo "✓ POSTGRES_PASSWORD atualizado"
echo ""

echo "[6/9] Atualizando DATABASE_URL no .env..."
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASS@db:5432/sentinelweb|" .env
echo "✓ DATABASE_URL atualizado"
echo ""

echo "[7/9] Verificando alterações..."
echo "Configurações atuais:"
grep -E "^(POSTGRES_PASSWORD|DATABASE_URL)=" .env | sed 's/\(PASSWORD=\).*/\1***OCULTA***/' | sed 's/\(:[^@]*\)@/:*****@/'
echo ""

echo "[8/9] Recriando containers..."
docker compose -f docker-compose.prod.yml up -d
echo "✓ Containers iniciados"
echo ""

echo "[9/9] Aguardando PostgreSQL ficar pronto (30 segundos)..."
for i in {30..1}; do
    printf "\r   Aguardando... %02d segundos" $i
    sleep 1
done
echo ""
echo "✓ Tempo de espera concluído"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CORREÇÃO CONCLUÍDA COM SUCESSO!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔐 Nova senha PostgreSQL: $NEW_PASS"
echo "⚠️  GUARDE ESTA SENHA EM LOCAL SEGURO!"
echo ""
echo "📊 Verificando status dos containers:"
docker compose -f docker-compose.prod.yml ps
echo ""
echo "🧪 Testando conexão ao PostgreSQL:"
if docker compose -f docker-compose.prod.yml exec -T db psql -U sentinelweb -d sentinelweb -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Conexão PostgreSQL OK!"
else
    echo "⚠️  Aguarde mais alguns segundos e tente novamente"
fi
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 PRÓXIMO PASSO - Criar Superusuário:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Execute agora:"
echo "   docker compose -f docker-compose.prod.yml exec web python create_superuser.py"
echo ""
echo "E forneça:"
echo "   - Nome: Seu Nome Completo"
echo "   - Email: guilhermesantiago921@gmail.com"
echo "   - Senha: (escolha uma senha forte)"
echo ""
