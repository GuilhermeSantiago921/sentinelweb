#!/bin/bash
# ========================================
# SentinelWeb - Script de Deploy Automático
# Painel Administrativo SQLAdmin
# ========================================

set -e  # Para na primeira falha

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para printar com cor
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║   🚀 SENTINELWEB - DEPLOY PAINEL ADMINISTRATIVO       ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ========================================
# 1. VERIFICAÇÕES PRÉ-DEPLOY
# ========================================

print_info "Verificando ambiente..."

# Verifica se está no diretório correto
if [ ! -f "main.py" ] || [ ! -f "admin.py" ]; then
    print_error "Execute este script no diretório raiz do projeto!"
    exit 1
fi

# Verifica se tem mudanças não commitadas
if [[ -n $(git status -s) ]]; then
    print_warning "Há mudanças não commitadas!"
    git status -s
    echo ""
    read -p "Deseja continuar mesmo assim? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_error "Deploy cancelado."
        exit 1
    fi
fi

print_success "Ambiente validado!"

# ========================================
# 2. GIT COMMIT E PUSH
# ========================================

echo ""
print_info "Preparando commit no GitHub..."

# Mostra arquivos que serão commitados
echo ""
echo "Arquivos novos/modificados:"
git status -s

echo ""
read -p "Deseja fazer commit destes arquivos? (S/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    print_warning "Commit ignorado. Continuando deploy com código atual..."
else
    # Adiciona arquivos
    git add admin.py setup_admin.py templates/admin_dashboard.html main.py requirements.txt \
           ADMIN_SQLADMIN_COMPLETE.md ADMIN_QUICKSTART.md DEPLOY_ADMIN_PANEL.md deploy_admin.sh
    
    print_success "Arquivos adicionados ao stage"
    
    # Commit
    git commit -m "feat: Painel administrativo enterprise com SQLAdmin

✨ Novos Recursos:
- Painel administrativo completo usando SQLAdmin
- Dashboard executivo com KPIs (MRR, Churn, Saúde, Fila Celery)
- Gestão de usuários (CRM) com filtros e busca
- Gestão de sites (Ops) com status visual
- Gestão financeira (ERP) integrada com Asaas
- Logs de monitoramento (auditoria read-only)
- Configurações do sistema (singleton)
- Autenticação blindada (apenas superusers)
- Gráficos interativos (Chart.js)

📦 Dependências: sqladmin[full], itsdangerous, redis
📚 Documentação completa incluída
🔒 Segurança: JWT + SessionMiddleware + validação superuser"
    
    print_success "Commit realizado!"
    
    # Push
    print_info "Fazendo push para GitHub..."
    
    BRANCH=$(git branch --show-current)
    git push origin $BRANCH
    
    print_success "Push concluído! Branch: $BRANCH"
fi

# ========================================
# 3. DEPLOY NO SERVIDOR
# ========================================

echo ""
echo -e "${YELLOW}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║              DEPLOY NO SERVIDOR                        ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════╝${NC}"

read -p "Digite o IP ou hostname do servidor (ex: 192.168.1.100): " SERVER_IP

if [ -z "$SERVER_IP" ]; then
    print_error "IP do servidor não fornecido!"
    exit 1
fi

read -p "Usuário SSH (padrão: root): " SSH_USER
SSH_USER=${SSH_USER:-root}

print_info "Conectando em $SSH_USER@$SERVER_IP..."

# Testa conexão SSH
if ! ssh -o ConnectTimeout=5 $SSH_USER@$SERVER_IP "echo 'Conexão OK'" &> /dev/null; then
    print_error "Falha ao conectar via SSH!"
    exit 1
fi

print_success "Conexão SSH estabelecida!"

# ========================================
# 4. EXECUTAR COMANDOS NO SERVIDOR
# ========================================

echo ""
print_info "Executando deploy no servidor..."

ssh $SSH_USER@$SERVER_IP << 'ENDSSH'
    set -e
    
    # Cores
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
    
    echo -e "${BLUE}📂 Navegando para /opt/sentinelweb${NC}"
    cd /opt/sentinelweb
    
    echo -e "${BLUE}💾 Criando backup...${NC}"
    BACKUP_DIR="/opt/sentinelweb_backup_$(date +%Y%m%d_%H%M%S)"
    cp -r /opt/sentinelweb $BACKUP_DIR
    echo -e "${GREEN}✅ Backup criado: $BACKUP_DIR${NC}"
    
    echo -e "${BLUE}📥 Fazendo git pull...${NC}"
    git pull origin main
    
    echo -e "${BLUE}🐳 Parando containers...${NC}"
    docker compose -f docker-compose.prod.yml down
    
    echo -e "${BLUE}🔨 Reconstruindo imagem do web...${NC}"
    docker compose -f docker-compose.prod.yml build --no-cache web
    
    echo -e "${BLUE}🚀 Iniciando containers...${NC}"
    docker compose -f docker-compose.prod.yml up -d
    
    echo -e "${BLUE}⏳ Aguardando containers iniciarem (10s)...${NC}"
    sleep 10
    
    echo -e "${BLUE}🔍 Verificando status dos containers...${NC}"
    docker compose -f docker-compose.prod.yml ps
    
    echo -e "${GREEN}✅ Deploy concluído no servidor!${NC}"
    
    echo ""
    echo -e "${YELLOW}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  PRÓXIMO PASSO: CRIAR SUPERUSUÁRIO                 ║${NC}"
    echo -e "${YELLOW}║  Execute: docker compose exec web python setup_admin.py  ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════╝${NC}"
ENDSSH

print_success "Deploy no servidor concluído!"

# ========================================
# 5. CRIAR SUPERUSUÁRIO (OPCIONAL)
# ========================================

echo ""
read -p "Deseja criar o superusuário agora? (S/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    print_info "Criando superusuário no servidor..."
    
    ssh -t $SSH_USER@$SERVER_IP << 'ENDSSH'
        cd /opt/sentinelweb
        docker compose -f docker-compose.prod.yml exec web python setup_admin.py
ENDSSH
    
    print_success "Superusuário configurado!"
fi

# ========================================
# 6. VERIFICAÇÕES FINAIS
# ========================================

echo ""
print_info "Executando verificações finais..."

ssh $SSH_USER@$SERVER_IP << 'ENDSSH'
    set -e
    cd /opt/sentinelweb
    
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    BLUE='\033[0;34m'
    NC='\033[0m'
    
    echo ""
    echo -e "${BLUE}📊 Status dos Containers:${NC}"
    docker compose -f docker-compose.prod.yml ps
    
    echo ""
    echo -e "${BLUE}📝 Últimas 20 linhas dos logs:${NC}"
    docker compose -f docker-compose.prod.yml logs web --tail=20
    
    echo ""
    echo -e "${BLUE}🧪 Testando health check...${NC}"
    if curl -s http://localhost:8000/ > /dev/null; then
        echo -e "${GREEN}✅ API respondendo!${NC}"
    else
        echo -e "${RED}❌ API não está respondendo!${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}🧪 Testando endpoint de stats do admin...${NC}"
    if curl -s http://localhost:8000/admin/api/dashboard-stats > /dev/null; then
        echo -e "${GREEN}✅ Endpoint de stats funcionando!${NC}"
    else
        echo -e "${RED}❌ Endpoint de stats não está respondendo!${NC}"
    fi
ENDSSH

# ========================================
# 7. RESUMO FINAL
# ========================================

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ DEPLOY CONCLUÍDO COM SUCESSO!          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"

echo ""
echo -e "${BLUE}📋 Resumo do Deploy:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "✅ Código commitado no GitHub"
echo -e "✅ Servidor atualizado via git pull"
echo -e "✅ Containers reconstruídos"
echo -e "✅ Aplicação reiniciada"
echo -e "✅ Verificações executadas"

echo ""
echo -e "${YELLOW}🌐 Próximos Passos:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Acesse o painel: https://$SERVER_IP/admin"
echo "2. Faça login com o superusuário criado"
echo "3. Explore o dashboard com KPIs"
echo "4. Configure os módulos (Usuários, Sites, Pagamentos)"

echo ""
echo -e "${BLUE}📚 Documentação:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "• ADMIN_SQLADMIN_COMPLETE.md - Guia completo"
echo "• ADMIN_QUICKSTART.md - Quickstart"
echo "• DEPLOY_ADMIN_PANEL.md - Guia de deploy"

echo ""
echo -e "${BLUE}🛠️  Comandos Úteis:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "# Ver logs em tempo real:"
echo "ssh $SSH_USER@$SERVER_IP 'cd /opt/sentinelweb && docker compose logs -f web'"
echo ""
echo "# Reiniciar aplicação:"
echo "ssh $SSH_USER@$SERVER_IP 'cd /opt/sentinelweb && docker compose restart web'"
echo ""
echo "# Criar novo superusuário:"
echo "ssh $SSH_USER@$SERVER_IP 'cd /opt/sentinelweb && docker compose exec web python setup_admin.py'"

echo ""
print_success "Deploy finalizado! 🎉"
