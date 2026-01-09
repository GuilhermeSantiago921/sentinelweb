#!/bin/bash
################################################################################
# SENTINELWEB - INSTALAÇÃO AUTOMÁTICA UBUNTU (v2.0 - CORRIGIDO)
################################################################################
# Descrição: Script de instalação e configuração completa do SentinelWeb
# Compatível: Ubuntu 20.04 LTS, 22.04 LTS, 24.04 LTS
# Requisitos: Executar como root ou com sudo
# Uso: sudo bash install.sh
# 
# CORREÇÕES v2.0:
# - Garante sincronização de senha PostgreSQL
# - Remove volumes antigos antes de iniciar
# - Aguarda PostgreSQL ficar completamente pronto
# - Melhor tratamento de erros
# - Remove atributo 'version' obsoleto do docker-compose
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗║
║   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║║
║   ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║║
║   ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║║
║   ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███║
║   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══╝║
║                                                               ║
║              🔧 INSTALAÇÃO AUTOMÁTICA - UBUNTU 🔧             ║
║                       Versão 2.0.0                           ║
║                                                               ║
║        📦 GitHub: GuilhermeSantiago921/sentinelweb           ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

################################################################################
# FUNÇÕES AUXILIARES
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}[PASSO $1/$2]${NC} $3"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

confirm() {
    read -p "$(echo -e ${YELLOW}"$1 (s/N): "${NC})" -n 1 -r
    echo
    [[ $REPLY =~ ^[SsYy]$ ]]
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Este script precisa ser executado como root!"
        log_info "Execute: sudo bash install.sh"
        exit 1
    fi
}

check_ubuntu() {
    if [ ! -f /etc/os-release ]; then
        log_error "Sistema operacional não identificado!"
        exit 1
    fi
    
    . /etc/os-release
    
    if [ "$ID" != "ubuntu" ]; then
        log_error "Este script é compatível apenas com Ubuntu!"
        log_info "Detectado: $ID $VERSION_ID"
        exit 1
    fi
    
    log_success "Sistema detectado: Ubuntu $VERSION_ID"
}

check_disk_space() {
    AVAILABLE_SPACE=$(df / | tail -1 | awk '{print $4}')
    REQUIRED_SPACE=10485760
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        log_error "Espaço em disco insuficiente!"
        log_info "Disponível: $(($AVAILABLE_SPACE / 1024 / 1024))GB"
        log_info "Necessário: 10GB (recomendado 20GB)"
        exit 1
    fi
    
    log_success "Espaço em disco: $(($AVAILABLE_SPACE / 1024 / 1024))GB disponível"
}

check_memory() {
    TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
    REQUIRED_MEM=1536
    
    if [ "$TOTAL_MEM" -lt "$REQUIRED_MEM" ]; then
        log_warning "RAM abaixo do recomendado!"
        log_info "Disponível: ${TOTAL_MEM}MB"
        log_info "Recomendado: 2048MB (2GB)"
        
        if ! confirm "Deseja continuar mesmo assim?"; then
            exit 1
        fi
    else
        log_success "RAM: ${TOTAL_MEM}MB"
    fi
}

################################################################################
# VERIFICAÇÕES INICIAIS
################################################################################

TOTAL_STEPS=20

log_step 0 $TOTAL_STEPS "Verificações Iniciais"

check_root
check_ubuntu
check_disk_space
check_memory

# Detectar usuário
if [ -n "${SUDO_USER:-}" ]; then
    INSTALL_USER=$SUDO_USER
else
    INSTALL_USER=$(whoami)
fi

log_info "Usuário de instalação: $INSTALL_USER"

# Diretórios
INSTALL_DIR="/opt/sentinelweb"
DATA_DIR="/var/lib/sentinelweb"
BACKUP_DIR="/var/backups/sentinelweb"
LOG_DIR="/var/log/sentinelweb"

log_info "Diretório de instalação: $INSTALL_DIR"

# Confirmar instalação
echo ""
log_warning "Este script irá instalar:"
echo "  • Docker & Docker Compose"
echo "  • PostgreSQL 15 (containerizado)"
echo "  • Redis (containerizado)"
echo "  • Nginx (reverse proxy)"
echo "  • Certbot (SSL/TLS)"
echo "  • UFW (firewall)"
echo "  • Fail2Ban (proteção brute force)"
echo ""

if ! confirm "Deseja continuar com a instalação?"; then
    log_info "Instalação cancelada pelo usuário."
    exit 0
fi

################################################################################
# PASSO 1: ATUALIZAR SISTEMA
################################################################################

log_step 1 $TOTAL_STEPS "Atualizando Sistema"

export DEBIAN_FRONTEND=noninteractive

log_info "Atualizando lista de pacotes..."
apt-get update -qq

log_info "Atualizando pacotes instalados..."
apt-get upgrade -y -qq

log_info "Instalando dependências básicas..."
apt-get install -y -qq \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    git \
    wget \
    unzip \
    vim \
    htop \
    net-tools \
    dnsutils \
    jq \
    python3 \
    python3-pip \
    python3-venv

log_success "Sistema atualizado com sucesso!"

################################################################################
# PASSO 2: INSTALAR DOCKER
################################################################################

log_step 2 $TOTAL_STEPS "Instalando Docker"

if command -v docker &> /dev/null; then
    log_warning "Docker já está instalado ($(docker --version))"
else
    log_info "Adicionando repositório Docker..."
    
    apt-get remove -y -qq docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    usermod -aG docker $INSTALL_USER
    
    systemctl enable docker
    systemctl start docker
    
    log_success "Docker instalado: $(docker --version)"
fi

if docker compose version &> /dev/null; then
    log_success "Docker Compose instalado: $(docker compose version)"
else
    log_error "Docker Compose não encontrado!"
    exit 1
fi

################################################################################
# PASSO 3: INSTALAR NGINX
################################################################################

log_step 3 $TOTAL_STEPS "Instalando Nginx"

if command -v nginx &> /dev/null; then
    log_warning "Nginx já está instalado"
else
    apt-get install -y -qq nginx nginx-extras
    systemctl enable nginx
    log_success "Nginx instalado"
fi

################################################################################
# PASSO 4: INSTALAR CERTBOT
################################################################################

log_step 4 $TOTAL_STEPS "Instalando Certbot"

if command -v certbot &> /dev/null; then
    log_warning "Certbot já está instalado"
else
    apt-get install -y -qq certbot python3-certbot-nginx
    log_success "Certbot instalado"
fi

################################################################################
# PASSO 5: CONFIGURAR FIREWALL
################################################################################

log_step 5 $TOTAL_STEPS "Configurando Firewall"

if command -v ufw &> /dev/null; then
    ufw --force disable
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow 22/tcp comment 'SSH'
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'
    ufw --force enable
    log_success "Firewall configurado!"
fi

################################################################################
# PASSO 6: INSTALAR FAIL2BAN
################################################################################

log_step 6 $TOTAL_STEPS "Instalando Fail2Ban"

if ! command -v fail2ban-client &> /dev/null; then
    apt-get install -y -qq fail2ban
    
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF
    
    systemctl enable fail2ban
    systemctl restart fail2ban
    log_success "Fail2Ban instalado!"
else
    log_warning "Fail2Ban já está instalado"
fi

################################################################################
# PASSO 7: CRIAR ESTRUTURA DE DIRETÓRIOS
################################################################################

log_step 7 $TOTAL_STEPS "Criando Estrutura de Diretórios"

mkdir -p $INSTALL_DIR
mkdir -p $DATA_DIR/{postgres,redis}
mkdir -p $BACKUP_DIR
mkdir -p $LOG_DIR
mkdir -p /etc/nginx/ssl

if ! id "sentinelweb" &>/dev/null; then
    useradd -r -s /bin/bash -d $INSTALL_DIR -m sentinelweb
fi
usermod -aG docker sentinelweb 2>/dev/null || true

chown -R sentinelweb:sentinelweb $INSTALL_DIR
chown -R sentinelweb:sentinelweb $DATA_DIR
chown -R sentinelweb:sentinelweb $BACKUP_DIR
chown -R sentinelweb:sentinelweb $LOG_DIR

log_success "Estrutura de diretórios criada!"

################################################################################
# PASSO 8: LIMPAR INSTALAÇÃO ANTERIOR (SE EXISTIR) *** CRÍTICO ***
################################################################################

log_step 8 $TOTAL_STEPS "Limpando Instalação Anterior"

cd $INSTALL_DIR 2>/dev/null || cd /tmp

# Verificar se existem containers/volumes antigos
VOLUMES_EXIST=false
if docker volume ls 2>/dev/null | grep -q "sentinelweb"; then
    VOLUMES_EXIST=true
fi

CONTAINERS_EXIST=false
if docker ps -a 2>/dev/null | grep -q "sentinelweb"; then
    CONTAINERS_EXIST=true
fi

if [ "$VOLUMES_EXIST" = true ] || [ "$CONTAINERS_EXIST" = true ]; then
    log_warning "Instalação anterior detectada!"
    echo ""
    echo -e "   ${YELLOW}ATENÇÃO:${NC} Volumes/containers existentes podem causar"
    echo -e "   problemas de autenticação no PostgreSQL."
    echo ""
    echo -e "   ${RED}REMOVER:${NC} Limpa tudo e faz instalação limpa (PERDE DADOS!)"
    echo -e "   ${GREEN}MANTER:${NC} Tenta usar dados existentes (pode falhar)"
    echo ""
    
    if confirm "Deseja REMOVER volumes/containers antigos? (APAGA DADOS DO BANCO!)"; then
        log_info "Parando containers antigos..."
        cd $INSTALL_DIR 2>/dev/null && docker compose -f docker-compose.prod.yml down -v 2>/dev/null || true
        
        # Parar todos os containers com nome sentinelweb
        docker ps -aq --filter "name=sentinelweb" | xargs -r docker stop 2>/dev/null || true
        docker ps -aq --filter "name=sentinelweb" | xargs -r docker rm -f 2>/dev/null || true
        
        log_info "Removendo volumes..."
        docker volume rm sentinelweb_postgres_data 2>/dev/null || true
        docker volume rm sentinelweb_redis_data 2>/dev/null || true
        
        # Remover TODOS os volumes relacionados
        docker volume ls -q 2>/dev/null | grep -i sentinelweb | xargs -r docker volume rm 2>/dev/null || true
        
        # Limpar networks antigas
        docker network ls -q --filter "name=sentinelweb" | xargs -r docker network rm 2>/dev/null || true
        
        log_success "Instalação anterior removida!"
        CLEAN_INSTALL=true
    else
        log_warning "Mantendo dados antigos - podem ocorrer problemas de autenticação!"
        CLEAN_INSTALL=false
    fi
else
    log_success "Nenhuma instalação anterior encontrada"
    CLEAN_INSTALL=true
fi

################################################################################
# PASSO 9: BAIXAR APLICAÇÃO DO GITHUB
################################################################################

log_step 9 $TOTAL_STEPS "Baixando Aplicação do GitHub"

GITHUB_REPO="https://github.com/GuilhermeSantiago921/sentinelweb.git"

log_info "Verificando conectividade com GitHub..."
if ! curl -s --connect-timeout 10 https://github.com > /dev/null; then
    log_error "Não foi possível conectar ao GitHub!"
    exit 1
fi
log_success "Conexão com GitHub OK!"

# Fazer backup do .env se existir
if [ -f "$INSTALL_DIR/.env" ]; then
    cp $INSTALL_DIR/.env /tmp/.env.backup.$(date +%Y%m%d_%H%M%S)
    log_info "Backup do .env criado"
fi

# Clonar ou atualizar repositório
if [ -d "$INSTALL_DIR/.git" ]; then
    log_info "Atualizando repositório existente..."
    cd $INSTALL_DIR
    git fetch origin
    git reset --hard origin/main
    log_success "Repositório atualizado!"
else
    if [ -d "$INSTALL_DIR" ] && [ "$(ls -A $INSTALL_DIR 2>/dev/null)" ]; then
        BACKUP_NAME="/tmp/sentinelweb.backup.$(date +%Y%m%d_%H%M%S)"
        mv $INSTALL_DIR $BACKUP_NAME
        log_info "Backup criado: $BACKUP_NAME"
        mkdir -p $INSTALL_DIR
    fi
    
    git clone $GITHUB_REPO $INSTALL_DIR
    log_success "Repositório clonado!"
fi

chown -R sentinelweb:sentinelweb $INSTALL_DIR

################################################################################
# PASSO 10: GERAR CREDENCIAIS
################################################################################

log_step 10 $TOTAL_STEPS "Gerando Credenciais de Segurança"

# Gerar senhas SEM caracteres especiais (evita problemas de escape)
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)
REDIS_PASSWORD=$(openssl rand -hex 16)

log_success "Credenciais geradas (apenas caracteres alfanuméricos)!"
echo ""
echo -e "   ${CYAN}POSTGRES_PASSWORD:${NC} $POSTGRES_PASSWORD"
echo ""

################################################################################
# PASSO 11: COLETAR INFORMAÇÕES DO USUÁRIO
################################################################################

log_step 11 $TOTAL_STEPS "Configuração de Acesso"

echo ""
log_info "MODO DE INSTALAÇÃO:"
echo ""
echo "  1) ${GREEN}Com Domínio${NC} - Produção com HTTPS/SSL"
echo "  2) ${YELLOW}Apenas IP${NC} - Teste/Desenvolvimento (HTTP)"
echo ""

USE_DOMAIN=""
while [[ ! "$USE_DOMAIN" =~ ^[12]$ ]]; do
    read -p "$(echo -e ${CYAN}'Escolha o modo (1 ou 2): '${NC})" USE_DOMAIN
done

if [ "$USE_DOMAIN" = "1" ]; then
    read -p "$(echo -e ${CYAN}'Digite o domínio (ex: sentinelweb.com.br): '${NC})" APP_DOMAIN
    read -p "$(echo -e ${CYAN}'Digite o email para SSL: '${NC})" ADMIN_EMAIL
    
    APP_DOMAIN=$(echo "$APP_DOMAIN" | tr -d '[:space:]')
    ADMIN_EMAIL=$(echo "$ADMIN_EMAIL" | tr -d '[:space:]')
    
    if [ -z "$APP_DOMAIN" ] || [ -z "$ADMIN_EMAIL" ]; then
        log_error "Domínio e email são obrigatórios!"
        exit 1
    fi
    
    INSTALL_MODE="domain"
else
    SERVER_IP=$(curl -4 -s --connect-timeout 5 ifconfig.me 2>/dev/null || echo "")
    
    if [ -z "$SERVER_IP" ]; then
        read -p "$(echo -e ${CYAN}'Digite o IP do servidor: '${NC})" SERVER_IP
    else
        log_info "IP detectado: $SERVER_IP"
        read -p "$(echo -e ${CYAN}'Confirme ou corrija o IP: '${NC})" -i "$SERVER_IP" -e CONFIRMED_IP
        SERVER_IP=${CONFIRMED_IP:-$SERVER_IP}
    fi
    
    APP_DOMAIN=$SERVER_IP
    ADMIN_EMAIL="admin@localhost"
    INSTALL_MODE="ip-only"
fi

log_success "Configuração: $APP_DOMAIN"

################################################################################
# PASSO 12: CRIAR ARQUIVO .env
################################################################################

log_step 12 $TOTAL_STEPS "Criando Arquivo .env"

ENV_FILE="$INSTALL_DIR/.env"

cat > $ENV_FILE << EOF
# ============================================================================
# SENTINELWEB - CONFIGURAÇÃO DE PRODUÇÃO
# Gerado em: $(date)
# ============================================================================

# SEGURANÇA
SECRET_KEY=$SECRET_KEY

# BANCO DE DADOS - POSTGRESQL
POSTGRES_USER=sentinelweb
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=sentinelweb
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql://sentinelweb:$POSTGRES_PASSWORD@db:5432/sentinelweb

# REDIS
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_URL=redis://:$REDIS_PASSWORD@redis:6379/0

# APLICAÇÃO
APP_NAME=SentinelWeb
APP_DOMAIN=$APP_DOMAIN
APP_URL=https://$APP_DOMAIN
ENVIRONMENT=production

# ASAAS (PAGAMENTOS) - OPCIONAL
ASAAS_API_KEY=
ASAAS_API_URL=https://api.asaas.com/v3

# TELEGRAM (ALERTAS) - OPCIONAL
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# CONFIGURAÇÕES
LOG_LEVEL=INFO
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MAX_SITES_PER_USER=10
CHECK_INTERVAL_MINUTES=5
UVICORN_WORKERS=4
CELERY_CONCURRENCY=4
EOF

chown sentinelweb:sentinelweb $ENV_FILE
chmod 600 $ENV_FILE

log_success "Arquivo .env criado!"

################################################################################
# PASSO 13: CORRIGIR DOCKER-COMPOSE (REMOVER VERSION OBSOLETO)
################################################################################

log_step 13 $TOTAL_STEPS "Corrigindo docker-compose.prod.yml"

cd $INSTALL_DIR

# Remover linha 'version' obsoleta do docker-compose
if grep -q "^version:" docker-compose.prod.yml 2>/dev/null; then
    log_info "Removendo atributo 'version' obsoleto..."
    sed -i '/^version:/d' docker-compose.prod.yml
    log_success "docker-compose.prod.yml corrigido!"
else
    log_success "docker-compose.prod.yml já está correto"
fi

################################################################################
# PASSO 14: GERAR DHPARAM
################################################################################

log_step 14 $TOTAL_STEPS "Gerando DH Param"

DHPARAM_FILE="/etc/nginx/ssl/dhparam.pem"

if [ ! -f "$DHPARAM_FILE" ]; then
    log_info "Gerando dhparam.pem (pode demorar)..."
    openssl dhparam -out $DHPARAM_FILE 2048
    chmod 644 $DHPARAM_FILE
    log_success "DH Param gerado!"
else
    log_warning "DH Param já existe"
fi

################################################################################
# PASSO 15: CONFIGURAR NGINX
################################################################################

log_step 15 $TOTAL_STEPS "Configurando Nginx"

NGINX_CONFIG="/etc/nginx/sites-available/sentinelweb"

if [ "$INSTALL_MODE" = "ip-only" ]; then
    cat > $NGINX_CONFIG << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    server_tokens off;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
EOF
else
    cat > $NGINX_CONFIG << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $APP_DOMAIN www.$APP_DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        allow all;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
fi

rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/sites-enabled/sentinelweb
ln -s $NGINX_CONFIG /etc/nginx/sites-enabled/sentinelweb

if nginx -t; then
    systemctl reload nginx
    log_success "Nginx configurado!"
else
    log_error "Erro na configuração do Nginx!"
    exit 1
fi

################################################################################
# PASSO 16: GARANTIR VOLUMES LIMPOS *** CRÍTICO PARA POSTGRESQL ***
################################################################################

log_step 16 $TOTAL_STEPS "Preparando Ambiente Docker"

cd $INSTALL_DIR

# Este passo é CRÍTICO - garantir que não há volumes antigos
# O PostgreSQL só aceita a senha do .env na PRIMEIRA inicialização

log_info "Verificando volumes Docker..."

if docker volume ls 2>/dev/null | grep -q "sentinelweb_postgres_data"; then
    if [ "$CLEAN_INSTALL" = true ]; then
        log_info "Removendo volume PostgreSQL antigo..."
        docker volume rm sentinelweb_postgres_data 2>/dev/null || true
    else
        log_warning "Volume PostgreSQL existente - usando dados anteriores"
    fi
fi

if docker volume ls 2>/dev/null | grep -q "sentinelweb_redis_data"; then
    if [ "$CLEAN_INSTALL" = true ]; then
        log_info "Removendo volume Redis antigo..."
        docker volume rm sentinelweb_redis_data 2>/dev/null || true
    fi
fi

log_success "Ambiente Docker preparado!"

################################################################################
# PASSO 17: CONSTRUIR E INICIAR CONTAINERS
################################################################################

log_step 17 $TOTAL_STEPS "Construindo e Iniciando Containers"

cd $INSTALL_DIR

log_info "Construindo imagens Docker..."
if docker compose -f docker-compose.prod.yml build --no-cache; then
    log_success "Imagens construídas!"
else
    log_error "Falha ao construir imagens!"
    exit 1
fi

log_info "Iniciando containers..."
if docker compose -f docker-compose.prod.yml up -d; then
    log_success "Containers iniciados!"
else
    log_error "Falha ao iniciar containers!"
    exit 1
fi

# Mostrar status
docker compose -f docker-compose.prod.yml ps

################################################################################
# PASSO 18: AGUARDAR E VERIFICAR POSTGRESQL
################################################################################

log_step 18 $TOTAL_STEPS "Aguardando PostgreSQL"

# Aguardar containers subirem
log_info "Aguardando inicialização dos containers (15s)..."
sleep 15

# Aguardar PostgreSQL ficar pronto
MAX_WAIT=90
WAIT_TIME=0

log_info "Aguardando PostgreSQL aceitar conexões..."

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if docker compose -f docker-compose.prod.yml exec -T db pg_isready -U sentinelweb -d sentinelweb > /dev/null 2>&1; then
        echo ""
        log_success "PostgreSQL está pronto!"
        break
    fi
    
    echo -ne "\r   Aguardando... ${WAIT_TIME}s/${MAX_WAIT}s"
    sleep 3
    WAIT_TIME=$((WAIT_TIME + 3))
done

echo ""

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    log_error "PostgreSQL não ficou pronto em tempo hábil!"
    log_info "Verificando logs do container..."
    docker compose -f docker-compose.prod.yml logs --tail=50 db
    exit 1
fi

# Testar conexão real com autenticação
log_info "Testando autenticação no PostgreSQL..."

sleep 5  # Aguardar mais um pouco para garantir

if docker compose -f docker-compose.prod.yml exec -T db psql -U sentinelweb -d sentinelweb -c "SELECT 'AUTH_OK';" 2>&1 | grep -q "AUTH_OK"; then
    log_success "Autenticação PostgreSQL OK!"
else
    log_error "FALHA na autenticação PostgreSQL!"
    echo ""
    log_info "Isso indica que o volume PostgreSQL tem uma senha diferente do .env"
    log_info "Logs do PostgreSQL:"
    docker compose -f docker-compose.prod.yml logs --tail=30 db
    echo ""
    log_warning "SOLUÇÃO: Remover volumes e reinstalar"
    echo "   1) docker compose -f docker-compose.prod.yml down -v"
    echo "   2) docker volume rm sentinelweb_postgres_data"
    echo "   3) Executar install.sh novamente"
    exit 1
fi

################################################################################
# PASSO 19: CRIAR TABELAS E SUPERUSUÁRIO
################################################################################

log_step 19 $TOTAL_STEPS "Configurando Banco de Dados"

log_info "Criando estrutura do banco de dados..."

# Aguardar aplicação ficar pronta
sleep 5

if docker compose -f docker-compose.prod.yml exec -T web python -c "
from database import engine, Base
from models import User, Site, SiteCheck, MonitorLog, HeartbeatCheck, HeartbeatPing, SystemConfig, Payment
Base.metadata.create_all(bind=engine)
print('TABLES_CREATED')
" 2>&1 | grep -q "TABLES_CREATED"; then
    log_success "Tabelas criadas com sucesso!"
else
    log_warning "Aviso ao criar tabelas (podem já existir)"
    # Tentar novamente após uma pausa
    sleep 10
    docker compose -f docker-compose.prod.yml exec -T web python -c "
from database import engine, Base
from models import User, Site, SiteCheck, MonitorLog, HeartbeatCheck, HeartbeatPing, SystemConfig, Payment
Base.metadata.create_all(bind=engine)
" 2>/dev/null || true
fi

echo ""
if confirm "Deseja criar um superusuário agora?"; then
    log_info "Criando superusuário..."
    docker compose -f docker-compose.prod.yml exec web python create_superuser.py
    log_success "Superusuário criado!"
else
    log_warning "Superusuário NÃO criado."
    log_info "Execute depois:"
    echo "   cd $INSTALL_DIR"
    echo "   docker compose -f docker-compose.prod.yml exec web python create_superuser.py"
fi

################################################################################
# PASSO 20: CONFIGURAR SSL (SE MODO DOMÍNIO)
################################################################################

log_step 20 $TOTAL_STEPS "Finalização"

SSL_OBTAINED=false

if [ "$INSTALL_MODE" = "domain" ]; then
    mkdir -p /var/www/certbot
    chown -R www-data:www-data /var/www/certbot
    
    if confirm "Deseja obter certificado SSL agora?"; then
        if certbot certonly \
            --webroot \
            -w /var/www/certbot \
            --non-interactive \
            --agree-tos \
            --email "$ADMIN_EMAIL" \
            -d "$APP_DOMAIN"; then
            
            log_success "Certificado SSL obtido!"
            SSL_OBTAINED=true
            
            # Configurar renovação automática
            (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
        else
            log_warning "Falha ao obter SSL"
        fi
    fi
else
    log_info "Modo IP: SSL não configurado"
fi

################################################################################
# CONFIGURAR BACKUPS AUTOMÁTICOS
################################################################################

BACKUP_SCRIPT="$INSTALL_DIR/backup.sh"

cat > $BACKUP_SCRIPT << 'EOF'
#!/bin/bash
# Script de Backup Automático - SentinelWeb

BACKUP_DIR="/var/backups/sentinelweb"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "[$(date)] Iniciando backup..."

if docker exec sentinelweb_db_prod pg_dump -U sentinelweb sentinelweb | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz; then
    echo "[$(date)] Backup OK: $BACKUP_DIR/postgres_$DATE.sql.gz"
else
    echo "[$(date)] ERRO no backup!"
    exit 1
fi

# Manter apenas últimos 30 dias
find $BACKUP_DIR -name "postgres_*.sql.gz" -mtime +30 -delete

echo "[$(date)] Backup concluído!"
EOF

chmod +x $BACKUP_SCRIPT
(crontab -l 2>/dev/null | grep -v "backup.sh"; echo "0 2 * * * $BACKUP_SCRIPT >> $LOG_DIR/backup.log 2>&1") | crontab -

log_success "Backups automáticos configurados!"

################################################################################
# RESUMO FINAL
################################################################################

echo ""
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}               ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!                      ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$INSTALL_MODE" = "ip-only" ]; then
    echo -e "   ${BLUE}🌐 Acesso:${NC} http://$APP_DOMAIN"
else
    if [ "$SSL_OBTAINED" = true ]; then
        echo -e "   ${BLUE}🌐 Acesso:${NC} https://$APP_DOMAIN"
    else
        echo -e "   ${BLUE}🌐 Acesso:${NC} http://$APP_DOMAIN"
    fi
fi

echo ""
echo -e "${YELLOW}🔐 CREDENCIAIS (SALVE EM LOCAL SEGURO!):${NC}"
echo -e "   POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
echo -e "   REDIS_PASSWORD:    $REDIS_PASSWORD"
echo -e "   SECRET_KEY:        $SECRET_KEY"
echo ""
echo -e "${CYAN}📋 COMANDOS ÚTEIS:${NC}"
echo -e "   ${MAGENTA}Entrar no diretório:${NC}"
echo -e "   cd $INSTALL_DIR"
echo ""
echo -e "   ${MAGENTA}Ver status dos containers:${NC}"
echo -e "   docker compose -f docker-compose.prod.yml ps"
echo ""
echo -e "   ${MAGENTA}Ver logs da aplicação:${NC}"
echo -e "   docker compose -f docker-compose.prod.yml logs -f web"
echo ""
echo -e "   ${MAGENTA}Reiniciar containers:${NC}"
echo -e "   docker compose -f docker-compose.prod.yml restart"
echo ""
echo -e "   ${MAGENTA}Criar superusuário:${NC}"
echo -e "   docker compose -f docker-compose.prod.yml exec web python create_superuser.py"
echo ""

# Salvar resumo em arquivo
cat > $INSTALL_DIR/INSTALLATION_SUMMARY.txt << EOF
===============================================================================
SENTINELWEB - RESUMO DA INSTALAÇÃO
===============================================================================
Data/Hora: $(date)
Modo: $INSTALL_MODE
Domínio/IP: $APP_DOMAIN
Diretório: $INSTALL_DIR

===============================================================================
CREDENCIAIS (GUARDE EM LOCAL SEGURO!)
===============================================================================
POSTGRES_PASSWORD: $POSTGRES_PASSWORD
REDIS_PASSWORD: $REDIS_PASSWORD
SECRET_KEY: $SECRET_KEY

===============================================================================
PRÓXIMOS PASSOS
===============================================================================
1. Acesse: http://$APP_DOMAIN
2. Faça login com o superusuário criado
3. Configure o Telegram em Configurações (opcional)
4. Configure o Asaas em Configurações (opcional)

===============================================================================
SUPORTE
===============================================================================
GitHub: https://github.com/GuilhermeSantiago921/sentinelweb
EOF

chmod 600 $INSTALL_DIR/INSTALLATION_SUMMARY.txt

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
log_success "Instalação completa! 🚀"
echo ""

exit 0
