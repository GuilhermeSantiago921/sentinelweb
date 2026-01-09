#!/bin/bash

# Script de Inicialização Rápida - SentinelWeb
# Este script prepara e inicia o ambiente de desenvolvimento

echo "🛡️  SentinelWeb - Inicialização"
echo "================================"
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.11+"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa ambiente virtual
echo "🔄 Ativando ambiente virtual..."
source venv/bin/activate

# Instala dependências
echo "📥 Instalando dependências..."
pip install -r requirements.txt

# Cria arquivo .env se não existir
if [ ! -f ".env" ]; then
    echo "⚙️  Criando arquivo .env..."
    cp .env.example .env
fi

# Verifica Redis
echo ""
echo "🔍 Verificando Redis..."
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis não encontrado!"
    echo "   Instale com: brew install redis (Mac) ou sudo apt install redis (Linux)"
    echo "   Ou use Docker: docker run -d -p 6379:6379 redis:alpine"
else
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis está rodando!"
    else
        echo "⚠️  Redis instalado mas não está rodando"
        echo "   Inicie com: brew services start redis (Mac) ou sudo systemctl start redis (Linux)"
    fi
fi

echo ""
echo "✅ Setup concluído!"
echo ""
echo "📋 Próximos passos:"
echo "   1. Terminal 1: uvicorn main:app --reload"
echo "   2. Terminal 2: celery -A celery_app worker --loglevel=info"
echo "   3. Terminal 3: celery -A celery_app beat --loglevel=info"
echo "   4. Acesse: http://localhost:8000"
echo ""
echo "Ou use Docker: docker-compose up --build"
echo ""
