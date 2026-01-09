# 🔧 TROUBLESHOOTING - PROBLEMAS COMUNS

## 🐛 Problemas Durante Instalação

### ❌ Erro: "password authentication failed for user sentinelweb"

**Sintoma:**
```
psycopg2.OperationalError: connection to server at "db" (172.20.0.3), port 5432 failed: 
FATAL: password authentication failed for user "sentinelweb"
```

**Causa:**
O container PostgreSQL foi criado com credenciais diferentes das especificadas no `.env`, ou os containers foram criados antes do `.env` ser gerado.

**Solução Automática:**
O script de instalação detecta este erro e oferece recriar os containers automaticamente.

**Solução Manual:**

```bash
cd /opt/sentinelweb

# 1. Parar e remover TODOS os containers e volumes
docker compose -f docker-compose.prod.yml down -v

# 2. Verificar que o .env tem as credenciais corretas
cat .env | grep POSTGRES

# 3. Recriar containers do zero
docker compose -f docker-compose.prod.yml up -d

# 4. Aguardar containers ficarem prontos
sleep 30

# 5. Criar tabelas
docker compose -f docker-compose.prod.yml exec web python -c "
from database import engine, Base
from models import User, Site, MonitorLog, HeartbeatCheck, SystemConfig, Payment
Base.metadata.create_all(bind=engine)
print('Tabelas criadas!')
"
```

---

### ❌ Erro: "integer expression expected"

**Sintoma:**
```
install.sh: line 1111: [: 0
0: integer expression expected
```

**Causa:**
Variável `HEALTHY` contém quebras de linha ou caracteres não numéricos.

**Solução:**
Atualizado no commit `2ee49e1` - script agora sanitiza a variável.

**Se o erro persistir:**
```bash
# Baixar script atualizado
curl -fsSL https://raw.githubusercontent.com/GuilhermeSantiago921/sentinelweb/main/install.sh -o install.sh
chmod +x install.sh
```

---

### ⚠️ Warning: Variable is not set

**Sintoma:**
```
WARN[0000] The "ASAAS_API_KEY" variable is not set. Defaulting to a blank string.
WARN[0000] The "TELEGRAM_BOT_TOKEN" variable is not set. Defaulting to a blank string.
```

**Causa:**
Variáveis opcionais não configuradas no `.env`.

**Solução:**
Estas variáveis são **opcionais** e não afetam a instalação básica. Para configurá-las:

```bash
nano /opt/sentinelweb/.env
```

Adicione:
```bash
# ASAAS (Pagamentos)
ASAAS_API_KEY=seu_api_key_aqui
ASAAS_API_URL=https://api.asaas.com/v3

# TELEGRAM (Alertas)
TELEGRAM_BOT_TOKEN=seu_bot_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

Reinicie:
```bash
cd /opt/sentinelweb
docker compose -f docker-compose.prod.yml restart
```

---

### ⚠️ Warning: attribute `version` is obsolete

**Sintoma:**
```
WARN[0000] /opt/sentinelweb/docker-compose.prod.yml: the attribute `version` is obsolete
```

**Causa:**
Docker Compose v2 não requer mais a linha `version:`.

**Solução:**
Este é apenas um aviso, não afeta o funcionamento. Para remover:

```bash
nano /opt/sentinelweb/docker-compose.prod.yml
```

Delete a linha:
```yaml
version: '3.9'  # <-- Remover esta linha
```

---

## 🐳 Problemas com Containers

### Container não fica "healthy"

**Verificar logs:**
```bash
docker compose -f docker-compose.prod.yml logs [service_name]
```

**Containers específicos:**

#### Web (FastAPI)
```bash
docker compose -f docker-compose.prod.yml logs web
```

**Possíveis causas:**
- Banco de dados não conectado
- Redis não conectado
- Erro de importação Python
- Porta 8000 em uso

#### PostgreSQL (db)
```bash
docker compose -f docker-compose.prod.yml logs db
```

**Possíveis causas:**
- Senha incorreta
- Volume corrompido
- Falta de memória

**Solução:**
```bash
# Recriar apenas o banco
docker compose -f docker-compose.prod.yml stop db
docker compose -f docker-compose.prod.yml rm -f db
docker volume rm sentinelweb_postgres_data
docker compose -f docker-compose.prod.yml up -d db
```

#### Redis
```bash
docker compose -f docker-compose.prod.yml logs redis
```

**Solução:**
```bash
docker compose -f docker-compose.prod.yml restart redis
```

---

## 🌐 Problemas com Nginx

### Nginx não inicia

**Verificar configuração:**
```bash
nginx -t
```

**Ver erros:**
```bash
tail -50 /var/log/nginx/error.log
```

**Problemas comuns:**

#### Porta 80/443 em uso
```bash
# Verificar quem está usando
netstat -tulpn | grep -E ':(80|443)'

# Parar Apache (se existir)
systemctl stop apache2
systemctl disable apache2

# Reiniciar Nginx
systemctl restart nginx
```

#### Certificado SSL não encontrado
```bash
# Verificar se existe
ls -la /etc/letsencrypt/live/seudominio.com.br/

# Se não existir, obter manualmente
certbot certonly --webroot -w /var/www/certbot -d seudominio.com.br
```

---

## 🔐 Problemas com SSL

### Erro ao obter certificado

**Sintoma:**
```
Failed authorization procedure
```

**Verificar DNS:**
```bash
dig seudominio.com.br +short
nslookup seudominio.com.br
```

Deve retornar o IP do seu servidor.

**Verificar webroot:**
```bash
ls -la /var/www/certbot/.well-known/acme-challenge/
```

**Solução:**
```bash
# 1. Criar diretório
mkdir -p /var/www/certbot

# 2. Ajustar permissões
chown -R www-data:www-data /var/www/certbot

# 3. Testar Nginx
nginx -t

# 4. Tentar novamente
certbot certonly \
  --webroot \
  -w /var/www/certbot \
  --email seu@email.com \
  -d seudominio.com.br \
  -d www.seudominio.com.br
```

---

## 🔥 Problemas com Firewall

### UFW bloqueou SSH

**⚠️ NUNCA faça `ufw enable` sem permitir SSH primeiro!**

**Prevenção:**
```bash
ufw allow 22/tcp
ufw enable
```

**Recuperação:**
- Acesse via console VNC/VPS da Hostinger
- Execute: `ufw disable`
- Configure corretamente

---

## 💾 Problemas com Banco de Dados

### Tabelas não foram criadas

**Verificar:**
```bash
docker exec -it sentinelweb_db_prod psql -U sentinelweb -d sentinelweb -c "\dt"
```

**Se vazio, criar manualmente:**
```bash
docker compose -f docker-compose.prod.yml exec web python -c "
from database import engine, Base
from models import User, Site, MonitorLog, HeartbeatCheck, SystemConfig, Payment
Base.metadata.create_all(bind=engine)
print('Tabelas criadas!')
"
```

### Erro de conexão com banco

**Verificar se está rodando:**
```bash
docker compose -f docker-compose.prod.yml ps db
```

**Verificar logs:**
```bash
docker compose -f docker-compose.prod.yml logs db
```

**Testar conexão:**
```bash
docker exec -it sentinelweb_db_prod psql -U sentinelweb -d sentinelweb
```

---

## 🔄 Reset Completo

Se nada funcionar, reset completo:

```bash
cd /opt/sentinelweb

# 1. Parar tudo
docker compose -f docker-compose.prod.yml down -v

# 2. Remover volumes
docker volume rm sentinelweb_postgres_data sentinelweb_redis_data

# 3. Fazer backup do .env
cp .env .env.backup

# 4. Recriar do zero
docker compose -f docker-compose.prod.yml up -d

# 5. Aguardar
sleep 60

# 6. Criar tabelas
docker compose -f docker-compose.prod.yml exec web python -c "
from database import engine, Base
from models import User, Site, MonitorLog, HeartbeatCheck, SystemConfig, Payment
Base.metadata.create_all(bind=engine)
"

# 7. Criar superusuário
docker compose -f docker-compose.prod.yml exec web python create_superuser.py
```

---

## 📞 Suporte Adicional

### Logs Importantes

```bash
# Logs da aplicação
docker compose -f docker-compose.prod.yml logs -f web

# Logs do banco
docker compose -f docker-compose.prod.yml logs -f db

# Logs do Nginx
tail -f /var/log/nginx/error.log

# Logs do sistema
journalctl -xe
```

### Informações do Sistema

```bash
# Uso de recursos
docker stats

# Espaço em disco
df -h

# Memória
free -h

# Containers rodando
docker ps -a
```

---

**Atualizado:** 09/01/2026  
**Versão:** 1.0.0  
**Autor:** SentinelWeb Team
