# 🛡️ MELHORIAS NO SCRIPT DE INSTALAÇÃO

## 📋 Resumo

O script `install.sh` foi revisado e melhorado com **15 correções preventivas** para evitar erros futuros durante a instalação.

---

## ✅ Melhorias Implementadas

### 1. **Verificação de Recursos do Sistema**

#### Espaço em Disco
- ✅ Verifica se há pelo menos **10GB livres**
- ✅ Mostra espaço disponível em GB
- ✅ Bloqueia instalação se insuficiente
- **Previne:** Falhas por falta de espaço durante build ou runtime

```bash
Espaço em disco: 45GB disponível
```

#### Memória RAM
- ✅ Verifica se há pelo menos **1.5GB de RAM**
- ✅ Avisa se abaixo do recomendado (2GB)
- ✅ Permite continuar com confirmação
- **Previne:** Lentidão ou falhas de containers por falta de memória

```bash
RAM: 2048MB
```

### 2. **Verificação de Portas**

- ✅ Verifica se portas **80, 443, 5432, 6379** estão livres
- ✅ Avisa sobre conflitos com outros serviços
- ✅ Permite continuar com confirmação
- **Previne:** Erro de bind ao iniciar Nginx, PostgreSQL ou Redis

```bash
Portas necessárias estão livres
```

### 3. **Conectividade com GitHub**

- ✅ Testa conexão com GitHub antes de clonar
- ✅ Timeout de 10 segundos
- ✅ Mensagem clara em caso de falha
- **Previne:** Timeout ou falha no clone por problemas de rede

```bash
Conexão com GitHub OK!
```

### 4. **Validação de Domínio**

- ✅ Remove espaços em branco
- ✅ Valida formato com regex (ex: `exemplo.com.br`)
- ✅ Rejeita domínios inválidos
- **Previne:** Erro na configuração do Nginx e certificado SSL

```bash
Domínio inválido! Use o formato: exemplo.com.br
```

### 5. **Validação de Email**

- ✅ Remove espaços em branco
- ✅ Valida formato com regex (ex: `user@domain.com`)
- ✅ Rejeita emails inválidos
- **Previne:** Erro ao obter certificado SSL com Let's Encrypt

```bash
Email inválido! Use o formato: usuario@dominio.com
```

### 6. **Validação de IP**

- ✅ Detecta IP público automaticamente
- ✅ Valida formato IPv4 (ex: `192.168.1.1`)
- ✅ Timeout de 5 segundos na detecção
- **Previne:** Configuração incorreta no modo IP-only

```bash
IP inválido! Use o formato: 192.168.1.1
```

### 7. **Verificação de DNS**

- ✅ Verifica se domínio aponta para o servidor
- ✅ Compara IP do domínio com IP do servidor
- ✅ Avisa sobre configuração incorreta
- ✅ Permite continuar com confirmação
- **Previne:** Falha ao obter certificado SSL por DNS incorreto

```bash
DNS configurado corretamente! exemplo.com -> 192.168.1.1
```

### 8. **Timeout Inteligente de Healthcheck**

- ✅ Loop de espera até 60 segundos
- ✅ Verifica se containers estão "healthy"
- ✅ Fallback se `jq` não estiver disponível
- ✅ Progresso em tempo real
- **Previne:** Falsos positivos/negativos no status dos containers

```bash
Aguardando containers ficarem saudáveis (pode demorar até 60s)...
Aguardando... (15s/60s)
Containers saudáveis!
```

### 9. **Verificação de Dependência `jq`**

- ✅ Fallback se `jq` não disponível
- ✅ Parse de JSON manual quando necessário
- ✅ Não bloqueia instalação
- **Previne:** Erro ao verificar healthcheck ou status

```bash
# Usa jq se disponível, senão grep
```

### 10. **Verificação de Containers Existentes**

- ✅ Detecta containers já rodando
- ✅ Oferece parar e recriar
- ✅ Evita conflitos de nomes
- **Previne:** Erro "container already exists"

```bash
Containers já existentes detectados
Deseja parar e recriar os containers? (s/N):
```

### 11. **Validação de Arquivos Docker**

- ✅ Verifica se `docker-compose.prod.yml` existe
- ✅ Verifica se `Dockerfile.prod` existe
- ✅ Lista arquivos disponíveis em caso de erro
- **Previne:** Erro obscuro "file not found" durante build

```bash
Arquivo docker-compose.prod.yml não encontrado!
Arquivos disponíveis: (lista)
```

### 12. **Mensagens de Erro Detalhadas**

- ✅ Explica possíveis causas de falhas
- ✅ Sugere comandos para debugging
- ✅ Indica próximos passos
- **Previne:** Usuário não saber o que fazer após erro

```bash
Falha ao construir imagens Docker!
Verifique os logs acima para mais detalhes
Possíveis causas:
  • Erro de sintaxe no Dockerfile
  • Falta de dependências
  • Problemas de conectividade
```

### 13. **Script de Backup Robusto**

- ✅ Verifica se container PostgreSQL está rodando
- ✅ Valida se arquivo de backup foi criado
- ✅ Valida se arquivo não está vazio
- ✅ Registra erros específicos
- ✅ Mostra espaço usado por backups
- **Previne:** Backups corrompidos ou vazios

```bash
[2026-01-09 12:00:00] Backup PostgreSQL: OK - /var/backups/sentinelweb/postgres_20260109_120000.sql.gz
[2026-01-09 12:00:05] Backup aplicação: OK - /var/backups/sentinelweb/app_20260109_120000.tar.gz
[2026-01-09 12:00:06] Espaço total de backups: 2.3G
```

### 14. **Validação de Criação de Tabelas**

- ✅ Verifica se comando de criação teve sucesso
- ✅ Sugere verificar logs em caso de erro
- ✅ Bloqueia instalação se falhar
- **Previne:** Instalação "completa" mas com banco vazio

```bash
Tabelas criadas com sucesso!
```

### 15. **Tratamento de Erro no Build**

- ✅ Captura exit code do docker build
- ✅ Lista possíveis causas
- ✅ Sugere comandos de investigação
- **Previne:** Continuar instalação com imagens quebradas

---

## 🔍 Antes vs Depois

### ❌ ANTES

```bash
# Instalação falhava silenciosamente em vários cenários:
- Disco cheio durante build
- RAM insuficiente (containers crashando)
- Porta 80 já em uso (Nginx falha)
- DNS não configurado (SSL falha)
- Domínio/email inválido (certbot erro obscuro)
- Containers não ficam healthy (timeout fixo)
- Backup corrupto não detectado
- IP público não detectado corretamente
```

### ✅ DEPOIS

```bash
# Todas as verificações são feitas ANTES de começar:
✓ Espaço em disco verificado
✓ RAM verificada
✓ Portas livres
✓ Conectividade GitHub testada
✓ Domínio validado
✓ Email validado
✓ DNS verificado
✓ Healthcheck inteligente
✓ Erros claros e informativos
✓ Backup robusto com validação
✓ IP detectado com fallback
```

---

## 📊 Estatísticas

| Métrica | Valor |
|---------|-------|
| **Linhas adicionadas** | 249 |
| **Linhas removidas** | 21 |
| **Novas verificações** | 15 |
| **Funções adicionadas** | 3 |
| **Validações de formato** | 5 |
| **Timeouts adicionados** | 4 |

---

## 🚀 Benefícios

### Para o Usuário
- ✅ Menos chances de instalação falhar
- ✅ Erros mais claros quando ocorrem
- ✅ Sugestões de como resolver problemas
- ✅ Instalação mais rápida (detecta problemas cedo)

### Para Suporte
- ✅ Menos tickets de suporte
- ✅ Logs mais informativos
- ✅ Problemas detectados antes de começar
- ✅ Backup confiável

### Para o Sistema
- ✅ Containers mais estáveis
- ✅ Backup íntegro
- ✅ Configuração correta desde o início
- ✅ Menos necessidade de reinstalação

---

## 🔧 Comandos de Verificação

### Testar Validações

```bash
# Testar com domínio inválido
sudo bash install.sh
# Digite: "dominio com espaço"

# Testar com email inválido
sudo bash install.sh
# Digite: "emailsemarroba"

# Testar com IP inválido
sudo bash install.sh
# Digite: "999.999.999.999"
```

### Simular Falta de Recursos

```bash
# Simular disco cheio
dd if=/dev/zero of=/tmp/bigfile bs=1G count=50

# Verificar RAM
free -m

# Verificar portas
netstat -tuln | grep -E ':(80|443|5432|6379)'
```

---

## 📝 Notas Técnicas

### Regex Utilizados

```bash
# Domínio
^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$

# Email
^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$

# IPv4
^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$
```

### Timeouts

- **GitHub**: 10s (conexão inicial)
- **IP detection**: 5s (cada serviço)
- **DNS check**: 5s
- **Container healthcheck**: até 60s

### Requisitos Mínimos

- **Disco**: 10GB (recomendado 20GB)
- **RAM**: 1.5GB (recomendado 2GB)
- **CPU**: 2 cores (recomendado 4 cores)

---

## 🎯 Próximos Passos

### Melhorias Futuras Possíveis

1. **Retry Automático**
   - Tentar novamente em caso de falha temporária
   - Útil para problemas de rede

2. **Validação de Certificado**
   - Verificar se certificado foi obtido corretamente
   - Testar acesso HTTPS

3. **Monitoramento Pós-Instalação**
   - Verificar saúde dos containers periodicamente
   - Alertar sobre problemas

4. **Rollback Automático**
   - Desfazer instalação em caso de falha crítica
   - Restaurar estado anterior

5. **Instalação Desatendida**
   - Modo silencioso com arquivo de configuração
   - Para automação com Terraform/Ansible

---

## 📞 Suporte

Se encontrar algum erro não coberto por estas validações:

1. Verifique os logs: `/var/log/sentinelweb/`
2. Execute: `docker compose -f docker-compose.prod.yml logs`
3. Reporte no GitHub com os logs completos

---

**Versão:** 2.0.0  
**Data:** 09/01/2026  
**Commit:** b5be8dd  
**Autor:** SentinelWeb Team
