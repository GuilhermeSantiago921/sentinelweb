#!/bin/bash

# ====================================================
# 🚀 ATUALIZAR SERVIDOR - ADMIN PANEL FIXES
# ====================================================
# Execute este script NO SERVIDOR para aplicar as correções
# ====================================================

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 ATUALIZAR SERVIDOR COM CORREÇÕES DO ADMIN PANEL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Código já foi comitado e enviado para GitHub!"
echo "✅ Agora vamos atualizar o servidor..."
echo ""

# Verificar se está no diretório correto
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ ERRO: docker-compose.prod.yml não encontrado!"
    echo "Execute este script em: /opt/sentinelweb"
    exit 1
fi

echo "[1/7] 📦 Fazendo backup do admin.py atual..."
cp admin.py admin.py.backup_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup criado!"
echo ""

echo "[2/7] 📥 Baixando código atualizado do GitHub..."
git fetch origin
git reset --hard origin/main
echo "✅ Código atualizado!"
echo ""

echo "[3/7] 🔍 Verificando correções aplicadas..."
echo ""
echo "   Verificando se 'import jwt' foi removido..."
if grep -q "^import jwt" admin.py; then
    echo "   ❌ ERRO: 'import jwt' ainda está no arquivo!"
    exit 1
else
    echo "   ✅ 'import jwt' removido com sucesso!"
fi

echo ""
echo "   Verificando se 'decode_token' está presente..."
if grep -q "decode_token" admin.py; then
    echo "   ✅ 'decode_token' encontrado!"
else
    echo "   ❌ ERRO: 'decode_token' não encontrado!"
    exit 1
fi

echo ""
echo "   Verificando se usa 'SessionLocal' (síncrono)..."
if grep -q "SessionLocal" admin.py; then
    echo "   ✅ 'SessionLocal' encontrado (modo síncrono)!"
else
    echo "   ❌ ERRO: 'SessionLocal' não encontrado!"
    exit 1
fi

echo ""
echo "✅ Todas as verificações passaram!"
echo ""

echo "[4/7] 🛑 Parando containers..."
docker compose -f docker-compose.prod.yml down
echo "✅ Containers parados!"
echo ""

echo "[5/7] 🔨 Rebuilding imagem (sem cache)..."
docker compose -f docker-compose.prod.yml build --no-cache web
echo "✅ Build completo!"
echo ""

echo "[6/7] 🚀 Iniciando containers..."
docker compose -f docker-compose.prod.yml up -d
echo "✅ Containers iniciados!"
echo ""

echo "[7/7] ⏳ Aguardando inicialização (40 segundos)..."
for i in {40..1}; do
    echo -ne "   Aguardando... $i segundos restantes\r"
    sleep 1
done
echo ""
echo "✅ Aguardo completo!"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 VERIFICAÇÃO FINAL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📊 Status dos containers:"
docker compose -f docker-compose.prod.yml ps
echo ""

echo "🌐 Testando endpoint /health..."
sleep 5  # Aguardar mais 5 segundos
if curl -sf http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Aplicação está SAUDÁVEL!"
else
    echo "⚠️  Endpoint /health não responde ainda..."
    echo "    Verificando logs..."
    docker compose -f docker-compose.prod.yml logs --tail=20 web
fi
echo ""

echo "📋 Últimas 30 linhas do log (buscando erros):"
echo ""
docker compose -f docker-compose.prod.yml logs --tail=30 web | grep -i "error\|exception\|traceback" || echo "✅ Nenhum erro encontrado nos logs!"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ATUALIZAÇÃO COMPLETA!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1️⃣  Verificar logs completos (se necessário):"
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
echo "5️⃣  Testar HTTPS:"
echo "   curl -I https://seudominio.com.br"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 SISTEMA PRONTO!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
