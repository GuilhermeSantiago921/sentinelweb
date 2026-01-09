# Verificação de Blacklist (RBL) - Real-time Blackhole List

## 📋 Visão Geral

O SentinelWeb agora inclui verificação automática de **Blacklists (RBL - Real-time Blackhole List)** para detectar se o IP do seu domínio está listado em listas de bloqueio conhecidas.

## 🎯 Para que serve?

As **RBLs** são listas públicas de IPs que foram reportados por:
- Envio de spam
- Atividades maliciosas
- Servidores comprometidos
- Comportamento suspeito

Se seu IP estiver em uma blacklist, você pode enfrentar:
- ❌ Emails sendo bloqueados ou indo para spam
- ❌ Problemas de reputação do domínio
- ❌ Restrições de acesso a alguns serviços
- ❌ Bloqueio por firewalls e filtros

## 🔍 Como funciona?

A verificação RBL segue este processo:

1. **Resolve o IP** do domínio (DNS lookup)
2. **Inverte o IP** (ex: `1.2.3.4` vira `4.3.2.1`)
3. **Consulta DNS** em cada RBL: `4.3.2.1.zen.spamhaus.org`
4. **Se houver resposta**, o IP está listado naquela RBL
5. **Se NXDOMAIN**, o IP NÃO está listado (tudo ok!)

## 🛡️ RBLs Verificadas

O SentinelWeb verifica as seguintes blacklists populares:

| RBL | Descrição |
|-----|-----------|
| **zen.spamhaus.org** | Spamhaus (mais popular e confiável) |
| **bl.spamcop.net** | SpamCop (reportes comunitários) |
| **b.barracudacentral.org** | Barracuda (spam e malware) |
| **dnsbl.sorbs.net** | SORBS (diversos tipos de abuso) |
| **cbl.abuseat.org** | Composite Blocking List |

## 📊 Campos no Banco de Dados

Foram adicionados dois novos campos na tabela `Site`:

```python
is_blacklisted: Boolean       # True se está em alguma blacklist
blacklisted_in: Text          # Lista JSON das RBLs onde foi encontrado
```

## 🔔 Alertas Telegram

Se seu site for detectado em uma blacklist, você receberá um alerta via Telegram:

```
🚨 ALERTA - BLACKLIST DETECTADA

🌐 Site: Meu Site
🔗 Domínio: meusite.com.br
⏰ Horário: 07/01/2026 10:30:45 UTC
⚠️ Blacklists: zen.spamhaus.org, bl.spamcop.net

Seu IP está listado em uma ou mais blacklists.
Isso pode afetar a reputação e entrega de emails.
```

## 🎨 Visualização no Dashboard

Sites em blacklist aparecem com um **badge vermelho pulsante**:

```
[ONLINE] [BLACKLISTED] 🚨
```

## ⚡ Performance e Timeouts

Para evitar travamentos, a verificação RBL usa:

- **Timeout de 2 segundos** por consulta DNS
- **Processamento em background** (não trava a API)
- **Ignora falhas** de RBLs individuais (continua verificando os outros)
- **Try-catch** para não quebrar o monitoramento

## 🔧 Instalação da Dependência

A nova biblioteca `dnspython` foi adicionada:

```bash
pip install dnspython==2.4.2
```

## 📝 Código Principal

### scanner.py - Função check_blacklist()

```python
def check_blacklist(domain: str, timeout: float = 2.0) -> Tuple[bool, List[str]]:
    """
    Verifica se o domínio está listado em blacklists (RBL).
    
    Returns:
        Tuple[bool, List[str]]: (is_blacklisted, lista_de_RBLs)
    """
    # Lista de RBLs para verificar
    RBL_PROVIDERS = [
        "zen.spamhaus.org",
        "bl.spamcop.net",
        "b.barracudacentral.org",
        "dnsbl.sorbs.net",
        "cbl.abuseat.org",
    ]
    
    # Resolve IP e consulta cada RBL
    # ...
```

### tasks.py - Integração no monitoramento

```python
# Verifica se está em blacklist (RBL)
try:
    is_blacklisted, blacklisted_in_list = check_blacklist(site.domain, timeout=2.0)
    site.is_blacklisted = is_blacklisted
    
    if blacklisted_in_list:
        site.blacklisted_in = json.dumps(blacklisted_in_list)
        
    # Envia alerta Telegram se detectado
    if is_blacklisted:
        send_telegram_alert(message, owner.telegram_chat_id)
except Exception as e:
    # Não quebra o monitoramento se RBL falhar
    site.is_blacklisted = False
```

## 🚀 Como Usar

1. **Cadastre um site** normalmente no sistema
2. **Aguarde o primeiro scan** (executado automaticamente)
3. **Verifique o Dashboard** - se houver blacklist, aparecerá o badge
4. **Receba alertas** via Telegram (se configurado)

## 🆘 O que fazer se for detectado?

Se seu IP estiver em uma blacklist:

1. **Identifique a causa**:
   - Servidor comprometido?
   - Emails de spam sendo enviados?
   - Malware no site?

2. **Corrija o problema**:
   - Limpe o servidor
   - Mude senhas
   - Atualize software vulnerável
   - Configure SPF, DKIM, DMARC

3. **Solicite remoção**:
   - Cada RBL tem seu processo de delist
   - Spamhaus: https://www.spamhaus.org/lookup/
   - SpamCop: https://www.spamcop.net/bl.shtml

4. **Monitore**:
   - O SentinelWeb continuará verificando
   - Você será notificado quando sair da blacklist

## 🔒 Segurança

- Todas as consultas DNS são **read-only**
- Não há envio de dados dos seus sites
- As RBLs são **públicas e gratuitas**
- Timeout curto previne DoS acidental

## 📚 Referências

- [Spamhaus](https://www.spamhaus.org/)
- [SpamCop](https://www.spamcop.net/)
- [SORBS](http://www.sorbs.net/)
- [RFC 5782 - DNS Blacklists](https://tools.ietf.org/html/rfc5782)

---

**SentinelWeb** - Monitoramento Completo de Sites 🛡️
