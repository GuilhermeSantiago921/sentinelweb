#!/bin/bash
################################################################################
# SENTINELWEB - INSTALAÇÃO AUTOMÁTICA UBUNTU
################################################################################
# Descrição: Script de instalação e configuração completa do SentinelWeb
# Compatível: Ubuntu 20.04 LTS, 22.04 LTS, 24.04 LTS
# Requisitos: Executar como root ou com sudo
# Uso: sudo bash install.sh
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
║                       Versão 1.0.0                           ║
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

################################################################################
# VERIFICAÇÕES INICIAIS
################################################################################

TOTAL_STEPS=20

log_step 0 $TOTAL_STEPS "Verificações Iniciais"

check_root
check_ubuntu

# Detectar usuário que executou sudo
if [ -n "${SUDO_USER:-}" ]; then
    INSTALL_USER=$SUDO_USER
else
    INSTALL_USER=$(whoami)
fi

log_info "Usuário de instalação: $INSTALL_USER"

# Detectar diretório de instalação
INSTALL_DIR="/opt/sentinelweb"
DATA_DIR="/var/lib/sentinelweb"
BACKUP_DIR="/var/backups/sentinelweb"
LOG_DIR="/var/log/sentinelweb"

log_info "Diretório de instalação: $INSTALL_DIR"
log_info "Diretório de dados: $DATA_DIR"
log_info "Diretório de backups: $BACKUP_DIR"
log_info "Diretório de logs: $LOG_DIR"

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
log_info "O código será baixado automaticamente do GitHub:"
log_info "📦 https://github.com/GuilhermeSantiago921/sentinelweb.git"
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
    
    # Remover versões antigas
    apt-get remove -y -qq docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Adicionar chave GPG
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    
    # Adicionar repositório
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Instalar Docker
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Adicionar usuário ao grupo docker
    usermod -aG docker $INSTALL_USER
    
    # Iniciar Docker
    systemctl enable docker
    systemctl start docker
    
    log_success "Docker instalado: $(docker --version)"
fi

# Verificar Docker Compose
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
    log_warning "Nginx já está instalado ($(nginx -v 2>&1))"
else
    log_info "Instalando Nginx..."
    apt-get install -y -qq nginx nginx-extras
    
    # Configurar para iniciar automaticamente
    systemctl enable nginx
    
    log_success "Nginx instalado: $(nginx -v 2>&1)"
fi

################################################################################
# PASSO 4: INSTALAR CERTBOT
################################################################################

log_step 4 $TOTAL_STEPS "Instalando Certbot (Let's Encrypt)"

if command -v certbot &> /dev/null; then
    log_warning "Certbot já está instalado ($(certbot --version 2>&1 | head -n1))"
else
    log_info "Instalando Certbot..."
    apt-get install -y -qq certbot python3-certbot-nginx
    
    log_success "Certbot instalado: $(certbot --version 2>&1 | head -n1)"
fi

################################################################################
# PASSO 5: CONFIGURAR UFW (FIREWALL)
################################################################################

log_step 5 $TOTAL_STEPS "Configurando UFW (Firewall)"

if command -v ufw &> /dev/null; then
    log_info "Configurando regras do firewall..."
    
    # Desabilitar temporariamente
    ufw --force disable
    
    # Configurar regras padrão
    ufw default deny incoming
    ufw default allow outgoing
    
    # Permitir SSH (porta 22)
    ufw allow 22/tcp comment 'SSH'
    
    # Permitir HTTP (porta 80)
    ufw allow 80/tcp comment 'HTTP'
    
    # Permitir HTTPS (porta 443)
    ufw allow 443/tcp comment 'HTTPS'
    
    # Habilitar firewall
    ufw --force enable
    
    log_success "Firewall configurado e ativo!"
    ufw status numbered
else
    log_error "UFW não encontrado!"
    exit 1
fi

################################################################################
# PASSO 6: INSTALAR FAIL2BAN
################################################################################

log_step 6 $TOTAL_STEPS "Instalando Fail2Ban"

if command -v fail2ban-client &> /dev/null; then
    log_warning "Fail2Ban já está instalado"
else
    log_info "Instalando Fail2Ban..."
    apt-get install -y -qq fail2ban
    
    # Criar configuração personalizada
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
destemail = root@localhost
sendername = Fail2Ban

[sshd]
enabled = true
port = 22
logpath = %(sshd_log)s
backend = %(sshd_backend)s

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
    
    # Iniciar Fail2Ban
    systemctl enable fail2ban
    systemctl restart fail2ban
    
    log_success "Fail2Ban instalado e configurado!"
fi

################################################################################
# PASSO 7: CRIAR ESTRUTURA DE DIRETÓRIOS
################################################################################

log_step 7 $TOTAL_STEPS "Criando Estrutura de Diretórios"

log_info "Criando diretórios..."

mkdir -p $INSTALL_DIR
mkdir -p $DATA_DIR/{postgres,redis}
mkdir -p $BACKUP_DIR
mkdir -p $LOG_DIR
mkdir -p /etc/nginx/ssl

# Criar usuário do sistema
if id "sentinelweb" &>/dev/null; then
    log_warning "Usuário 'sentinelweb' já existe"
else
    log_info "Criando usuário do sistema 'sentinelweb'..."
    useradd -r -s /bin/bash -d $INSTALL_DIR -m sentinelweb
fi

# Ajustar permissões
chown -R sentinelweb:sentinelweb $INSTALL_DIR
chown -R sentinelweb:sentinelweb $DATA_DIR
chown -R sentinelweb:sentinelweb $BACKUP_DIR
chown -R sentinelweb:sentinelweb $LOG_DIR

chmod 750 $INSTALL_DIR
chmod 750 $DATA_DIR
chmod 750 $BACKUP_DIR
chmod 750 $LOG_DIR

log_success "Estrutura de diretórios criada!"

################################################################################
# PASSO 8: BAIXAR APLICAÇÃO DO GITHUB
################################################################################

log_step 8 $TOTAL_STEPS "Baixando Aplicação do GitHub"

GITHUB_REPO="https://github.com/GuilhermeSantiago921/sentinelweb.git"

# Verificar se o diretório já existe e tem conteúdo
if [ -d "$INSTALL_DIR" ] && [ "$(ls -A $INSTALL_DIR 2>/dev/null)" ]; then
    log_warning "Diretório $INSTALL_DIR já existe com conteúdo"
    
    # Verificar se é um repositório Git
    if [ -d "$INSTALL_DIR/.git" ]; then
        log_info "Atualizando repositório existente..."
        cd $INSTALL_DIR
        sudo -u sentinelweb git pull origin main
        log_success "Repositório atualizado!"
    else
        # Fazer backup do diretório existente
        BACKUP_NAME="$INSTALL_DIR.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "Fazendo backup do diretório existente para $BACKUP_NAME..."
        mv $INSTALL_DIR $BACKUP_NAME
        
        # Clonar repositório
        log_info "Clonando repositório do GitHub..."
        sudo -u sentinelweb git clone $GITHUB_REPO $INSTALL_DIR
        
        log_success "Repositório clonado com sucesso!"
    fi
else
    # Diretório não existe ou está vazio - clonar repositório
    log_info "Clonando repositório do GitHub: $GITHUB_REPO"
    log_info "Destino: $INSTALL_DIR"
    
    # Garantir que o diretório pai existe
    mkdir -p $(dirname $INSTALL_DIR)
    
    # Remover diretório se existir (mesmo que não esteja vazio)
    if [ -d "$INSTALL_DIR" ]; then
        log_info "Removendo diretório existente..."
        rm -rf $INSTALL_DIR
    fi
    
    # Clonar como root primeiro, depois ajustar permissões
    git clone $GITHUB_REPO $INSTALL_DIR
    
    if [ $? -eq 0 ]; then
        # Ajustar ownership para o usuário sentinelweb
        chown -R sentinelweb:sentinelweb $INSTALL_DIR
        log_success "Repositório clonado com sucesso!"
    else
        log_error "Falha ao clonar repositório do GitHub!"
        log_info "Verifique sua conexão com a internet e tente novamente."
        exit 1
    fi
fi

# Ajustar permissões
chown -R sentinelweb:sentinelweb $INSTALL_DIR
chmod 750 $INSTALL_DIR

# Verificar se arquivos essenciais existem
REQUIRED_FILES=("main.py" "docker-compose.prod.yml" "requirements.txt")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$INSTALL_DIR/$file" ]; then
        log_error "Arquivo obrigatório não encontrado: $file"
        exit 1
    fi
done

log_success "Todos os arquivos essenciais verificados!"

################################################################################
# PASSO 9: GERAR CREDENCIAIS
################################################################################

log_step 9 $TOTAL_STEPS "Gerando Credenciais de Segurança"

log_info "Gerando credenciais fortes..."

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

log_success "Credenciais geradas com sucesso!"
log_warning "As credenciais serão salvas no arquivo .env"

################################################################################
# PASSO 10: COLETAR INFORMAÇÕES DO USUÁRIO
################################################################################

log_step 10 $TOTAL_STEPS "Configuração do Domínio e Email"

echo ""
read -p "$(echo -e ${CYAN}'Digite o domínio da aplicação (ex: sentinelweb.com.br): '${NC})" APP_DOMAIN
read -p "$(echo -e ${CYAN}'Digite o email para SSL/TLS (ex: admin@sentinelweb.com.br): '${NC})" ADMIN_EMAIL

# Validar domínio
if [ -z "$APP_DOMAIN" ]; then
    log_error "Domínio não pode estar vazio!"
    exit 1
fi

# Validar email
if [ -z "$ADMIN_EMAIL" ]; then
    log_error "Email não pode estar vazio!"
    exit 1
fi

log_success "Domínio: $APP_DOMAIN"
log_success "Email: $ADMIN_EMAIL"

################################################################################
# PASSO 11: CRIAR ARQUIVO .env
################################################################################

log_step 11 $TOTAL_STEPS "Criando Arquivo de Configuração (.env)"

ENV_FILE="$INSTALL_DIR/.env"

log_info "Criando $ENV_FILE..."

cat > $ENV_FILE << EOF
# ============================================================================
# SENTINELWEB - CONFIGURAÇÃO DE PRODUÇÃO
# ============================================================================
# Gerado automaticamente em: $(date)
# ATENÇÃO: Mantenha este arquivo seguro! Não commite no Git!
# ============================================================================

# ----------------------------------------------------------------------------
# SEGURANÇA (OBRIGATÓRIO)
# ----------------------------------------------------------------------------
SECRET_KEY=$SECRET_KEY

# ----------------------------------------------------------------------------
# BANCO DE DADOS - POSTGRESQL
# ----------------------------------------------------------------------------
POSTGRES_USER=sentinelweb
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=sentinelweb
POSTGRES_HOST=db
POSTGRES_PORT=5432

DATABASE_URL=postgresql://sentinelweb:$POSTGRES_PASSWORD@db:5432/sentinelweb

# ----------------------------------------------------------------------------
# REDIS
# ----------------------------------------------------------------------------
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_URL=redis://:$REDIS_PASSWORD@redis:6379/0

# ----------------------------------------------------------------------------
# APLICAÇÃO
# ----------------------------------------------------------------------------
APP_NAME=SentinelWeb
APP_DOMAIN=$APP_DOMAIN
APP_URL=https://$APP_DOMAIN
ENVIRONMENT=production

# ----------------------------------------------------------------------------
# ASAAS (PAGAMENTOS) - OPCIONAL
# ----------------------------------------------------------------------------
# ASAAS_API_KEY=seu_api_key_de_producao_aqui
# ASAAS_API_URL=https://api.asaas.com/v3

# ----------------------------------------------------------------------------
# TELEGRAM (ALERTAS) - OPCIONAL
# ----------------------------------------------------------------------------
# TELEGRAM_BOT_TOKEN=seu_bot_token_aqui
# TELEGRAM_CHAT_ID=seu_chat_id_aqui

# ----------------------------------------------------------------------------
# EMAIL (SMTP) - OPCIONAL
# ----------------------------------------------------------------------------
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=seu_email@gmail.com
# SMTP_PASSWORD=sua_senha_app
# SMTP_FROM=noreply@$APP_DOMAIN

# ----------------------------------------------------------------------------
# GOOGLE PAGESPEED - OPCIONAL
# ----------------------------------------------------------------------------
# GOOGLE_PAGESPEED_API_KEY=sua_api_key_aqui

# ----------------------------------------------------------------------------
# CONFIGURAÇÕES AVANÇADAS
# ----------------------------------------------------------------------------
LOG_LEVEL=INFO
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MAX_SITES_PER_USER=10
CHECK_INTERVAL_MINUTES=5

# ----------------------------------------------------------------------------
# WORKERS
# ----------------------------------------------------------------------------
UVICORN_WORKERS=4
CELERY_CONCURRENCY=4
EOF

# Ajustar permissões
chown sentinelweb:sentinelweb $ENV_FILE
chmod 600 $ENV_FILE

log_success "Arquivo .env criado: $ENV_FILE"
log_warning "IMPORTANTE: Edite o .env para adicionar chaves opcionais (Asaas, Telegram, etc)"

################################################################################
# PASSO 12: GERAR DHPARAM
################################################################################

log_step 12 $TOTAL_STEPS "Gerando Parâmetros Diffie-Hellman (2048 bits)"

DHPARAM_FILE="/etc/nginx/ssl/dhparam.pem"

if [ -f "$DHPARAM_FILE" ]; then
    log_warning "DH Param já existe: $DHPARAM_FILE"
else
    log_info "Gerando dhparam.pem (isso pode demorar alguns minutos)..."
    openssl dhparam -out $DHPARAM_FILE 2048
    chmod 644 $DHPARAM_FILE
    log_success "DH Param gerado: $DHPARAM_FILE"
fi

################################################################################
# PASSO 13: CONFIGURAR NGINX (HTTP TEMPORÁRIO)
################################################################################

log_step 13 $TOTAL_STEPS "Configurando Nginx (HTTP temporário)"

NGINX_CONFIG="/etc/nginx/sites-available/sentinelweb"
NGINX_ENABLED="/etc/nginx/sites-enabled/sentinelweb"

log_info "Criando configuração temporária HTTP (para obter SSL)..."

# Backup da configuração antiga se existir
if [ -f "$NGINX_CONFIG" ]; then
    cp $NGINX_CONFIG ${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)
fi

# Criar configuração temporária HTTP-only para Certbot
cat > $NGINX_CONFIG << EOF
# Configuração temporária para obtenção de certificado SSL
server {
    listen 80;
    listen [::]:80;
    server_name $APP_DOMAIN www.$APP_DOMAIN;
    
    # Certbot ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        allow all;
    }
    
    # Temporariamente permite acesso HTTP
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

log_success "Configuração HTTP temporária criada!"

# Habilitar site
if [ -L "$NGINX_ENABLED" ]; then
    rm $NGINX_ENABLED
fi
ln -s $NGINX_CONFIG $NGINX_ENABLED

# Remover site padrão
if [ -L "/etc/nginx/sites-enabled/default" ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Testar configuração
log_info "Testando configuração do Nginx..."
if nginx -t; then
    log_success "Configuração do Nginx válida!"
    systemctl reload nginx
    log_success "Nginx rodando em modo HTTP temporário"
else
    log_error "Erro na configuração do Nginx!"
    exit 1
fi

################################################################################
# PASSO 14: OBTER CERTIFICADO SSL
################################################################################

log_step 14 $TOTAL_STEPS "Obtendo Certificado SSL (Let's Encrypt)"

# Criar diretório webroot
mkdir -p /var/www/certbot
chown -R www-data:www-data /var/www/certbot

log_info "Obtendo certificado SSL para $APP_DOMAIN..."
log_warning "Certifique-se de que o domínio aponta para este servidor!"

SSL_OBTAINED=false

if confirm "Deseja obter o certificado SSL agora?"; then
    if certbot certonly \
        --webroot \
        -w /var/www/certbot \
        --non-interactive \
        --agree-tos \
        --email "$ADMIN_EMAIL" \
        -d "$APP_DOMAIN" \
        -d "www.$APP_DOMAIN"; then
        
        log_success "Certificado SSL obtido com sucesso!"
        SSL_OBTAINED=true
        
        # Configurar renovação automática
        log_info "Configurando renovação automática..."
        (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
        
        log_success "Renovação automática configurada (3AM diariamente)"
    else
        log_error "Falha ao obter certificado SSL!"
        log_warning "Você pode tentar manualmente depois com:"
        log_warning "  certbot certonly --webroot -w /var/www/certbot -d $APP_DOMAIN -d www.$APP_DOMAIN"
        SSL_OBTAINED=false
    fi
else
    log_warning "Certificado SSL NÃO obtido."
    log_info "Execute manualmente: certbot certonly --webroot -w /var/www/certbot -d $APP_DOMAIN"
    SSL_OBTAINED=false
fi

################################################################################
# PASSO 14.5: CONFIGURAR NGINX COM SSL (SE OBTIDO)
################################################################################

if [ "$SSL_OBTAINED" = true ]; then
    log_info "Configurando Nginx com SSL/HTTPS..."
    
    # Verificar se o template existe
    if [ -f "$INSTALL_DIR/nginx-sentinelweb.conf" ]; then
        # Copiar configuração completa com SSL
        cp $INSTALL_DIR/nginx-sentinelweb.conf $NGINX_CONFIG
        
        # Substituir domínio
        sed -i "s/seudominio\.com\.br/$APP_DOMAIN/g" $NGINX_CONFIG
        sed -i "s/seu-email@dominio\.com\.br/$ADMIN_EMAIL/g" $NGINX_CONFIG
        
        # Testar configuração
        log_info "Testando configuração HTTPS do Nginx..."
        if nginx -t; then
            systemctl reload nginx
            log_success "Nginx configurado com SSL/HTTPS!"
            log_success "Acesse: https://$APP_DOMAIN"
        else
            log_error "Erro na configuração HTTPS do Nginx!"
            log_warning "Mantendo configuração HTTP temporária"
        fi
    else
        log_warning "Template nginx-sentinelweb.conf não encontrado!"
        log_warning "Mantendo configuração HTTP temporária"
    fi
else
    log_warning "Nginx permanecerá em modo HTTP até que o SSL seja obtido"
    log_info "Após obter SSL, reconfigure com:"
    log_info "  cp $INSTALL_DIR/nginx-sentinelweb.conf $NGINX_CONFIG"
    log_info "  sed -i 's/seudominio\.com\.br/$APP_DOMAIN/g' $NGINX_CONFIG"
    log_info "  nginx -t && systemctl reload nginx"
fi

################################################################################
# PASSO 15: CONSTRUIR IMAGENS DOCKER
################################################################################

log_step 15 $TOTAL_STEPS "Construindo Imagens Docker"

cd $INSTALL_DIR

log_info "Construindo imagens Docker (isso pode demorar)..."

if sudo -u sentinelweb docker compose -f docker-compose.prod.yml build; then
    log_success "Imagens Docker construídas!"
else
    log_error "Falha ao construir imagens Docker!"
    exit 1
fi

################################################################################
# PASSO 16: INICIAR CONTAINERS
################################################################################

log_step 16 $TOTAL_STEPS "Iniciando Containers"

log_info "Iniciando containers em background..."

if sudo -u sentinelweb docker compose -f docker-compose.prod.yml up -d; then
    log_success "Containers iniciados!"
    
    # Aguardar containers ficarem saudáveis
    log_info "Aguardando containers ficarem saudáveis (30s)..."
    sleep 30
    
    # Mostrar status
    sudo -u sentinelweb docker compose -f docker-compose.prod.yml ps
else
    log_error "Falha ao iniciar containers!"
    exit 1
fi

################################################################################
# PASSO 17: MIGRAR BANCO DE DADOS
################################################################################

log_step 17 $TOTAL_STEPS "Migrando Banco de Dados"

if [ -f "$INSTALL_DIR/sentinelweb.db" ]; then
    log_info "SQLite detectado - migrando para PostgreSQL..."
    
    if [ -f "$INSTALL_DIR/migrate_to_postgres.py" ]; then
        if sudo -u sentinelweb docker compose -f docker-compose.prod.yml exec -T web python migrate_to_postgres.py; then
            log_success "Migração concluída!"
            
            # Backup do SQLite
            cp $INSTALL_DIR/sentinelweb.db $BACKUP_DIR/sentinelweb.db.backup.$(date +%Y%m%d_%H%M%S)
            log_success "Backup do SQLite criado em $BACKUP_DIR"
        else
            log_error "Falha na migração!"
            exit 1
        fi
    else
        log_warning "Script de migração não encontrado - pulando..."
    fi
else
    log_info "Nenhum banco SQLite encontrado - criando banco PostgreSQL..."
    
    # Criar tabelas
    sudo -u sentinelweb docker compose -f docker-compose.prod.yml exec -T web python -c "
from database import engine, Base
from models import User, Site, SiteCheck, HeartbeatCheck, HeartbeatPing, Payment, SystemConfig
Base.metadata.create_all(bind=engine)
print('Tabelas criadas com sucesso!')
"
    
    log_success "Banco de dados inicializado!"
fi

################################################################################
# PASSO 18: CRIAR SUPERUSUÁRIO
################################################################################

log_step 18 $TOTAL_STEPS "Criar Superusuário"

echo ""
if confirm "Deseja criar um superusuário agora?"; then
    log_info "Criando superusuário..."
    
    sudo -u sentinelweb docker compose -f docker-compose.prod.yml exec web python create_superuser.py
    
    log_success "Superusuário criado!"
else
    log_warning "Superusuário NÃO criado."
    log_info "Execute manualmente: docker compose -f docker-compose.prod.yml exec web python create_superuser.py"
fi

################################################################################
# PASSO 19: CONFIGURAR BACKUPS AUTOMÁTICOS
################################################################################

log_step 19 $TOTAL_STEPS "Configurando Backups Automáticos"

BACKUP_SCRIPT="$INSTALL_DIR/backup.sh"

log_info "Criando script de backup..."

cat > $BACKUP_SCRIPT << 'EOF'
#!/bin/bash
# Backup automático do SentinelWeb

BACKUP_DIR="/var/backups/sentinelweb"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do PostgreSQL
docker exec sentinelweb_db_prod pg_dump -U sentinelweb sentinelweb | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Backup dos arquivos da aplicação
tar -czf $BACKUP_DIR/app_$DATE.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    /opt/sentinelweb

# Remover backups antigos
find $BACKUP_DIR -name "postgres_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "app_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup concluído: $BACKUP_DIR/postgres_$DATE.sql.gz"
EOF

chmod +x $BACKUP_SCRIPT
chown sentinelweb:sentinelweb $BACKUP_SCRIPT

# Adicionar ao crontab do root
log_info "Agendando backup diário (2AM)..."
(crontab -l 2>/dev/null | grep -v "backup.sh"; echo "0 2 * * * $BACKUP_SCRIPT >> $LOG_DIR/backup.log 2>&1") | crontab -

log_success "Backups automáticos configurados!"
log_info "Backup diário às 2AM - Retenção: 30 dias"

################################################################################
# PASSO 20: VALIDAÇÃO FINAL
################################################################################

log_step 20 $TOTAL_STEPS "Validação Final"

log_info "Verificando serviços..."

# Verificar Docker
if systemctl is-active --quiet docker; then
    log_success "Docker: ATIVO"
else
    log_error "Docker: INATIVO"
fi

# Verificar Nginx
if systemctl is-active --quiet nginx; then
    log_success "Nginx: ATIVO"
else
    log_error "Nginx: INATIVO"
fi

# Verificar Fail2Ban
if systemctl is-active --quiet fail2ban; then
    log_success "Fail2Ban: ATIVO"
else
    log_error "Fail2Ban: INATIVO"
fi

# Verificar Containers
log_info "Status dos containers:"
sudo -u sentinelweb docker compose -f docker-compose.prod.yml ps

# Verificar endpoint de saúde
log_info "Testando endpoint de saúde..."
sleep 5
if curl -s http://localhost:8000/health | jq . > /dev/null 2>&1; then
    log_success "Endpoint /health: FUNCIONANDO"
    curl -s http://localhost:8000/health | jq .
else
    log_warning "Endpoint /health: NÃO RESPONDENDO (pode demorar mais alguns segundos)"
fi

################################################################################
# RESUMO FINAL
################################################################################

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}                 INSTALAÇÃO CONCLUÍDA!                ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}🎉 SENTINELWEB INSTALADO COM SUCESSO! 🎉${NC}"
echo ""
echo -e "${YELLOW}📍 INFORMAÇÕES IMPORTANTES:${NC}"
echo ""
echo -e "   ${BLUE}Domínio:${NC} https://$APP_DOMAIN"
echo -e "   ${BLUE}Diretório:${NC} $INSTALL_DIR"
echo -e "   ${BLUE}Dados:${NC} $DATA_DIR"
echo -e "   ${BLUE}Backups:${NC} $BACKUP_DIR"
echo -e "   ${BLUE}Logs:${NC} $LOG_DIR"
echo ""
echo -e "${YELLOW}🔐 CREDENCIAIS GERADAS:${NC}"
echo ""
echo -e "   ${BLUE}SECRET_KEY:${NC} $SECRET_KEY"
echo -e "   ${BLUE}POSTGRES_PASSWORD:${NC} $POSTGRES_PASSWORD"
echo -e "   ${BLUE}REDIS_PASSWORD:${NC} $REDIS_PASSWORD"
echo ""
echo -e "   ${RED}⚠️  GUARDE ESTAS CREDENCIAIS EM LOCAL SEGURO!${NC}"
echo -e "   ${RED}⚠️  Elas estão salvas em: $ENV_FILE${NC}"
echo ""
echo -e "${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo ""
echo -e "   1️⃣  Edite o arquivo .env para adicionar chaves opcionais:"
echo -e "      ${CYAN}sudo nano $ENV_FILE${NC}"
echo ""
echo -e "   2️⃣  Se ainda não criou superusuário, execute:"
echo -e "      ${CYAN}cd $INSTALL_DIR${NC}"
echo -e "      ${CYAN}docker compose -f docker-compose.prod.yml exec web python create_superuser.py${NC}"
echo ""
echo -e "   3️⃣  Acesse sua aplicação:"
echo -e "      ${CYAN}https://$APP_DOMAIN${NC}"
echo ""
echo -e "   4️⃣  Verifique os logs:"
echo -e "      ${CYAN}docker compose -f docker-compose.prod.yml logs -f${NC}"
echo ""
echo -e "${YELLOW}🛠️  COMANDOS ÚTEIS:${NC}"
echo ""
echo -e "   ${BLUE}Ver status:${NC}"
echo -e "      ${CYAN}docker compose -f docker-compose.prod.yml ps${NC}"
echo ""
echo -e "   ${BLUE}Ver logs:${NC}"
echo -e "      ${CYAN}docker compose -f docker-compose.prod.yml logs -f [service]${NC}"
echo ""
echo -e "   ${BLUE}Reiniciar:${NC}"
echo -e "      ${CYAN}docker compose -f docker-compose.prod.yml restart${NC}"
echo ""
echo -e "   ${BLUE}Parar:${NC}"
echo -e "      ${CYAN}docker compose -f docker-compose.prod.yml stop${NC}"
echo ""
echo -e "   ${BLUE}Iniciar:${NC}"
echo -e "      ${CYAN}docker compose -f docker-compose.prod.yml start${NC}"
echo ""
echo -e "   ${BLUE}Backup manual:${NC}"
echo -e "      ${CYAN}$BACKUP_SCRIPT${NC}"
echo ""
echo -e "${YELLOW}📚 DOCUMENTAÇÃO:${NC}"
echo ""
echo -e "   • SECURITY_AUDIT.md - Auditoria de segurança"
echo -e "   • SECURITY_CHECKLIST.md - Checklist de 96 itens"
echo -e "   • DEPLOY_GUIDE.md - Guia de deploy completo"
echo -e "   • PRODUCTION_READY.md - Resumo executivo"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}Obrigado por usar SentinelWeb! 🚀${NC}"
echo ""

# Salvar resumo em arquivo
SUMMARY_FILE="$INSTALL_DIR/INSTALLATION_SUMMARY.txt"
cat > $SUMMARY_FILE << EOF
================================================================================
SENTINELWEB - RESUMO DA INSTALAÇÃO
================================================================================
Data: $(date)
Servidor: $(hostname)
IP: $(hostname -I | awk '{print $1}')
Sistema: $(lsb_release -ds)

DOMÍNIO
-------
Domínio: $APP_DOMAIN
URL: https://$APP_DOMAIN
Email Admin: $ADMIN_EMAIL

DIRETÓRIOS
----------
Instalação: $INSTALL_DIR
Dados: $DATA_DIR
Backups: $BACKUP_DIR
Logs: $LOG_DIR

CREDENCIAIS
-----------
SECRET_KEY: $SECRET_KEY
POSTGRES_PASSWORD: $POSTGRES_PASSWORD
REDIS_PASSWORD: $REDIS_PASSWORD

⚠️  IMPORTANTE: Guarde estas informações em local seguro!

SERVIÇOS INSTALADOS
-------------------
✓ Docker $(docker --version)
✓ Docker Compose $(docker compose version)
✓ Nginx $(nginx -v 2>&1)
✓ Certbot $(certbot --version 2>&1 | head -n1)
✓ UFW (Firewall)
✓ Fail2Ban

BACKUPS
-------
Backup automático: Diário às 2AM
Retenção: 30 dias
Script: $BACKUP_SCRIPT

PORTAS
------
22/tcp - SSH
80/tcp - HTTP (redirect para HTTPS)
443/tcp - HTTPS

COMANDOS ÚTEIS
--------------
cd $INSTALL_DIR
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml restart

SUPORTE
-------
Documentação completa em:
- SECURITY_AUDIT.md
- SECURITY_CHECKLIST.md
- DEPLOY_GUIDE.md
- PRODUCTION_READY.md

================================================================================
EOF

chown sentinelweb:sentinelweb $SUMMARY_FILE
chmod 600 $SUMMARY_FILE

log_success "Resumo salvo em: $SUMMARY_FILE"

exit 0
