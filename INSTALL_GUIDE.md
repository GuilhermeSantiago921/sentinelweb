# 🚀 GUIA DE INSTALAÇÃO AUTOMÁTICA - SENTINELWEB

## 📋 Visão Geral

O script `install.sh` automatiza **100% da instalação** do SentinelWeb em servidores Ubuntu, instalando e configurando todos os componentes necessários em apenas um comando.

---

## ✅ Requisitos

### Sistema Operacional
- **Ubuntu 20.04 LTS** ✅
- **Ubuntu 22.04 LTS** ✅ (recomendado)
- **Ubuntu 24.04 LTS** ✅

### Servidor
- **RAM:** Mínimo 2GB (recomendado 4GB)
- **CPU:** Mínimo 2 cores (recomendado 4 cores)
- **Disco:** Mínimo 20GB livres (recomendado 50GB)
- **Acesso:** Root ou sudo

### Rede
- **IP Público** com acesso SSH
- **Domínio** apontando para o servidor (A record)
- **Portas abertas:** 22, 80, 443

---

## 🎯 O Que o Script Instala

### Infraestrutura Base
- ✅ **Docker** (última versão)
- ✅ **Docker Compose** (plugin v2)
- ✅ **Nginx** (reverse proxy + rate limiting)
- ✅ **Certbot** (SSL/TLS Let's Encrypt)
- ✅ **UFW** (firewall)
- ✅ **Fail2Ban** (proteção brute force)

### Aplicação
- ✅ **PostgreSQL 15** (containerizado)
- ✅ **Redis** (cache e fila)
- ✅ **FastAPI** (4 workers Uvicorn)
- ✅ **Celery** (worker + beat)
- ✅ **SentinelWeb** (aplicação completa)

### Segurança
- ✅ Gera **SECRET_KEY** forte (64 bytes)
- ✅ Gera **senhas** fortes (32 bytes)
- ✅ Configura **firewall** (UFW)
- ✅ Instala **Fail2Ban**
- ✅ Obtém **certificado SSL**
- ✅ Configura **headers de segurança**
- ✅ Aplica **rate limiting**

### Automação
- ✅ **Backup diário** automático (2AM)
- ✅ **Renovação SSL** automática
- ✅ **Healthchecks** em todos os containers
- ✅ **Logs estruturados**

---

## 📥 Preparação

### 1. Acesse seu Servidor VPS

```bash
ssh root@SEU_IP_DO_SERVIDOR
```

### 2. Baixe o Script de Instalação

```bash
# Baixar o script diretamente do GitHub
curl -fsSL https://raw.githubusercontent.com/GuilhermeSantiago921/sentinelweb/main/install.sh -o install.sh

# Tornar executável
chmod +x install.sh
```

**Ou via wget:**
```bash
wget https://raw.githubusercontent.com/GuilhermeSantiago921/sentinelweb/main/install.sh
chmod +x install.sh
```

---

## 🚀 Instalação

### Executar o Script

```bash
sudo bash install.sh
```

**⚠️ IMPORTANTE:** O script irá:
- Baixar automaticamente o código do GitHub
- Instalar todas as dependências
- Configurar tudo em `/opt/sentinelweb`
- Não é necessário clonar o repositório manualmente!

### Durante a Instalação

O script vai solicitar algumas informações:

#### 1. Confirmação Inicial
```
Deseja continuar com a instalação? (s/N):
```
Digite: **s** e pressione Enter

#### 2. Domínio da Aplicação
```
Digite o domínio da aplicação (ex: sentinelweb.com.br):
```
Digite seu domínio: **seudominio.com.br**

#### 3. Email para SSL
```
Digite o email para SSL/TLS (ex: admin@sentinelweb.com.br):
```
Digite seu email: **seu@email.com**

#### 4. Obter Certificado SSL
```
Deseja obter o certificado SSL agora? (s/N):
```
Digite: **s** (recomendado)

**⚠️ IMPORTANTE:** Seu domínio DEVE estar apontando para o servidor antes deste passo!

#### 5. Criar Superusuário
```
Deseja criar um superusuário agora? (s/N):
```
Digite: **s**

Então forneça:
- Nome completo
- Email
- Senha (será hashada com bcrypt)

---

## ⏱️ Tempo de Instalação

| Etapa | Tempo Estimado |
|-------|----------------|
| Atualização do sistema | 2-5 min |
| Instalação de pacotes | 3-8 min |
| Geração DH Param | 2-5 min |
| Build Docker | 5-10 min |
| Obtenção SSL | 1-2 min |
| Migração DB | 1-2 min |
| **TOTAL** | **15-30 min** |

---

## 📊 Progresso do Script

O script tem **20 passos** claramente identificados:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[PASSO 1/20] Atualizando Sistema
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[INFO] Atualizando lista de pacotes...
[✓] Sistema atualizado com sucesso!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[PASSO 2/20] Instalando Docker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
```

---

## ✅ Verificação Pós-Instalação

### 1. Verificar Containers

```bash
cd /opt/sentinelweb
docker compose -f docker-compose.prod.yml ps
```

Todos devem estar **healthy**:
```
NAME                    STATUS          PORTS
sentinelweb_db_prod     Up (healthy)    5432/tcp
sentinelweb_redis_prod  Up (healthy)    6379/tcp
sentinelweb_web_prod    Up (healthy)    8000/tcp
sentinelweb_celery_prod Up              
sentinelweb_beat_prod   Up              
```

### 2. Verificar Endpoint de Saúde

```bash
curl http://localhost:8000/health | jq
```

Resposta esperada:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-09T12:00:00",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

### 3. Testar HTTPS

```bash
curl -I https://seudominio.com.br
```

Deve retornar **200 OK** com headers de segurança.

### 4. Verificar Firewall

```bash
ufw status
```

Apenas portas 22, 80, 443 devem estar abertas.

### 5. Verificar Fail2Ban

```bash
fail2ban-client status
```

Deve mostrar jails ativos: `sshd`, `nginx-http-auth`, `nginx-limit-req`.

### 6. Verificar Logs

```bash
docker compose -f docker-compose.prod.yml logs -f web
```

Não deve haver erros críticos.

---

## 🔐 Credenciais Geradas

Após a instalação, você encontrará as credenciais em:

```bash
cat /opt/sentinelweb/.env
```

**Credenciais importantes:**
- `SECRET_KEY` (64 bytes) - Chave JWT
- `POSTGRES_PASSWORD` (32 bytes) - Senha PostgreSQL
- `REDIS_PASSWORD` (32 bytes) - Senha Redis

**⚠️ GUARDE ESTAS CREDENCIAIS EM LOCAL SEGURO!**

Um resumo também é salvo em:
```bash
cat /opt/sentinelweb/INSTALLATION_SUMMARY.txt
```

---

## 🎨 Acessar a Aplicação

### Interface Web

Abra seu navegador:
```
https://seudominio.com.br
```

### Login Admin

Use as credenciais do superusuário criado durante a instalação.

### Dashboard

Após login, você terá acesso a:
- 📊 Dashboard de monitoramento
- 🌐 Gerenciamento de sites
- ❤️ Heartbeat checks
- 💰 Sistema de pagamentos
- 👤 Perfil de usuário

---

## 🛠️ Comandos Úteis

### Gerenciar Containers

```bash
cd /opt/sentinelweb

# Ver status
docker compose -f docker-compose.prod.yml ps

# Ver logs
docker compose -f docker-compose.prod.yml logs -f [service]

# Reiniciar todos
docker compose -f docker-compose.prod.yml restart

# Reiniciar um serviço
docker compose -f docker-compose.prod.yml restart web

# Parar todos
docker compose -f docker-compose.prod.yml stop

# Iniciar todos
docker compose -f docker-compose.prod.yml start

# Parar e remover
docker compose -f docker-compose.prod.yml down

# Rebuild e restart
docker compose -f docker-compose.prod.yml up -d --build
```

### Gerenciar Banco de Dados

```bash
# Entrar no PostgreSQL
docker exec -it sentinelweb_db_prod psql -U sentinelweb -d sentinelweb

# Backup manual
docker exec sentinelweb_db_prod pg_dump -U sentinelweb sentinelweb | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip -c backup_20260109.sql.gz | docker exec -i sentinelweb_db_prod psql -U sentinelweb -d sentinelweb
```

### Criar Superusuário Adicional

```bash
docker compose -f docker-compose.prod.yml exec web python create_superuser.py
```

### Ver Logs em Tempo Real

```bash
# Todos os serviços
docker compose -f docker-compose.prod.yml logs -f

# Apenas web
docker compose -f docker-compose.prod.yml logs -f web

# Apenas celery
docker compose -f docker-compose.prod.yml logs -f celery

# Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Executar Backup Manual

```bash
/opt/sentinelweb/backup.sh
```

### Renovar SSL Manualmente

```bash
certbot renew --dry-run  # Teste
certbot renew            # Renovação real
systemctl reload nginx
```

---

## 🔧 Configurações Opcionais

### Adicionar Chaves API (Asaas, Telegram, etc)

```bash
nano /opt/sentinelweb/.env
```

Adicione/edite:
```bash
# ASAAS (Pagamentos)
ASAAS_API_KEY=seu_api_key_de_producao_aqui
ASAAS_API_URL=https://api.asaas.com/v3

# TELEGRAM (Alertas)
TELEGRAM_BOT_TOKEN=seu_bot_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui

# SMTP (Email)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app
SMTP_FROM=noreply@seudominio.com

# GOOGLE PAGESPEED
GOOGLE_PAGESPEED_API_KEY=sua_api_key_aqui
```

Depois reinicie:
```bash
cd /opt/sentinelweb
docker compose -f docker-compose.prod.yml restart
```

---

## 🚨 Solução de Problemas

### Problema: Containers não ficam "healthy"

**Solução:**
```bash
# Ver logs do container com problema
docker compose -f docker-compose.prod.yml logs db
docker compose -f docker-compose.prod.yml logs web

# Verificar se portas estão livres
netstat -tulpn | grep -E ':(5432|6379|8000)'

# Reiniciar
docker compose -f docker-compose.prod.yml restart
```

### Problema: Erro ao obter certificado SSL

**Causa:** Domínio não aponta para o servidor

**Solução:**
```bash
# Verificar DNS
dig seudominio.com.br +short
nslookup seudominio.com.br

# Deve retornar o IP do seu servidor

# Obter certificado manualmente
certbot certonly --webroot -w /var/www/certbot -d seudominio.com.br -d www.seudominio.com.br

# Reiniciar Nginx
systemctl reload nginx
```

### Problema: "Permission denied" ao executar docker

**Solução:**
```bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Fazer logout e login novamente
exit
ssh root@SEU_IP

# Testar
docker ps
```

### Problema: Erro de migração de banco

**Solução:**
```bash
# Verificar se PostgreSQL está rodando
docker compose -f docker-compose.prod.yml ps db

# Recriar banco manualmente
docker compose -f docker-compose.prod.yml exec web python -c "
from database import engine, Base
from models import User, Site, SiteCheck, HeartbeatCheck, HeartbeatPing, Payment, SystemConfig
Base.metadata.create_all(bind=engine)
print('Tabelas criadas!')
"
```

### Problema: Nginx não inicia

**Solução:**
```bash
# Testar configuração
nginx -t

# Ver logs de erro
tail -50 /var/log/nginx/error.log

# Verificar se porta 80/443 está livre
netstat -tulpn | grep -E ':(80|443)'

# Reiniciar
systemctl restart nginx
```

### Problema: Firewall bloqueou SSH

**⚠️ CUIDADO! Pode perder acesso ao servidor!**

**Prevenção:**
```bash
# Antes de habilitar UFW, SEMPRE permita SSH:
ufw allow 22/tcp
ufw enable
```

**Recuperação:**
- Acesse via console VNC da Hostinger
- Desabilite UFW: `ufw disable`
- Configure corretamente e reative

---

## 📈 Monitoramento

### Verificar Uso de Recursos

```bash
# CPU e Memória dos containers
docker stats

# Disco
df -h

# Memória do sistema
free -h

# Processos
htop
```

### Verificar Logs de Acesso

```bash
# Nginx access log
tail -100 /var/log/nginx/access.log

# Nginx error log
tail -100 /var/log/nginx/error.log

# Fail2Ban
tail -100 /var/log/fail2ban.log
```

### Verificar Backups

```bash
ls -lah /var/backups/sentinelweb/
```

Deve haver arquivos:
- `postgres_YYYYMMDD_HHMMSS.sql.gz`
- `app_YYYYMMDD_HHMMSS.tar.gz`

---

## 🔄 Atualização da Aplicação

### Atualizar Código

```bash
cd /opt/sentinelweb

# Backup do .env atual
cp .env .env.backup

# Pull das mudanças (se usando Git)
git pull

# Rebuild das imagens
docker compose -f docker-compose.prod.yml build

# Restart com novo código
docker compose -f docker-compose.prod.yml up -d

# Verificar logs
docker compose -f docker-compose.prod.yml logs -f web
```

### Rollback (se algo der errado)

```bash
cd /opt/sentinelweb

# Reverter código (se Git)
git reset --hard HEAD~1

# Ou restaurar backup
docker compose -f docker-compose.prod.yml down
# Restaurar arquivos do backup
docker compose -f docker-compose.prod.yml up -d
```

---

## 🗑️ Desinstalação

### Remover Completamente

```bash
cd /opt/sentinelweb

# Parar e remover containers
docker compose -f docker-compose.prod.yml down -v

# Remover imagens
docker rmi $(docker images -q 'sentinelweb*')

# Remover arquivos
rm -rf /opt/sentinelweb
rm -rf /var/lib/sentinelweb
rm -rf /var/log/sentinelweb

# Remover backups (CUIDADO!)
# rm -rf /var/backups/sentinelweb

# Remover configurações Nginx
rm /etc/nginx/sites-enabled/sentinelweb
rm /etc/nginx/sites-available/sentinelweb
systemctl reload nginx

# Remover certificado SSL
certbot delete --cert-name seudominio.com.br

# Remover cron jobs
crontab -l | grep -v sentinelweb | crontab -

# Opcional: Remover Docker, Nginx, etc
apt-get remove -y docker-ce docker-ce-cli containerd.io nginx certbot fail2ban
apt-get autoremove -y
```

---

## 📞 Suporte

### Documentação Adicional

- `SECURITY_AUDIT.md` - Auditoria de segurança completa
- `SECURITY_CHECKLIST.md` - Checklist de 96 itens
- `DEPLOY_GUIDE.md` - Guia manual de deploy
- `PRODUCTION_READY.md` - Resumo executivo

### Checklist Pós-Instalação

Use o checklist de segurança para garantir que tudo está correto:

```bash
cat /opt/sentinelweb/SECURITY_CHECKLIST.md
```

Execute os testes de segurança recomendados:
- SSL Labs: https://www.ssllabs.com/ssltest/
- Security Headers: https://securityheaders.com
- OWASP ZAP scan

---

## 🎉 Conclusão

Parabéns! Seu SentinelWeb está instalado e rodando com:

✅ PostgreSQL 15 (produção)  
✅ Redis (cache e fila)  
✅ SSL/TLS (Let's Encrypt)  
✅ Firewall (UFW)  
✅ Proteção brute force (Fail2Ban)  
✅ Backups automáticos (diários)  
✅ Rate limiting  
✅ Security headers  
✅ Container security  
✅ Healthchecks  

**Sistema pronto para produção! 🚀**

---

**Versão:** 1.0.0  
**Data:** 09/01/2026  
**Autor:** SentinelWeb Team
