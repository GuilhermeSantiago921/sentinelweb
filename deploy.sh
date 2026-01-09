#!/bin/bash
# ============================================
# SENTINELWEB - SCRIPT DE DEPLOY PARA PRODUÇÃO
# ============================================
# Deploy automatizado para VPS Hostinger
# Sistema: Ubuntu 22.04 LTS
# Autor: DevOps Team
# Data: 08/01/2026

set -e  # Exit on error
set -u  # Exit on undefined variable

# ============================================
# CORES PARA OUTPUT
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Este script deve ser executado como root!"
        print_info "Use: sudo bash deploy.sh"
        exit 1
    fi
}

# ============================================
# VARIÁVEIS DE CONFIGURAÇÃO
# ============================================

APP_NAME="sentinelweb"
APP_DIR="/opt/sentinelweb"
APP_USER="sentinelweb"
DOMAIN="${DOMAIN:-seudominio.com.br}"
EMAIL="${EMAIL:-admin@seudominio.com.br}"
DATA_DIR="/var/lib/sentinelweb"
BACKUP_DIR="/var/backups/sentinelweb"
LOG_DIR="/var/log/sentinelweb"

# ============================================
# INÍCIO DO DEPLOY
# ============================================

print_header "SENTINELWEB - DEPLOY PARA PRODUÇÃO"
echo "Domínio: $DOMAIN"
echo "Email: $EMAIL"
echo "Diretório: $APP_DIR"
echo ""

read -p "Deseja continuar? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Deploy cancelado pelo usuário"
    exit 1
fi

check_root

# ============================================
# ETAPA 1: ATUALIZAÇÃO DO SISTEMA
# ============================================

print_header "ETAPA 1: Atualizando Sistema Operacional"

apt-get update
apt-get upgrade -y
apt-get autoremove -y

print_success "Sistema atualizado"

# ============================================
# ETAPA 2: INSTALAÇÃO DE DEPENDÊNCIAS
# ============================================

print_header "ETAPA 2: Instalando Dependências"

# Utilitários essenciais
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    git \
    wget \
    vim \
    htop \
    ufw \
    fail2ban \
    unattended-upgrades

print_success "Dependências instaladas"

# ============================================
# ETAPA 3: INSTALAÇÃO DO DOCKER
# ============================================

print_header "ETAPA 3: Instalando Docker"

# Remove versões antigas
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Adiciona repositório oficial do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instala Docker
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Inicia e habilita Docker
systemctl start docker
systemctl enable docker

# Testa Docker
docker --version
docker compose version

print_success "Docker instalado e configurado"

# ============================================
# ETAPA 4: CONFIGURAÇÃO DE FIREWALL (UFW)
# ============================================

print_header "ETAPA 4: Configurando Firewall"

# Reseta UFW (caso já esteja configurado)
ufw --force reset

# Regras padrão
ufw default deny incoming
ufw default allow outgoing

# Permite SSH (porta 22) - CRÍTICO!
ufw allow 22/tcp comment 'SSH'

# Permite HTTP (porta 80) - Certbot
ufw allow 80/tcp comment 'HTTP'

# Permite HTTPS (porta 443)
ufw allow 443/tcp comment 'HTTPS'

# Ativa firewall
ufw --force enable

# Mostra status
ufw status verbose

print_success "Firewall configurado"
print_warning "Portas liberadas: 22 (SSH), 80 (HTTP), 443 (HTTPS)"

# ============================================
# ETAPA 5: CONFIGURAÇÃO DO FAIL2BAN
# ============================================

print_header "ETAPA 5: Configurando Fail2Ban (proteção contra brute-force)"

# Cria configuração para SSH
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
destemail = $EMAIL
sendername = Fail2Ban
action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/sentinelweb_error.log
maxretry = 5

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/sentinelweb_error.log
maxretry = 10
EOF

systemctl enable fail2ban
systemctl restart fail2ban

print_success "Fail2Ban configurado"

# ============================================
# ETAPA 6: INSTALAÇÃO DO NGINX
# ============================================

print_header "ETAPA 6: Instalando Nginx"

apt-get install -y nginx nginx-extras

# Remove configuração padrão
rm -f /etc/nginx/sites-enabled/default

# Gera parâmetros Diffie-Hellman (pode demorar)
print_info "Gerando parâmetros DH (pode levar alguns minutos)..."
openssl dhparam -out /etc/nginx/dhparam.pem 2048

systemctl start nginx
systemctl enable nginx

print_success "Nginx instalado"

# ============================================
# ETAPA 7: INSTALAÇÃO DO CERTBOT (Let's Encrypt)
# ============================================

print_header "ETAPA 7: Instalando Certbot (SSL/TLS)"

apt-get install -y certbot python3-certbot-nginx

print_success "Certbot instalado"

# ============================================
# ETAPA 8: CRIAÇÃO DE USUÁRIO PARA A APLICAÇÃO
# ============================================

print_header "ETAPA 8: Criando Usuário da Aplicação"

# Cria usuário sem senha e sem shell interativo
if ! id -u "$APP_USER" >/dev/null 2>&1; then
    useradd -r -s /bin/false -d "$APP_DIR" -c "SentinelWeb Service Account" "$APP_USER"
    print_success "Usuário $APP_USER criado"
else
    print_info "Usuário $APP_USER já existe"
fi

# Adiciona ao grupo Docker
usermod -aG docker "$APP_USER"

print_success "Usuário configurado"

# ============================================
# ETAPA 9: CRIAÇÃO DE DIRETÓRIOS
# ============================================

print_header "ETAPA 9: Criando Diretórios"

mkdir -p "$APP_DIR"
mkdir -p "$DATA_DIR"/{postgres,redis}
mkdir -p "$BACKUP_DIR"/{postgres,app}
mkdir -p "$LOG_DIR"
mkdir -p /var/www/certbot
mkdir -p "$APP_DIR"/logs

# Define permissões
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
chown -R "$APP_USER":"$APP_USER" "$DATA_DIR"
chown -R "$APP_USER":"$APP_USER" "$BACKUP_DIR"
chown -R "$APP_USER":"$APP_USER" "$LOG_DIR"

chmod -R 750 "$APP_DIR"
chmod -R 750 "$DATA_DIR"
chmod -R 750 "$BACKUP_DIR"
chmod -R 750 "$LOG_DIR"

print_success "Diretórios criados e permissões configuradas"

# ============================================
# ETAPA 10: CLONE DO REPOSITÓRIO
# ============================================

print_header "ETAPA 10: Deploy da Aplicação"

print_info "Cole o código da aplicação em $APP_DIR"
print_info "Ou execute: git clone <seu-repo> $APP_DIR"

read -p "Aplicação já está em $APP_DIR? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Copie a aplicação para $APP_DIR e execute o script novamente"
    exit 1
fi

# Verifica se os arquivos necessários existem
if [ ! -f "$APP_DIR/docker-compose.prod.yml" ]; then
    print_error "docker-compose.prod.yml não encontrado em $APP_DIR"
    exit 1
fi

if [ ! -f "$APP_DIR/Dockerfile.prod" ]; then
    print_error "Dockerfile.prod não encontrado em $APP_DIR"
    exit 1
fi

print_success "Aplicação encontrada"

# ============================================
# ETAPA 11: CONFIGURAÇÃO DO .ENV
# ============================================

print_header "ETAPA 11: Configurando Variáveis de Ambiente"

if [ ! -f "$APP_DIR/.env" ]; then
    print_warning ".env não encontrado, criando a partir do exemplo..."
    
    if [ -f "$APP_DIR/.env.production.example" ]; then
        cp "$APP_DIR/.env.production.example" "$APP_DIR/.env"
        
        print_warning "ATENÇÃO: Configure o arquivo .env antes de continuar!"
        print_info "Edite: $APP_DIR/.env"
        print_info ""
        print_info "Variáveis OBRIGATÓRIAS:"
        echo "  - SECRET_KEY (gere com: python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
        echo "  - DATABASE_URL"
        echo "  - POSTGRES_USER"
        echo "  - POSTGRES_PASSWORD (gere com: python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
        echo "  - POSTGRES_DB"
        echo "  - REDIS_PASSWORD (gere com: python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
        echo "  - APP_DOMAIN=$DOMAIN"
        echo "  - APP_URL=https://$DOMAIN"
        echo ""
        
        read -p "Pressione ENTER após configurar o .env" -r
    else
        print_error ".env.production.example não encontrado"
        exit 1
    fi
fi

# Verifica se SECRET_KEY foi configurada
if grep -q "GERAR_UMA_CHAVE_FORTE_AQUI" "$APP_DIR/.env"; then
    print_error "SECRET_KEY não foi configurada no .env!"
    exit 1
fi

print_success ".env configurado"

# Define permissões seguras para .env
chmod 600 "$APP_DIR/.env"
chown "$APP_USER":"$APP_USER" "$APP_DIR/.env"

# ============================================
# ETAPA 12: CONFIGURAÇÃO DO NGINX
# ============================================

print_header "ETAPA 12: Configurando Nginx"

# Copia configuração do Nginx
if [ -f "$APP_DIR/nginx-sentinelweb.conf" ]; then
    # Substitui o domínio placeholder
    sed "s/seudominio.com.br/$DOMAIN/g" "$APP_DIR/nginx-sentinelweb.conf" > /etc/nginx/sites-available/sentinelweb.conf
    
    # Ativa o site
    ln -sf /etc/nginx/sites-available/sentinelweb.conf /etc/nginx/sites-enabled/
    
    # Testa configuração
    nginx -t
    
    print_success "Nginx configurado"
else
    print_error "nginx-sentinelweb.conf não encontrado"
    exit 1
fi

# ============================================
# ETAPA 13: OBTENÇÃO DE CERTIFICADO SSL
# ============================================

print_header "ETAPA 13: Obtendo Certificado SSL (Let's Encrypt)"

print_info "Obtendo certificado para $DOMAIN..."

# Temporariamente, configura Nginx básico para Certbot
cat > /etc/nginx/sites-available/sentinelweb-temp.conf <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 'SentinelWeb - Configuração em andamento';
        add_header Content-Type text/plain;
    }
}
EOF

ln -sf /etc/nginx/sites-available/sentinelweb-temp.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/sentinelweb.conf
nginx -t && systemctl reload nginx

# Obtém certificado
certbot certonly --webroot -w /var/www/certbot \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    --expand

if [ $? -eq 0 ]; then
    print_success "Certificado SSL obtido com sucesso"
    
    # Restaura configuração completa do Nginx
    rm -f /etc/nginx/sites-enabled/sentinelweb-temp.conf
    ln -sf /etc/nginx/sites-available/sentinelweb.conf /etc/nginx/sites-enabled/
    
    # Testa e recarrega
    nginx -t && systemctl reload nginx
    
    print_success "Nginx configurado com SSL"
else
    print_error "Falha ao obter certificado SSL"
    print_info "Configure manualmente: certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi

# Configura renovação automática
systemctl enable certbot.timer
systemctl start certbot.timer

# ============================================
# ETAPA 14: BUILD E START DA APLICAÇÃO
# ============================================

print_header "ETAPA 14: Construindo e Iniciando Aplicação"

cd "$APP_DIR"

# Build das imagens
print_info "Construindo imagens Docker (pode demorar alguns minutos)..."
docker compose -f docker-compose.prod.yml build --no-cache

# Inicia os containers
print_info "Iniciando containers..."
docker compose -f docker-compose.prod.yml up -d

# Aguarda containers ficarem prontos
print_info "Aguardando containers iniciarem..."
sleep 10

# Verifica status
docker compose -f docker-compose.prod.yml ps

print_success "Aplicação iniciada"

# ============================================
# ETAPA 15: MIGRAÇÃO DO BANCO DE DADOS
# ============================================

print_header "ETAPA 15: Migrando Banco de Dados"

print_info "Aguardando PostgreSQL ficar pronto..."
sleep 15

# Executa migrações
print_info "Criando tabelas no PostgreSQL..."
docker compose -f docker-compose.prod.yml exec -T web python -c "
from database import engine, Base
from models import *
Base.metadata.create_all(bind=engine)
print('✓ Tabelas criadas com sucesso')
"

if [ $? -eq 0 ]; then
    print_success "Banco de dados migrado"
else
    print_error "Falha na migração do banco"
    print_info "Execute manualmente: docker compose -f docker-compose.prod.yml exec web python migrate_to_postgres.py"
fi

# ============================================
# ETAPA 16: CRIAÇÃO DE SUPERUSUÁRIO
# ============================================

print_header "ETAPA 16: Criando Superusuário"

print_info "Será criado um usuário administrador"
echo ""

read -p "Email do admin: " ADMIN_EMAIL
read -sp "Senha do admin: " ADMIN_PASSWORD
echo ""

docker compose -f docker-compose.prod.yml exec -T web python -c "
from database import SessionLocal
from auth import get_password_hash
from models import User

db = SessionLocal()
try:
    # Verifica se já existe
    existing = db.query(User).filter(User.email == '$ADMIN_EMAIL').first()
    if existing:
        print('⚠ Usuário já existe')
    else:
        admin = User(
            email='$ADMIN_EMAIL',
            hashed_password=get_password_hash('$ADMIN_PASSWORD'),
            is_superuser=True,
            is_active=True,
            plan_status='agency',
            company_name='Administrador'
        )
        db.add(admin)
        db.commit()
        print('✓ Superusuário criado')
except Exception as e:
    print(f'✗ Erro: {e}')
finally:
    db.close()
"

print_success "Superusuário configurado"

# ============================================
# ETAPA 17: CONFIGURAÇÃO DE BACKUPS AUTOMÁTICOS
# ============================================

print_header "ETAPA 17: Configurando Backups Automáticos"

# Script de backup
cat > /usr/local/bin/sentinelweb-backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/sentinelweb"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/sentinelweb"

# Backup PostgreSQL
docker compose -f "$APP_DIR/docker-compose.prod.yml" exec -T db \
    pg_dump -U sentinelweb_user sentinelweb_prod | \
    gzip > "$BACKUP_DIR/postgres/sentinelweb_$DATE.sql.gz"

# Backup de arquivos da aplicação
tar -czf "$BACKUP_DIR/app/sentinelweb_files_$DATE.tar.gz" \
    -C "$APP_DIR" \
    --exclude=logs \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    .env static/screenshots

# Remove backups antigos (mantém últimos 30 dias)
find "$BACKUP_DIR/postgres" -type f -name "*.sql.gz" -mtime +30 -delete
find "$BACKUP_DIR/app" -type f -name "*.tar.gz" -mtime +30 -delete

echo "✓ Backup concluído: $DATE"
EOF

chmod +x /usr/local/bin/sentinelweb-backup.sh

# Cron job para backup diário às 2AM
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/sentinelweb-backup.sh >> /var/log/sentinelweb/backup.log 2>&1") | crontab -

print_success "Backups automáticos configurados (diariamente às 2AM)"

# ============================================
# ETAPA 18: CONFIGURAÇÃO DE LOGS ROTATIVOS
# ============================================

print_header "ETAPA 18: Configurando Rotação de Logs"

cat > /etc/logrotate.d/sentinelweb <<EOF
/var/log/sentinelweb/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 sentinelweb sentinelweb
    sharedscripts
    postrotate
        docker compose -f /opt/sentinelweb/docker-compose.prod.yml restart web celery_worker > /dev/null 2>&1 || true
    endscript
}
EOF

print_success "Rotação de logs configurada"

# ============================================
# ETAPA 19: CONFIGURAÇÃO DE ATUALIZAÇÕES AUTOMÁTICAS
# ============================================

print_header "ETAPA 19: Configurando Atualizações Automáticas de Segurança"

cat > /etc/apt/apt.conf.d/50unattended-upgrades <<EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
    "\${distro_id}ESMApps:\${distro_codename}-apps-security";
    "\${distro_id}ESM:\${distro_codename}-infra-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Mail "$EMAIL";
EOF

systemctl enable unattended-upgrades
systemctl start unattended-upgrades

print_success "Atualizações automáticas configuradas"

# ============================================
# ETAPA 20: VERIFICAÇÃO FINAL
# ============================================

print_header "ETAPA 20: Verificação Final"

echo ""
print_info "Verificando serviços..."

# Verifica Docker
if systemctl is-active --quiet docker; then
    print_success "Docker: Running"
else
    print_error "Docker: Stopped"
fi

# Verifica Nginx
if systemctl is-active --quiet nginx; then
    print_success "Nginx: Running"
else
    print_error "Nginx: Stopped"
fi

# Verifica containers
echo ""
print_info "Status dos containers:"
docker compose -f "$APP_DIR/docker-compose.prod.yml" ps

# Verifica UFW
echo ""
print_info "Status do Firewall:"
ufw status numbered

# Verifica certificado SSL
echo ""
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    print_success "Certificado SSL: Instalado"
    certbot certificates
else
    print_warning "Certificado SSL: Não instalado"
fi

# ============================================
# RESUMO FINAL
# ============================================

print_header "DEPLOY CONCLUÍDO COM SUCESSO! 🎉"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  INFORMAÇÕES DO SISTEMA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🌐 URL da Aplicação:  https://$DOMAIN"
echo "  📁 Diretório:         $APP_DIR"
echo "  👤 Usuário Sistema:   $APP_USER"
echo "  📦 Dados:             $DATA_DIR"
echo "  💾 Backups:           $BACKUP_DIR"
echo "  📝 Logs:              $LOG_DIR"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CREDENCIAIS DE ACESSO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Admin Email:    $ADMIN_EMAIL"
echo "  Admin Senha:    (a que você digitou)"
echo "  Login:          https://$DOMAIN/login"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  COMANDOS ÚTEIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Ver logs da aplicação:"
echo "    docker compose -f $APP_DIR/docker-compose.prod.yml logs -f web"
echo ""
echo "  Reiniciar aplicação:"
echo "    docker compose -f $APP_DIR/docker-compose.prod.yml restart"
echo ""
echo "  Parar aplicação:"
echo "    docker compose -f $APP_DIR/docker-compose.prod.yml down"
echo ""
echo "  Iniciar aplicação:"
echo "    docker compose -f $APP_DIR/docker-compose.prod.yml up -d"
echo ""
echo "  Backup manual:"
echo "    /usr/local/bin/sentinelweb-backup.sh"
echo ""
echo "  Ver status dos containers:"
echo "    docker compose -f $APP_DIR/docker-compose.prod.yml ps"
echo ""
echo "  Acessar container:"
echo "    docker compose -f $APP_DIR/docker-compose.prod.yml exec web sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PRÓXIMOS PASSOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Acesse https://$DOMAIN e faça login"
echo "  2. Configure integração Asaas (se usar pagamentos)"
echo "  3. Configure bot do Telegram (alertas)"
echo "  4. Adicione seus primeiros sites para monitorar"
echo "  5. Teste o sistema de backups"
echo "  6. Configure monitoramento externo (UptimeRobot)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_success "Sistema em produção e operacional!"
print_info "Documentação completa: $APP_DIR/README.md"

echo ""
