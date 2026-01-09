# ✅ CHECKLIST DE SEGURANÇA PRÉ-DEPLOY

**Data de Criação:** 08/01/2026  
**Última Verificação:** ___/___/______  
**Responsável:** _______________________

---

## 🔐 SEGURANÇA CRÍTICA

### Credenciais e Chaves

- [ ] **SECRET_KEY gerada** com 64+ bytes aleatórios
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(64))"
  ```
  - [ ] Verificado comprimento mínimo (32 chars)
  - [ ] Verificado que não é a chave padrão
  - [ ] Armazenada no .env (não hardcoded)

- [ ] **POSTGRES_PASSWORD** gerada com 32+ caracteres
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
  - [ ] Senha forte (letras, números, símbolos)
  - [ ] Diferente da SECRET_KEY
  - [ ] Armazenada apenas no .env

- [ ] **REDIS_PASSWORD** gerada com 32+ caracteres
  - [ ] Senha forte
  - [ ] Diferente das outras senhas
  - [ ] Configurada no docker-compose.prod.yml

- [ ] **ASAAS_API_KEY** configurada (se usar pagamentos)
  - [ ] Usando chave de PRODUÇÃO (não sandbox)
  - [ ] Testada e validada
  - [ ] Armazenada apenas no .env

- [ ] **TELEGRAM_BOT_TOKEN** configurado (se usar alertas)
  - [ ] Token válido do BotFather
  - [ ] Bot testado
  - [ ] Armazenado apenas no .env

---

## 🗄️ BANCO DE DADOS

### PostgreSQL

- [ ] **DATABASE_URL** configurada para PostgreSQL
  - [ ] Formato: `postgresql://user:password@host:port/database`
  - [ ] Host: `db` (nome do serviço Docker)
  - [ ] Porta: `5432` (interna)
  - [ ] Usuário NÃO é `postgres` (usar dedicado)

- [ ] **Volumes persistentes** configurados
  - [ ] Path: `/var/lib/sentinelweb/postgres`
  - [ ] Permissões corretas (750)
  - [ ] Backup configurado

- [ ] **Connection pooling** configurado
  - [ ] pool_size: 20
  - [ ] max_overflow: 40
  - [ ] pool_recycle: 3600

- [ ] **Migração testada**
  - [ ] Script `migrate_to_postgres.py` executado
  - [ ] Dados verificados
  - [ ] Backup do SQLite guardado

---

## 🐳 DOCKER & CONTAINERS

### Segurança de Containers

- [ ] **Containers NÃO rodam como root**
  - [ ] Dockerfile.prod usa `USER appuser`
  - [ ] Verificado com: `docker exec sentinelweb_web_prod whoami`
  - [ ] Resultado deve ser: `appuser`

- [ ] **Portas internas apenas**
  - [ ] PostgreSQL: NÃO exposto externamente
  - [ ] Redis: NÃO exposto externamente
  - [ ] FastAPI: Apenas via Nginx
  - [ ] Verificado com: `docker compose ps`

- [ ] **Healthchecks funcionando**
  - [ ] PostgreSQL: healthy
  - [ ] Redis: healthy
  - [ ] Web: healthy
  - [ ] Celery Worker: healthy

- [ ] **Security options**
  - [ ] `no-new-privileges: true` configurado
  - [ ] Read-only filesystem onde possível
  - [ ] Limites de recursos (CPU/RAM) definidos

---

## 🌐 NGINX & SSL

### Configuração do Nginx

- [ ] **SSL/TLS configurado**
  - [ ] Certificado Let's Encrypt obtido
  - [ ] Certificado válido (não expirado)
  - [ ] Grade no SSL Labs: A ou A+
  - [ ] HSTS habilitado (max-age=31536000)

- [ ] **Headers de segurança**
  - [ ] X-Frame-Options: SAMEORIGIN
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-XSS-Protection: 1; mode=block
  - [ ] Referrer-Policy configurado
  - [ ] CSP (Content-Security-Policy) configurado

- [ ] **Rate limiting**
  - [ ] Login: 5 req/min
  - [ ] API: 30 req/min
  - [ ] Geral: 100 req/min
  - [ ] Testado com: `ab -n 100 -c 10 https://domain/api/auth/login`

- [ ] **Redirect HTTP → HTTPS**
  - [ ] Todo tráfego HTTP redireciona para HTTPS
  - [ ] Testado: `curl -I http://domain.com`

---

## 🔥 FIREWALL

### UFW (Uncomplicated Firewall)

- [ ] **Firewall ativo**
  ```bash
  ufw status
  ```
  - [ ] Status: active

- [ ] **Portas corretas liberadas**
  - [ ] 22/tcp: SSH (PERMITIDO)
  - [ ] 80/tcp: HTTP (PERMITIDO)
  - [ ] 443/tcp: HTTPS (PERMITIDO)
  - [ ] Todas as outras: BLOQUEADAS

- [ ] **Regras padrão**
  - [ ] Default incoming: DENY
  - [ ] Default outgoing: ALLOW

- [ ] **Fail2Ban ativo**
  ```bash
  systemctl status fail2ban
  ```
  - [ ] SSH jail ativo
  - [ ] Nginx jail ativo
  - [ ] Bantime: 3600+ segundos

---

## 📝 ARQUIVOS E CONFIGURAÇÕES

### Arquivos Sensíveis

- [ ] **.env NÃO está no Git**
  - [ ] Verificado com: `git status`
  - [ ] .gitignore configurado
  - [ ] Backup do .env em local seguro (fora do servidor)

- [ ] **Permissões corretas**
  - [ ] .env: 600 (apenas owner lê)
  - [ ] deploy.sh: 755 (executável)
  - [ ] Diretórios: 750
  - [ ] Logs: 640

- [ ] **Backups configurados**
  - [ ] Script de backup criado
  - [ ] Cron job configurado (2AM diário)
  - [ ] Retenção: 30 dias
  - [ ] Testado manualmente

---

## 🔍 CÓDIGO & APLICAÇÃO

### Validações

- [ ] **SECRET_KEY validada no código**
  - [ ] auth.py: Valida presença e comprimento
  - [ ] Aplicação NÃO inicia sem SECRET_KEY
  - [ ] Testado com .env vazio

- [ ] **CORS configurado**
  - [ ] Origens específicas (não "*")
  - [ ] allow_credentials: True
  - [ ] Métodos limitados

- [ ] **Trusted Host configurado**
  - [ ] Apenas domínio da aplicação
  - [ ] Previne HTTP Host Header attacks

- [ ] **Endpoint /health funcionando**
  ```bash
  curl https://domain.com/health
  ```
  - [ ] Retorna JSON com status
  - [ ] Verifica database
  - [ ] Verifica redis

- [ ] **Logs configurados**
  - [ ] LOG_LEVEL: INFO (não DEBUG)
  - [ ] Rotação de logs ativa
  - [ ] Logs estruturados (JSON)

---

## 🧪 TESTES DE SEGURANÇA

### Testes Manuais

- [ ] **Teste de autenticação**
  - [ ] Login funciona
  - [ ] JWT expira corretamente
  - [ ] Logout funciona
  - [ ] Não aceita tokens inválidos

- [ ] **Teste de rate limiting**
  - [ ] Múltiplas tentativas de login bloqueadas
  - [ ] Retorna 429 após limite
  - [ ] Liberado após tempo configurado

- [ ] **Teste de HTTPS**
  - [ ] Certificado válido
  - [ ] HTTP redireciona para HTTPS
  - [ ] HSTS header presente

- [ ] **Teste de headers**
  ```bash
  curl -I https://domain.com
  ```
  - [ ] X-Frame-Options presente
  - [ ] X-Content-Type-Options presente
  - [ ] Strict-Transport-Security presente

### Testes Automatizados

- [ ] **Scan de vulnerabilidades**
  ```bash
  # OWASP ZAP
  docker run -t owasp/zap2docker-stable zap-baseline.py -t https://domain.com
  ```

- [ ] **SSL Labs**
  - [ ] Acessar: https://www.ssllabs.com/ssltest/
  - [ ] Grade: A ou A+

- [ ] **Security Headers**
  - [ ] Acessar: https://securityheaders.com
  - [ ] Grade: A ou A+

---

## 💾 BACKUP & RECUPERAÇÃO

### Procedimentos

- [ ] **Backup testado**
  - [ ] Backup manual executado com sucesso
  - [ ] Arquivo gerado corretamente
  - [ ] Verificado integridade (gzip -t)

- [ ] **Restore testado**
  - [ ] Restore em ambiente de teste
  - [ ] Dados restaurados corretamente
  - [ ] Aplicação funciona após restore

- [ ] **Disaster Recovery Plan**
  - [ ] Documentado procedimento de rollback
  - [ ] Testado rollback
  - [ ] Tempo de recuperação conhecido (RTO)

---

## 📊 MONITORAMENTO

### Métricas e Alertas

- [ ] **Healthcheck externo**
  - [ ] UptimeRobot configurado
  - [ ] Pingdom configurado
  - [ ] Alertas via email/telegram

- [ ] **Logs centralizados**
  - [ ] Aplicação logando corretamente
  - [ ] Nginx logando corretamente
  - [ ] PostgreSQL logando queries lentas

- [ ] **Métricas de performance**
  - [ ] Tempo de resposta < 500ms
  - [ ] Uso de CPU < 70%
  - [ ] Uso de RAM < 80%
  - [ ] Uso de disco < 80%

---

## 📞 PÓS-DEPLOY

### Verificações Finais

- [ ] **Aplicação acessível**
  ```bash
  curl -I https://domain.com
  ```
  - [ ] Retorna 200 OK
  - [ ] Página carrega completamente

- [ ] **Login funciona**
  - [ ] Admin consegue fazer login
  - [ ] Dashboard carrega
  - [ ] Funcionalidades testadas

- [ ] **Sites sendo monitorados**
  - [ ] Adicionar site de teste
  - [ ] Verificação executada
  - [ ] Status atualizado

- [ ] **Alertas funcionando**
  - [ ] Telegram recebe alertas (se configurado)
  - [ ] Email recebe alertas (se configurado)

---

## 🎯 SCORE FINAL

Total de itens: **96**

- [ ] **Críticos (30 itens):** ___/30 ✅
- [ ] **Importantes (40 itens):** ___/40 ✅
- [ ] **Recomendados (26 itens):** ___/26 ✅

**Score mínimo para produção:** 85/96 (88%)

**Meu score:** ___/96 (___%)

---

## ✅ APROVAÇÃO

- [ ] Todos os itens críticos verificados
- [ ] Score mínimo atingido (88%+)
- [ ] Backups configurados e testados
- [ ] Monitoramento ativo

**Aprovado para produção:** SIM ☐  NÃO ☐

**Assinatura:** _______________________  
**Data:** ___/___/______

---

## 📚 REFERÊNCIAS

- `SECURITY_AUDIT.md` - Auditoria completa de segurança
- `DEPLOY_GUIDE.md` - Guia de deploy
- `PRODUCTION_READY.md` - Resumo executivo
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SSL Labs](https://www.ssllabs.com/ssltest/)
- [Security Headers](https://securityheaders.com/)
