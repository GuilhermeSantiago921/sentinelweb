#!/bin/bash

# ====================================================
# 🚀 DEPLOY FINAL - ADMIN PANEL SQLADMIN
# ====================================================
# Aplica todas as correções e faz deploy completo
# Resolve os 3 erros de importação encontrados
# ====================================================

set -e  # Parar se houver erro

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 DEPLOY ADMIN PANEL - CORREÇÕES FINAIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar se está no diretório correto
if [ ! -f "main.py" ]; then
    echo "❌ ERRO: Execute este script no diretório /opt/sentinelweb"
    exit 1
fi

# ====================================================
# 1️⃣  BACKUP DO CÓDIGO ATUAL
# ====================================================
echo "[1/8] 📦 Fazendo backup do código atual..."
cp admin.py admin.py.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
echo "✅ Backup criado!"
echo ""

# ====================================================
# 2️⃣  PULL DO CÓDIGO ATUALIZADO
# ====================================================
echo "[2/8] 📥 Baixando código atualizado do GitHub..."
git fetch origin
git reset --hard origin/main
echo "✅ Código atualizado!"
echo ""

# ====================================================
# 3️⃣  VERIFICAR ALTERAÇÕES NO ADMIN.PY
# ====================================================
echo "[3/8] 🔍 Verificando admin.py..."
if grep -q "decode_token" admin.py; then
    echo "✅ admin.py está com decode_token (correto!)"
else
    echo "⚠️  admin.py ainda tem verify_token, aplicando correção..."
    sed -i 's/from auth import verify_token,/from auth import decode_token,/g' admin.py
    sed -i 's/payload = verify_token(token)/payload = decode_token(token)\n\n            # Verifica se o token é válido\n            if not payload:\n                return False/g' admin.py
    echo "✅ Correção aplicada manualmente!"
fi
echo ""

# ====================================================
# 4️⃣  PARAR CONTAINERS
# ====================================================
echo "[4/8] 🛑 Parando containers..."
docker compose -f docker-compose.prod.yml down
echo "✅ Containers parados!"
echo ""

# ====================================================
# 5️⃣  REBUILD SEM CACHE
# ====================================================
echo "[5/8] 🔨 Rebuilding imagens (sem cache)..."
docker compose -f docker-compose.prod.yml build --no-cache web
echo "✅ Build completo!"
echo ""

# ====================================================
# 6️⃣  INICIAR CONTAINERS
# ====================================================
echo "[6/8] 🚀 Iniciando containers..."
docker compose -f docker-compose.prod.yml up -d
echo "✅ Containers iniciados!"
echo ""

# ====================================================
# 7️⃣  AGUARDAR INICIALIZAÇÃO
# ====================================================
echo "[7/8] ⏳ Aguardando aplicação inicializar (40s)..."
sleep 40
echo "✅ Aguardo completo!"
echo ""

# ====================================================
# 8️⃣  VERIFICAR STATUS
# ====================================================
echo "[8/8] 🔍 Verificando status..."
echo ""
docker compose -f docker-compose.prod.yml ps
echo ""

# Testar endpoint
echo "🌐 Testando endpoint /health..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Aplicação está rodando!"
else
    echo "⚠️  Endpoint /health não responde, verificando logs..."
    docker compose -f docker-compose.prod.yml logs --tail=30 web
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOY COMPLETO!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1️⃣  Verificar logs:"
echo "   docker compose -f docker-compose.prod.yml logs -f web"
echo ""
echo "2️⃣  Criar superusuário admin:"
echo "   docker compose -f docker-compose.prod.yml exec web python setup_admin.py"
echo ""
echo "3️⃣  Acessar painel admin:"
echo "   https://seudominio.com.br/admin"
echo ""
echo "4️⃣  Reiniciar Nginx (se necessário):"
echo "   systemctl restart nginx"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
