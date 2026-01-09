# 🚀 GUIA COMPLETO DE DEPLOY - SENTINELWEB PRODUÇÃO

**Versão:** 1.0.0  
**Data:** 08/01/2026  
**Ambiente:** VPS Hostinger | Ubuntu 22.04 LTS  
**Infraestrutura:** PostgreSQL + Redis + Docker + Nginx

---

## 📋 ÍNDICE

1. [Pré-requisitos](#pré-requisitos)
2. [Preparação do Servidor](#preparação-do-servidor)
3. [Configuração de Variáveis de Ambiente](#configuração-de-variáveis-de-ambiente)
4. [Deploy Automatizado](#deploy-automatizado)
5. [Migração de Dados](#migração-de-dados)
6. [Verificação e Testes](#verificação-e-testes)
7. [Monitoramento](#monitoramento)
8. [Backups](#backups)
9. [Troubleshooting](#troubleshooting)
10. [Rollback](#rollback)

---

## 🎯 PRÉ-REQUISITOS

### Servidor VPS
- **OS:** Ubuntu 22.04 LTS (recomendado)
- **RAM:** Mínimo 2GB | Recomendado 4GB+
- **CPU:** 2+ cores
- **Disco:** 50GB SSD
- **Rede:** 100+ Mbps

### Acesso
- ✅ Acesso SSH como root ou sudo
- ✅ Domínio configurado apontando para o IP do servidor
- ✅ Portas 22, 80, 443 liberadas

### Credenciais Necessárias
- 📧 Email para certificado SSL
- 🔑 Chaves de API (Asaas, Telegram Bot)
- 💾 Backup do banco SQLite (se migrar dados)

---

## 🔧 PREPARAÇÃO DO SERVIDOR

### 1. Conectar ao Servidor

```bash
ssh root@seu-ip-vps
```

### 2. Atualizar Sistema

```bash
apt update && apt upgrade -y
apt autoremove -y
```

### 3. Configurar Timezone

```bash
timedatectl set-timezone America/Sao_Paulo
```

### 4. Configurar Hostname

```bash
hostnamectl set-hostname sentinelweb
echo "127.0.0.1 sentinelweb" >> /etc/hosts
```

---

## ⚙️ CONFIGURAÇÃO DE VARIÁVEIS DE AMBIENTE

### 1. Baixar o Código

```bash
# Opção A: Upload via SCP/SFTP
# Copie todos os arquivos para /opt/sentinelweb

# Opção B: Git Clone (se usar repositório)
cd /opt
git clone https://github.com/seu-usuario/sentinelweb.git
cd sentinelweb
```

### 2. Criar Arquivo .env

```bash
cd /opt/sentinelweb
cp .env.production.example .env
nano .env
```

### 3. Gerar Credenciais Seguras

**SECRET_KEY (64 bytes):**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

**POSTGRES_PASSWORD (32 bytes):**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**REDIS_PASSWORD (32 bytes):**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Configurar .env (Exemplo)

```bash
# ============================================
# CONFIGURAÇÕES DE APLICAÇÃO
# ============================================
SECRET_KEY=sua_secret_key_gerada_64_bytes
DATABASE_URL=postgresql://sentinelweb_user:SUA_SENHA_POSTGRES@db:5432/sentinelweb_prod

# ============================================
# BANCO DE DADOS
# ============================================
POSTGRES_USER=sentinelweb_user
POSTGRES_PASSWORD=SUA_SENHA_POSTGRES
POSTGRES_DB=sentinelweb_prod

# ============================================
# REDIS
# ============================================
REDIS_PASSWORD=SUA_SENHA_REDIS

# ============================================
# DOMÍNIO
# ============================================
APP_DOMAIN=seudominio.com.br
APP_URL=https://seudominio.com.br

# ============================================
# INTEGRAÇÕES (Opcional)
# ============================================
ASAAS_API_KEY=sua_chave_asaas
ASAAS_API_URL=https://api.asaas.com/v3
TELEGRAM_BOT_TOKEN=seu_token_telegram

# ============================================
# SISTEMA
# ============================================
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 5. Proteger .env

```bash
chmod 600 .env
chown root:root .env
```

---

## 🚀 DEPLOY AUTOMATIZADO

### Executar Script de Deploy

```bash
cd /opt/sentinelweb
chmod +x deploy.sh
bash deploy.sh
```

**O script irá:**
1. ✅ Atualizar sistema operacional
2. ✅ Instalar Docker e Docker Compose
3. ✅ Configurar Firewall (UFW)
4. ✅ Instalar Nginx
5. ✅ Instalar Certbot (SSL)
6. ✅ Criar usuário da aplicação
7. ✅ Configurar diretórios
8. ✅ Obter certificado SSL
9. ✅ Construir imagens Docker
10. ✅ Iniciar containers
11. ✅ Migrar banco de dados
12. ✅ Criar superusuário
13. ✅ Configurar backups automáticos

**Tempo estimado:** 15-30 minutos

---

## 📊 MIGRAÇÃO DE DADOS

### Se Migrar do SQLite

#### 1. Backup do SQLite

```bash
# No servidor antigo
cp sentinelweb.db sentinelweb.db.backup
scp sentinelweb.db root@novo-servidor:/opt/sentinelweb/
```

#### 2. Executar Migração

```bash
cd /opt/sentinelweb
docker compose -f docker-compose.prod.yml exec web python migrate_to_postgres.py
```

#### 3. Verificar Migração

```bash
# Acessar PostgreSQL
docker compose -f docker-compose.prod.yml exec db psql -U sentinelweb_user sentinelweb_prod

# Verificar tabelas
\dt

# Contar registros
SELECT 
    'users' as table, COUNT(*) as count FROM users
UNION ALL
SELECT 'sites', COUNT(*) FROM sites
UNION ALL
SELECT 'site_checks', COUNT(*) FROM site_checks
UNION ALL
SELECT 'payments', COUNT(*) FROM payments;

# Sair
\q
```

---

## ✅ VERIFICAÇÃO E TESTES

### 1. Verificar Containers

```bash
docker compose -f docker-compose.prod.yml ps
```

**Esperado:**
```
NAME                        STATUS
sentinelweb_db_prod         Up (healthy)
sentinelweb_redis_prod      Up (healthy)
sentinelweb_web_prod        Up (healthy)
sentinelweb_celery_prod     Up (healthy)
sentinelweb_beat_prod       Up
```

### 2. Verificar Logs

```bash
# Web
docker compose -f docker-compose.prod.yml logs -f web

# Celery
docker compose -f docker-compose.prod.yml logs -f celery_worker

# PostgreSQL
docker compose -f docker-compose.prod.yml logs -f db
```

### 3. Testar Health Check

```bash
curl -I https://seudominio.com.br/health
```

**Esperado:** `HTTP/2 200`

### 4. Testar Acesso Web

```bash
# Abra no navegador
https://seudominio.com.br
```

### 5. Testar Login

1. Acesse: `https://seudominio.com.br/login`
2. Use credenciais do superusuário criado
3. Deve acessar dashboard

### 6. Testar Monitoramento

1. Adicione um site
2. Aguarde 5 minutos (scan automático)
3. Verifique status na dashboard

---

## 📊 MONITORAMENTO

### Logs de Aplicação

```bash
# Logs em tempo real
tail -f /var/log/sentinelweb/*.log

# Nginx access
tail -f /var/log/nginx/sentinelweb_access.log

# Nginx errors
tail -f /var/log/nginx/sentinelweb_error.log
```

### Métricas de Containers

```bash
# Uso de recursos
docker stats

# Status de saúde
docker compose -f /opt/sentinelweb/docker-compose.prod.yml ps
```

### PostgreSQL Queries

```bash
# Top 10 queries lentas
docker compose -f /opt/sentinelweb/docker-compose.prod.yml exec db psql -U sentinelweb_user sentinelweb_prod -c "
SELECT 
    mean_exec_time::numeric(10,2) as avg_ms,
    calls,
    query
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"
```

### Celery Tasks

```bash
# Status do worker
docker compose -f /opt/sentinelweb/docker-compose.prod.yml exec celery_worker celery -A celery_app inspect active

# Estatísticas
docker compose -f /opt/sentinelweb/docker-compose.prod.yml exec celery_worker celery -A celery_app inspect stats
```

---

## 💾 BACKUPS

### Backup Manual

```bash
# Executar backup agora
/usr/local/bin/sentinelweb-backup.sh
```

### Verificar Backups Automáticos

```bash
# Listar backups
ls -lh /var/backups/sentinelweb/postgres/
ls -lh /var/backups/sentinelweb/app/
```

### Restore de Backup

```bash
# Parar aplicação
docker compose -f /opt/sentinelweb/docker-compose.prod.yml stop web celery_worker celery_beat

# Restore PostgreSQL
gunzip -c /var/backups/sentinelweb/postgres/sentinelweb_20260108_020000.sql.gz | \
docker compose -f /opt/sentinelweb/docker-compose.prod.yml exec -T db \
psql -U sentinelweb_user sentinelweb_prod

# Restore arquivos
tar -xzf /var/backups/sentinelweb/app/sentinelweb_files_20260108_020000.tar.gz -C /opt/sentinelweb

# Reiniciar aplicação
docker compose -f /opt/sentinelweb/docker-compose.prod.yml start web celery_worker celery_beat
```

---

## 🔧 TROUBLESHOOTING

### Container Não Inicia

```bash
# Ver erro detalhado
docker compose -f /opt/sentinelweb/docker-compose.prod.yml logs web

# Rebuild forçado
docker compose -f /opt/sentinelweb/docker-compose.prod.yml build --no-cache web
docker compose -f /opt/sentinelweb/docker-compose.prod.yml up -d web
```

### PostgreSQL Erro de Conexão

```bash
# Verificar se está rodando
docker compose -f /opt/sentinelweb/docker-compose.prod.yml ps db

# Testar conexão
docker compose -f /opt/sentinelweb/docker-compose.prod.yml exec db pg_isready -U sentinelweb_user

# Ver logs
docker compose -f /opt/sentinelweb/docker-compose.prod.yml logs db
```

### SSL Não Funciona

```bash
# Verificar certificado
certbot certificates

# Renovar manualmente
certbot renew --force-renewal

# Testar Nginx
nginx -t

# Recarregar Nginx
systemctl reload nginx
```

### Site Lento

```bash
# Verificar carga
htop

# Verificar disco
df -h

# Verificar memória
free -h

# Otimizar PostgreSQL
docker compose -f /opt/sentinelweb/docker-compose.prod.yml exec db psql -U sentinelweb_user sentinelweb_prod -c "VACUUM ANALYZE;"
```

### Celery Não Processa Tasks

```bash
# Verificar worker
docker compose -f /opt/sentinelweb/docker-compose.prod.yml exec celery_worker celery -A celery_app inspect ping

# Reiniciar worker
docker compose -f /opt/sentinelweb/docker-compose.prod.yml restart celery_worker

# Limpar fila
docker compose -f /opt/sentinelweb/docker-compose.prod.yml exec redis redis-cli -a $REDIS_PASSWORD FLUSHDB
```

---

## ⏮️ ROLLBACK

### Rollback Completo

```bash
# 1. Parar aplicação
docker compose -f /opt/sentinelweb/docker-compose.prod.yml down

# 2. Restore do backup
gunzip -c /var/backups/sentinelweb/postgres/BACKUP_ANTERIOR.sql.gz | \
docker compose -f /opt/sentinelweb/docker-compose.prod.yml exec -T db \
psql -U sentinelweb_user sentinelweb_prod

# 3. Restore do código
tar -xzf /var/backups/sentinelweb/app/BACKUP_ANTERIOR.tar.gz -C /opt/sentinelweb

# 4. Reiniciar
docker compose -f /opt/sentinelweb/docker-compose.prod.yml up -d
```

---

## 📞 SUPORTE

### Logs Importantes

```bash
# Compactar logs para análise
tar -czf logs_$(date +%Y%m%d).tar.gz \
    /var/log/sentinelweb/ \
    /var/log/nginx/sentinelweb_*.log
```

### Informações do Sistema

```bash
# Gerar relatório
cat > system_info.txt << EOF
=== SYSTEM INFO ===
Hostname: $(hostname)
OS: $(lsb_release -d | cut -f2)
Kernel: $(uname -r)
Uptime: $(uptime -p)
RAM: $(free -h | grep Mem | awk '{print $2}')
Disk: $(df -h / | tail -1 | awk '{print $2}')

=== DOCKER ===
$(docker --version)
$(docker compose version)

=== CONTAINERS ===
$(docker compose -f /opt/sentinelweb/docker-compose.prod.yml ps)

=== NGINX ===
$(nginx -v)

=== CERTBOT ===
$(certbot --version)

=== FIREWALL ===
$(ufw status)
EOF

cat system_info.txt
```

---

## ✅ CHECKLIST PÓS-DEPLOY

- [ ] ✅ Containers todos "healthy"
- [ ] ✅ Site acessível via HTTPS
- [ ] ✅ Certificado SSL válido (A+ no SSL Labs)
- [ ] ✅ Login funcionando
- [ ] ✅ Dashboard carregando
- [ ] ✅ Monitoramento de sites funcionando
- [ ] ✅ Celery worker processando tasks
- [ ] ✅ Alertas Telegram configurados (se usar)
- [ ] ✅ Backup automático configurado
- [ ] ✅ Logs rotativos configurados
- [ ] ✅ Firewall ativo
- [ ] ✅ Fail2Ban protegendo SSH
- [ ] ✅ Monitoramento externo configurado
- [ ] ✅ DNS configurado corretamente
- [ ] ✅ Email de teste enviado (se usar SMTP)

---

## 🎉 DEPLOY CONCLUÍDO!

Acesse: **https://seudominio.com.br**

**Próximos passos:**
1. Configure monitoramento externo (UptimeRobot, Pingdom)
2. Configure alertas de saúde
3. Adicione sites para monitorar
4. Teste todos os recursos
5. Configure integração Asaas (se usar pagamentos)
6. Convide usuários
7. Monitore métricas nos primeiros dias

---

**Documentação:** https://github.com/seu-repo/sentinelweb  
**Suporte:** support@seudominio.com.br
