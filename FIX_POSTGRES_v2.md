# 🔧 CORREÇÃO DO PROBLEMA DE SENHA POSTGRESQL - v2.0

## 📋 Resumo do Problema

O erro `FATAL: password authentication failed for user "sentinelweb"` ocorria porque:

1. O PostgreSQL Docker **só lê `POSTGRES_PASSWORD` na PRIMEIRA inicialização**
2. Se o container já existia com uma senha diferente, alterar o `.env` não tinha efeito
3. O PostgreSQL armazena a senha no volume `sentinelweb_postgres_data`
4. Na segunda execução: `PostgreSQL Database directory appears to contain a database; Skipping initialization`

## ✅ Correções Aplicadas

### 1. Script `install.sh` (v2.0)

**Arquivo:** `/opt/sentinelweb/install.sh`

**Alterações principais:**

- **Passo 8 - Limpeza de Instalação Anterior:** Novo passo que detecta e remove volumes/containers antigos antes de prosseguir
- **Passo 16 - Preparação do Ambiente Docker:** Garante que volumes estão limpos antes de iniciar containers
- **Passo 17 - Build com `--no-cache`:** Força reconstrução completa das imagens
- **Passo 18 - Aguarda PostgreSQL:** Aumentado tempo de espera e adicionado teste real de autenticação
- **Credenciais alfanuméricas:** Senhas geradas apenas com `openssl rand -hex` (sem caracteres especiais que podem causar problemas de escape)
- **Remoção do atributo `version`:** O docker-compose.prod.yml é corrigido automaticamente (atributo obsoleto)

### 2. Novo Script `reinstall_quick.sh`

**Arquivo:** `/opt/sentinelweb/reinstall_quick.sh`

Script para reinstalação rápida quando o problema de senha ocorrer:

```bash
sudo bash reinstall_quick.sh
```

Este script:
1. Para todos os containers
2. Remove TODOS os volumes (⚠️ apaga dados!)
3. Gera nova senha PostgreSQL
4. Atualiza o `.env`
5. Recria containers
6. Testa conexão
7. Oferece criar superusuário

### 3. Documentação Atualizada

**Arquivo:** `/opt/sentinelweb/INSTALL_GUIDE.md`

- Seção "Erro de autenticação PostgreSQL" reescrita com explicação clara da causa raiz
- Referência ao script `reinstall_quick.sh`
- Comandos manuais passo a passo

## 🚀 Para Reinstalar no Servidor

### Opção 1: Reinstalação Completa (Recomendada)

```bash
# 1. Acessar servidor
ssh root@SEU_IP

# 2. Baixar novo script de instalação
cd /opt
curl -fsSL https://raw.githubusercontent.com/GuilhermeSantiago921/sentinelweb/main/install.sh -o install.sh
chmod +x install.sh

# 3. Executar (vai perguntar se quer remover volumes antigos)
sudo bash install.sh
```

### Opção 2: Usar Script de Reinstalação Rápida

```bash
# Se já tem o sistema instalado:
cd /opt/sentinelweb

# Baixar script de reinstalação
curl -fsSL https://raw.githubusercontent.com/GuilhermeSantiago921/sentinelweb/main/reinstall_quick.sh -o reinstall_quick.sh
chmod +x reinstall_quick.sh

# Executar
sudo bash reinstall_quick.sh
```

### Opção 3: Comandos Manuais

```bash
cd /opt/sentinelweb

# Parar e remover tudo
docker compose -f docker-compose.prod.yml down -v
docker volume rm sentinelweb_postgres_data sentinelweb_redis_data 2>/dev/null

# Gerar nova senha
NEW_PASS=$(openssl rand -hex 16)
echo "Nova senha: $NEW_PASS"

# Atualizar .env
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://sentinelweb:$NEW_PASS@db:5432/sentinelweb|" .env

# Recriar
docker compose -f docker-compose.prod.yml up -d --build

# Aguardar e testar
sleep 30
docker compose -f docker-compose.prod.yml exec db psql -U sentinelweb -d sentinelweb -c "SELECT 'OK';"

# Criar superusuário
docker compose -f docker-compose.prod.yml exec web python create_superuser.py
```

## 📁 Arquivos Modificados/Criados

| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `install.sh` | ✅ Modificado | Script de instalação v2.0 com correções |
| `reinstall_quick.sh` | ✅ Novo | Script para reinstalação rápida |
| `install.sh.backup_old` | ✅ Backup | Backup do script antigo |
| `INSTALL_GUIDE.md` | ✅ Modificado | Documentação atualizada |
| `FIX_POSTGRES_v2.md` | ✅ Novo | Este arquivo de resumo |

## 🔍 Como Verificar se Funcionou

```bash
# 1. Ver status dos containers
docker compose -f docker-compose.prod.yml ps

# Todos devem estar "Up" ou "healthy"

# 2. Testar conexão PostgreSQL
docker compose -f docker-compose.prod.yml exec db psql -U sentinelweb -d sentinelweb -c "SELECT 'SUCESSO!';"

# Deve mostrar: SUCESSO!

# 3. Ver logs (sem erros de autenticação)
docker compose -f docker-compose.prod.yml logs db | tail -20

# 4. Acessar a aplicação
curl http://localhost:8000/health
# ou acesse via navegador
```

---

**Data:** $(date)
**Versão:** 2.0
