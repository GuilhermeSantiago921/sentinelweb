# WordPress Security Scanner - SentinelWeb

## 📋 Visão Geral

O SentinelWeb agora inclui um **scanner de segurança WordPress** completo que detecta automaticamente sites WordPress e verifica vulnerabilidades comuns de segurança.

## 🎯 Para que serve?

O WordPress é o CMS mais popular do mundo, mas também é frequentemente alvo de ataques. Este scanner identifica:

- ✅ Detecção automática de WordPress
- ✅ Versão do WordPress instalada
- ✅ Arquivos sensíveis expostos
- ✅ Enumeração de usuários via API
- ✅ Debug logs acessíveis
- ✅ Backups de configuração expostos
- ✅ XML-RPC habilitado
- ✅ Directory listing

## 🔍 Como funciona?

### 1. Detecção de WordPress

O scanner usa múltiplos métodos para detectar WordPress:

```python
# Método 1: Meta Generator no HTML
<meta name="generator" content="WordPress 6.4.2" />

# Método 2: Arquivo readme.html
GET /readme.html

# Método 3: Indicadores no código
/wp-content/
/wp-includes/
/wp-json/
```

### 2. Verificações de Segurança

O scanner realiza os seguintes testes:

#### 🔴 Teste 1: Debug Log Exposto
- **Arquivo**: `/wp-content/debug.log`
- **Severidade**: **ALTA**
- **Risco**: Pode conter credenciais, paths do servidor, informações de banco de dados
- **Impacto**: Exposição de dados sensíveis

#### 🔴 Teste 2: Backup de Configuração
- **Arquivos**: 
  - `/wp-config.php.bak`
  - `/wp-config.php.old`
- **Severidade**: **CRÍTICA**
- **Risco**: Contém credenciais do banco de dados
- **Impacto**: Acesso total ao banco de dados

#### 🔴 Teste 3: Repositório Git Exposto
- **Arquivo**: `/.git/config`
- **Severidade**: **ALTA**
- **Risco**: Exposição de código-fonte e histórico
- **Impacto**: Vazamento de informações do projeto

#### 🟡 Teste 4: XML-RPC Ativo
- **Arquivo**: `/xmlrpc.php`
- **Severidade**: **MÉDIA**
- **Risco**: Vetor de ataque para brute force e DDoS
- **Impacto**: Ataques de força bruta e amplificação DDoS

#### 🟡 Teste 5: User Enumeration
- **Endpoint**: `/wp-json/wp/v2/users`
- **Severidade**: **MÉDIA**
- **Risco**: Expõe usernames para ataques de brute force
- **Impacto**: Lista de usuários adminstradores

#### 🟢 Teste 6: Directory Listing
- **Diretório**: `/wp-content/uploads/`
- **Severidade**: **BAIXA**
- **Risco**: Permite navegação nos arquivos do site
- **Impacto**: Exposição da estrutura de arquivos

## 📊 Campos no Banco de Dados

Três novos campos foram adicionados à tabela `Site`:

```python
is_wordpress: Boolean           # True se o site é WordPress
wp_version: String(50)          # Versão detectada (ex: "6.4.2")
vulnerabilities_found: Text     # JSON com lista de vulnerabilidades
```

### Estrutura do JSON de Vulnerabilidades

```json
[
  {
    "type": "debug_log",
    "file": "/wp-content/debug.log",
    "description": "Debug log do WordPress exposto",
    "severity": "high",
    "risk": "Pode conter credenciais, paths do servidor e informações sensíveis",
    "url": "https://example.com/wp-content/debug.log"
  },
  {
    "type": "user_enumeration",
    "endpoint": "/wp-json/wp/v2/users",
    "description": "Enumeração de usuários via REST API",
    "severity": "medium",
    "risk": "Expõe usernames que podem ser usados em ataques de brute force",
    "users_found": 3,
    "sample_users": ["admin", "editor", "author"],
    "url": "https://example.com/wp-json/wp/v2/users"
  }
]
```

## 🔔 Alertas Telegram

Vulnerabilidades **CRÍTICAS** e **ALTAS** geram alertas automáticos via Telegram:

```
🚨 ALERTA - VULNERABILIDADES WORDPRESS

🌐 Site: Meu Site WordPress
🔗 Domínio: meusite.com.br
⏰ Horário: 07/01/2026 10:30:45 UTC
⚠️ Vulnerabilidades Críticas: 2

• Backup do wp-config.php acessível
• Debug log do WordPress exposto

Recomenda-se ação imediata para corrigir as vulnerabilidades.
```

## 🎨 Visualização no Dashboard

### Badge WordPress

Sites WordPress aparecem com um badge azul:

```
[ONLINE] [WordPress 6.4.2]
```

### Badge de Vulnerabilidades

Se vulnerabilidades forem encontradas, aparece um badge vermelho pulsante clicável:

```
[⚠️ 3 Vulnerabilidade(s)]
```

### Painel Expansível

Ao clicar no badge de vulnerabilidades, um painel detalhado se expande mostrando:

- ✅ Severidade (CRÍTICO, ALTO, MÉDIO, BAIXO) com cores
- ✅ Descrição da vulnerabilidade
- ✅ Risco associado
- ✅ Arquivo ou endpoint afetado
- ✅ Usuários expostos (quando aplicável)
- ✅ Recomendações de correção

## ⚡ Performance e Segurança

### Timeouts Inteligentes
- **5 segundos** por teste
- **Não trava o worker** se o site estiver lento
- **Try-catch** em cada teste individual

### Scan Não-Invasivo
- ✅ Apenas **leitura** (HEAD/GET requests)
- ✅ Não tenta **explorar** vulnerabilidades
- ✅ Não causa **sobrecarga** no servidor
- ✅ User-Agent profissional para evitar bloqueios

### Verificação SSL
- Aceita certificados autoassinados (`verify=False`)
- Testa HTTPS primeiro, depois HTTP

## 🔧 Código Principal

### scanner.py - Função check_wordpress_health()

```python
def check_wordpress_health(domain: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Verifica se o site é WordPress e realiza scan de segurança.
    
    Returns:
        {
            'is_wordpress': bool,
            'wp_version': str ou None,
            'vulnerabilities': List[Dict],
            'error': str ou None
        }
    """
    # 1. Detecção de WordPress
    # 2. Verificação de arquivos sensíveis
    # 3. User enumeration
    # 4. Directory listing
```

### tasks.py - Integração

```python
# Executa scan WordPress (somente se site estiver online)
if result.is_online:
    wp_health = check_wordpress_health(site.domain, timeout=5)
    site.is_wordpress = wp_health['is_wordpress']
    site.wp_version = wp_health['wp_version']
    
    if wp_health['vulnerabilities']:
        site.vulnerabilities_found = json.dumps(wp_health['vulnerabilities'])
        
        # Envia alerta para vulnerabilidades críticas
        critical_vulns = [v for v in wp_health['vulnerabilities'] 
                         if v.get('severity') in ['critical', 'high']]
        if critical_vulns:
            send_telegram_alert(message, owner.telegram_chat_id)
```

## 🚀 Como Usar

1. **Cadastre um site WordPress** no sistema
2. **Aguarde o primeiro scan** (executado automaticamente)
3. **Verifique o Dashboard**:
   - Badge "WordPress" aparecerá se detectado
   - Badge de vulnerabilidades se houver problemas
4. **Clique no badge de vulnerabilidades** para ver detalhes
5. **Receba alertas** via Telegram para problemas críticos

## 🆘 Como Corrigir Vulnerabilidades

### 1. Debug Log Exposto
```apache
# Adicione no .htaccess
<Files debug.log>
    Order allow,deny
    Deny from all
</Files>
```

Ou desative debug no `wp-config.php`:
```php
define('WP_DEBUG', false);
define('WP_DEBUG_LOG', false);
```

### 2. Backup de Configuração Exposto
```bash
# Remova os arquivos de backup
rm wp-config.php.bak
rm wp-config.php.old
```

### 3. User Enumeration via API
Adicione no `functions.php`:
```php
// Desabilita REST API para usuários não autenticados
add_filter('rest_authentication_errors', function($result) {
    if (!is_user_logged_in()) {
        return new WP_Error(
            'rest_not_logged_in', 
            'Você precisa estar logado para acessar a API.', 
            array('status' => 401)
        );
    }
    return $result;
});
```

### 4. XML-RPC Ativo
```apache
# Bloqueie no .htaccess
<Files xmlrpc.php>
    Order Deny,Allow
    Deny from all
</Files>
```

Ou use um plugin como "Disable XML-RPC".

### 5. Directory Listing
```apache
# Desabilite no .htaccess
Options -Indexes
```

### 6. Git Exposto
```apache
# Bloqueie no .htaccess
RedirectMatch 404 /\.git
```

Ou remova o diretório:
```bash
rm -rf .git
```

## 📈 Níveis de Severidade

| Severidade | Cor | Ação Requerida |
|------------|-----|----------------|
| **CRÍTICO** | 🔴 Vermelho Escuro | Ação IMEDIATA - Risco de comprometimento total |
| **ALTO** | 🔴 Vermelho | Ação URGENTE - Risco de exposição de dados |
| **MÉDIO** | 🟡 Laranja | Ação NECESSÁRIA - Risco moderado |
| **BAIXO** | 🟢 Amarelo | Ação RECOMENDADA - Melhor prática |

## 🔒 Boas Práticas WordPress

1. **Sempre atualize** o WordPress e plugins
2. **Use senhas fortes** e 2FA
3. **Limite tentativas de login**
4. **Desabilite editor de arquivos** no painel
5. **Use certificado SSL** (HTTPS)
6. **Faça backups regulares**
7. **Use plugins de segurança** (Wordfence, iThemes Security)
8. **Configure permissões corretas** nos arquivos (644/755)
9. **Oculte versão do WordPress**
10. **Use .htaccess para proteção adicional**

## 📚 Referências

- [WordPress Hardening](https://wordpress.org/support/article/hardening-wordpress/)
- [OWASP WordPress Security](https://owasp.org/www-project-web-security-testing-guide/)
- [Sucuri WordPress Security Guide](https://sucuri.net/guides/wordpress-security/)
- [WPScan](https://wpscan.com/)

## 🔍 Exemplo de Scan Completo

```json
{
  "is_wordpress": true,
  "wp_version": "6.4.2",
  "vulnerabilities": [
    {
      "type": "backup_config",
      "file": "/wp-config.php.bak",
      "description": "Backup do wp-config.php acessível",
      "severity": "critical",
      "risk": "Contém credenciais do banco de dados",
      "url": "https://example.com/wp-config.php.bak"
    },
    {
      "type": "debug_log",
      "file": "/wp-content/debug.log",
      "description": "Debug log do WordPress exposto",
      "severity": "high",
      "risk": "Pode conter credenciais, paths do servidor e informações sensíveis",
      "url": "https://example.com/wp-content/debug.log"
    },
    {
      "type": "user_enumeration",
      "endpoint": "/wp-json/wp/v2/users",
      "description": "Enumeração de usuários via REST API",
      "severity": "medium",
      "risk": "Expõe usernames que podem ser usados em ataques de brute force",
      "users_found": 5,
      "sample_users": ["admin", "editor", "author", "contributor", "subscriber"],
      "url": "https://example.com/wp-json/wp/v2/users"
    },
    {
      "type": "xmlrpc_enabled",
      "file": "/xmlrpc.php",
      "description": "XML-RPC ativo (possível vetor de ataque)",
      "severity": "medium",
      "risk": "Pode ser usado para brute force e DDoS",
      "url": "https://example.com/xmlrpc.php"
    }
  ],
  "error": null
}
```

---

**🛡️ SentinelWeb WordPress Scanner** - Proteja seu site WordPress com monitoramento contínuo de segurança!
