"""
SentinelWeb - Engine de Monitoramento (Scanner)
===============================================
Este módulo contém toda a lógica de verificação de segurança:
- Check de Uptime (HTTP Status)
- Verificação de Certificado SSL
- Scan de Portas Críticas

IMPORTANTE: Todas as funções usam timeouts curtos (5s) para não travar
a fila de processamento se um site estiver offline ou lento.
"""

import socket
import ssl
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import httpx
from OpenSSL import crypto
import asyncio
import os
import requests
import whois
import re
import dns.resolver  # Para verificação de blacklist (RBL)


# Timeout padrão para todas as operações de rede (em segundos)
DEFAULT_TIMEOUT = 5

# Token do Bot do Telegram (configurado via variável de ambiente)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Portas críticas que devem ser monitoradas
# Essas portas abertas podem representar riscos de segurança
CRITICAL_PORTS = {
    21: "FTP",      # File Transfer Protocol - transferência de arquivos sem criptografia
    22: "SSH",      # Secure Shell - acesso remoto (pode ser legítimo, mas monitoramos)
    23: "Telnet",   # Protocolo antigo sem criptografia - alto risco
    3306: "MySQL",  # Banco de dados MySQL exposto - risco crítico
    5432: "PostgreSQL",  # Banco de dados PostgreSQL exposto - risco crítico
    27017: "MongoDB",    # Banco de dados MongoDB exposto - risco crítico
    6379: "Redis",       # Redis exposto - risco crítico
}


@dataclass
class ScanResult:
    """
    Classe que encapsula todos os resultados de uma verificação.
    Facilita o transporte de dados entre funções.
    """
    # Uptime Check
    is_online: bool = False
    http_status_code: Optional[int] = None
    latency_ms: Optional[float] = None
    
    # SSL Check
    ssl_valid: Optional[bool] = None
    ssl_days_remaining: Optional[int] = None
    ssl_issuer: Optional[str] = None
    ssl_error: Optional[str] = None
    
    # Port Scan
    open_ports: List[int] = None
    
    # Erro geral
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.open_ports is None:
            self.open_ports = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização"""
        return {
            "is_online": self.is_online,
            "http_status_code": self.http_status_code,
            "latency_ms": self.latency_ms,
            "ssl_valid": self.ssl_valid,
            "ssl_days_remaining": self.ssl_days_remaining,
            "ssl_issuer": self.ssl_issuer,
            "ssl_error": self.ssl_error,
            "open_ports": self.open_ports,
            "error_message": self.error_message,
        }


def send_telegram_alert(message: str, chat_id: str) -> bool:
    """
    Envia um alerta via Telegram Bot API.
    
    Args:
        message: Mensagem a ser enviada
        chat_id: ID do chat do Telegram do usuário
    
    Returns:
        True se enviado com sucesso, False caso contrário
    
    Security Notes:
        - Usa HTTPS por padrão
        - Token deve estar em variável de ambiente
        - Timeout de 10 segundos para evitar travamento
    """
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️  TELEGRAM_BOT_TOKEN não configurado. Alerta não enviado.")
        return False
    
    if not chat_id:
        print("⚠️  chat_id não fornecido. Alerta não enviado.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"  # Permite formatação HTML na mensagem
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Alerta Telegram enviado para chat_id {chat_id}")
            return True
        else:
            print(f"❌ Erro ao enviar alerta Telegram: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Exceção ao enviar alerta Telegram: {e}")
        return False


def check_domain_expiration(domain: str) -> Optional[datetime]:
    """
    Verifica a data de expiração do domínio usando Whois.
    
    Args:
        domain: O domínio a verificar (sem protocolo, ex: "google.com")
    
    Returns:
        datetime: Data de expiração do domínio, ou None se não conseguir obter
    
    Notes:
        - Remove protocolo (http://, https://) e paths da URL
        - O campo expiration_date pode retornar lista ou string
        - Em caso de erro (domínio inválido, timeout, etc), retorna None
        - Não quebra a execução do monitoramento se falhar
    
    Examples:
        >>> check_domain_expiration("google.com")
        datetime(2024, 9, 14, 4, 0)
        
        >>> check_domain_expiration("invalido-xyz-123.com")
        None
    """
    try:
        # Limpa o domínio: remove protocolo, www, paths e querystrings
        clean_domain = domain.lower()
        clean_domain = re.sub(r'^https?://', '', clean_domain)
        clean_domain = re.sub(r'^www\.', '', clean_domain)
        clean_domain = clean_domain.split('/')[0]  # Removes path
        clean_domain = clean_domain.split('?')[0]  # Removes query string
        
        if not clean_domain:
            print(f"⚠️  Domínio vazio após limpeza: {domain}")
            return None
        
        print(f"🔍 Consultando Whois para: {clean_domain}")
        
        # Faz a consulta Whois
        w = whois.whois(clean_domain)
        
        if not w:
            print(f"⚠️  Whois retornou vazio para: {clean_domain}")
            return None
        
        expiration = w.expiration_date
        
        # O campo expiration_date pode ser:
        # - None (não encontrado)
        # - datetime (único)
        # - Lista de datetime (múltiplas datas)
        # - String (algumas bibliotecas retornam string)
        
        if expiration is None:
            print(f"⚠️  Data de expiração não encontrada para: {clean_domain}")
            return None
        
        # Se for lista, pega a primeira data (geralmente a mais próxima)
        if isinstance(expiration, list):
            if len(expiration) > 0:
                expiration = expiration[0]
            else:
                print(f"⚠️  Lista de expiração vazia para: {clean_domain}")
                return None
        
        # Se for string, tenta converter para datetime
        if isinstance(expiration, str):
            from dateutil import parser
            expiration = parser.parse(expiration)
        
        # Verifica se é datetime válido
        if isinstance(expiration, datetime):
            print(f"✅ Data de expiração encontrada: {expiration.strftime('%Y-%m-%d')} para {clean_domain}")
            return expiration
        else:
            print(f"⚠️  Tipo de data inválido para {clean_domain}: {type(expiration)}")
            return None
            
    except whois.parser.PywhoisError as e:
        print(f"❌ Erro Whois para {domain}: {e}")
        return None
    except Exception as e:
        print(f"❌ Erro inesperado ao consultar Whois para {domain}: {e}")
        return None


def check_blacklist(domain: str, timeout: float = 2.0) -> Tuple[bool, List[str]]:
    """
    Verifica se o domínio está listado em blacklists (RBL - Real-time Blackhole List).
    
    Como funciona:
    1. Resolve o IP do domínio
    2. Inverte o IP (ex: 1.2.3.4 vira 4.3.2.1)
    3. Consulta o IP invertido em listas RBL conhecidas
    4. Se houver resposta DNS, o IP está listado
    
    Args:
        domain: Domínio a verificar (sem protocolo, ex: "google.com")
        timeout: Timeout para cada consulta DNS (padrão: 2 segundos)
    
    Returns:
        Tuple[bool, List[str]]: (is_blacklisted, lista_de_blacklists_onde_foi_encontrado)
    
    Security Notes:
        - Usa timeout curto (2s) para não travar o worker
        - Verifica múltiplas blacklists populares
        - Remove protocolo e paths da URL
        - Retorna lista vazia se não estiver em nenhuma blacklist
    
    Example:
        >>> check_blacklist("malicious-site.com")
        (True, ["zen.spamhaus.org", "bl.spamcop.net"])
        
        >>> check_blacklist("google.com")
        (False, [])
    """
    # Lista de RBLs populares para verificar
    RBL_PROVIDERS = [
        "zen.spamhaus.org",      # Spamhaus (mais popular)
        "bl.spamcop.net",        # SpamCop
        "b.barracudacentral.org", # Barracuda
        "dnsbl.sorbs.net",       # SORBS
        "cbl.abuseat.org",       # Composite Blocking List
    ]
    
    # Remove protocolo e paths da URL
    clean_domain = re.sub(r'^https?://', '', domain)
    clean_domain = re.sub(r'^www\.', '', clean_domain)
    clean_domain = clean_domain.split('/')[0]
    
    blacklisted_in = []
    
    try:
        # 1. Resolve o IP do domínio
        ip_address = socket.gethostbyname(clean_domain)
        print(f"🔍 IP resolvido para {clean_domain}: {ip_address}")
        
        # 2. Inverte o IP (1.2.3.4 -> 4.3.2.1)
        octets = ip_address.split('.')
        reversed_ip = '.'.join(reversed(octets))
        
        # 3. Verifica em cada RBL
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout
        
        for rbl in RBL_PROVIDERS:
            query = f"{reversed_ip}.{rbl}"
            
            try:
                # Se a consulta retornar resultado, o IP está listado
                answers = resolver.resolve(query, 'A')
                
                if answers:
                    print(f"⚠️  BLACKLIST DETECTADA: {clean_domain} ({ip_address}) listado em {rbl}")
                    blacklisted_in.append(rbl)
                    
            except dns.resolver.NXDOMAIN:
                # NXDOMAIN significa que NÃO está listado (resposta esperada)
                pass
            except dns.resolver.NoAnswer:
                # Sem resposta, também significa que não está listado
                pass
            except dns.resolver.Timeout:
                # Timeout na consulta, ignora este RBL
                print(f"⏱️  Timeout ao consultar {rbl} para {clean_domain}")
                pass
            except Exception as e:
                # Outros erros, ignora este RBL
                print(f"⚠️  Erro ao consultar {rbl}: {e}")
                pass
        
        # Resultado final
        is_blacklisted = len(blacklisted_in) > 0
        
        if is_blacklisted:
            print(f"🚨 ALERTA: {clean_domain} está em {len(blacklisted_in)} blacklist(s): {', '.join(blacklisted_in)}")
        else:
            print(f"✅ {clean_domain} não está em nenhuma blacklist verificada")
        
        return is_blacklisted, blacklisted_in
        
    except socket.gaierror:
        # Não conseguiu resolver o domínio (pode estar offline ou inválido)
        print(f"⚠️  Não foi possível resolver IP para {clean_domain}")
        return False, []
    except Exception as e:
        print(f"❌ Erro inesperado ao verificar blacklist para {domain}: {e}")
        return False, []


def check_seo_health(domain: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    Verifica se o site está bloqueando motores de busca (Google/Bing).
    
    VERIFICAÇÕES CRÍTICAS:
    1. Meta tag noindex no HTML
    2. HTTP Header X-Robots-Tag
    3. Robots.txt bloqueando tudo (Disallow: /)
    
    Args:
        domain: Domínio a verificar (sem protocolo, ex: "example.com")
        timeout: Timeout para cada requisição (padrão: 5 segundos)
    
    Returns:
        Dict com:
        - indexable: bool (True = OK, False = BLOQUEADO)
        - issues: List[str] com problemas encontrados
        - robots_txt_content: str com conteúdo do robots.txt (se existir)
        - error: str ou None se houver erro
    
    Example:
        >>> check_seo_health("example.com")
        {
            'indexable': False,
            'issues': ['Meta tag noindex encontrada', 'Robots.txt bloqueia o site'],
            'robots_txt_content': 'User-agent: *\\nDisallow: /',
            'error': None
        }
    """
    url = f"https://{domain}"
    result = {
        'indexable': True,
        'issues': [],
        'robots_txt_content': None,
        'error': None
    }
    
    try:
        # ============================================
        # CHECK 1: Meta Tag Noindex no HTML
        # ============================================
        print(f"🔍 Verificando meta tags SEO em {domain}...")
        
        try:
            response = httpx.get(
                url,
                timeout=timeout,
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; SentinelWeb SEO Checker/1.0)'
                }
            )
            
            html_content = response.text.lower()
            
            # Regex para encontrar meta tags robots/googlebot com noindex
            # Exemplos que devem pegar:
            # <meta name="robots" content="noindex">
            # <meta name="robots" content="noindex, nofollow">
            # <meta name="googlebot" content="noindex">
            # <meta name="ROBOTS" content="NOINDEX, NOFOLLOW">
            
            meta_robots_pattern = r'<meta\s+name=["\']?(robots|googlebot)["\']?\s+content=["\']?[^"\']*noindex[^"\']*["\']?'
            
            if re.search(meta_robots_pattern, html_content, re.IGNORECASE):
                result['indexable'] = False
                result['issues'].append('🚨 Meta tag noindex encontrada no HTML')
                print(f"  ❌ Meta tag noindex detectada!")
            else:
                print(f"  ✅ Nenhuma meta tag noindex encontrada")
            
            # ============================================
            # CHECK 2: HTTP Header X-Robots-Tag
            # ============================================
            print(f"🔍 Verificando HTTP headers...")
            
            x_robots_tag = response.headers.get('X-Robots-Tag', '').lower()
            
            if 'noindex' in x_robots_tag:
                result['indexable'] = False
                result['issues'].append(f'🚨 HTTP Header X-Robots-Tag: {x_robots_tag}')
                print(f"  ❌ X-Robots-Tag com noindex detectado: {x_robots_tag}")
            else:
                print(f"  ✅ Header X-Robots-Tag OK")
        
        except httpx.HTTPError as e:
            print(f"  ⚠️ Erro ao buscar HTML: {e}")
            result['error'] = f"Erro HTTP: {str(e)}"
        
        # ============================================
        # CHECK 3: Robots.txt Global Disallow
        # ============================================
        print(f"🔍 Verificando robots.txt...")
        
        try:
            robots_url = f"{url}/robots.txt"
            robots_response = httpx.get(
                robots_url,
                timeout=timeout,
                follow_redirects=False,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; SentinelWeb SEO Checker/1.0)'
                }
            )
            
            if robots_response.status_code == 200:
                robots_content = robots_response.text
                result['robots_txt_content'] = robots_content
                
                print(f"  ✅ Robots.txt encontrado ({len(robots_content)} bytes)")
                
                # Verifica bloqueio global (User-agent: * + Disallow: /)
                # Regex para detectar:
                # User-agent: *
                # Disallow: /
                
                # Normaliza o conteúdo (remove espaços extras e case-insensitive)
                normalized_content = robots_content.lower()
                
                # Procura por User-agent: * seguido de Disallow: /
                # Permite espaços e quebras de linha entre as diretivas
                global_block_pattern = r'user-agent:\s*\*\s*.*?disallow:\s*/'
                
                if re.search(global_block_pattern, normalized_content, re.DOTALL):
                    result['indexable'] = False
                    result['issues'].append('🚨 Robots.txt bloqueia o site inteiro (Disallow: /)')
                    print(f"  ❌ Bloqueio global detectado no robots.txt!")
                else:
                    # Verifica se tem Disallow: / sem User-agent específico antes
                    lines = robots_content.split('\n')
                    user_agent_star = False
                    
                    for line in lines:
                        line_clean = line.strip().lower()
                        
                        if line_clean.startswith('user-agent:'):
                            if '*' in line_clean:
                                user_agent_star = True
                            else:
                                user_agent_star = False
                        
                        if user_agent_star and line_clean.startswith('disallow:'):
                            disallow_value = line_clean.split('disallow:')[1].strip()
                            if disallow_value == '/':
                                result['indexable'] = False
                                result['issues'].append('🚨 Robots.txt bloqueia o site inteiro (Disallow: /)')
                                print(f"  ❌ Bloqueio global detectado no robots.txt!")
                                break
                    else:
                        print(f"  ✅ Robots.txt não bloqueia o site")
            else:
                print(f"  ℹ️ Robots.txt não encontrado (Status: {robots_response.status_code})")
        
        except httpx.HTTPError as e:
            print(f"  ℹ️ Robots.txt não acessível: {e}")
        
        # ============================================
        # RESULTADO FINAL
        # ============================================
        if result['indexable']:
            print(f"✅ SEO Health Check: Site INDEXÁVEL")
        else:
            print(f"❌ SEO Health Check: Site BLOQUEADO - {len(result['issues'])} problemas encontrados")
        
        return result
    
    except Exception as e:
        print(f"❌ Erro inesperado no SEO Health Check para {domain}: {e}")
        result['error'] = str(e)
        result['indexable'] = True  # Assume OK em caso de erro (não queremos falso positivo)
        return result


def check_wordpress_health(domain: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    Verifica se o site é WordPress e realiza scan de segurança.
    
    Testes realizados:
    1. Detecção de WordPress e versão
    2. Arquivos sensíveis expostos
    3. User enumeration via API
    4. Debug log exposto
    
    Args:
        domain: Domínio a verificar (sem protocolo, ex: "example.com")
        timeout: Timeout para cada requisição (padrão: 5 segundos)
    
    Returns:
        Dict com:
        - is_wordpress: bool
        - wp_version: str ou None
        - vulnerabilities: List[Dict] com detalhes das vulnerabilidades
        - error: str ou None se houver erro
    
    Security Notes:
        - Usa User-Agent profissional para evitar bloqueios
        - Timeout curto para não travar o worker
        - Verifica apenas arquivos comuns (não é invasivo)
        - Não tenta explorar vulnerabilidades, apenas detecta
    
    Example:
        >>> check_wordpress_health("wordpress-site.com")
        {
            'is_wordpress': True,
            'wp_version': '6.4.2',
            'vulnerabilities': [
                {'type': 'debug_log', 'file': '/wp-content/debug.log', 'severity': 'high'},
                {'type': 'user_enumeration', 'endpoint': '/wp-json/wp/v2/users', 'severity': 'medium'}
            ],
            'error': None
        }
    """
    # Remove protocolo e paths da URL
    clean_domain = re.sub(r'^https?://', '', domain)
    clean_domain = re.sub(r'^www\.', '', clean_domain)
    clean_domain = clean_domain.split('/')[0]
    
    # Tenta HTTPS primeiro, depois HTTP
    protocols = ['https', 'http']
    
    result = {
        'is_wordpress': False,
        'wp_version': None,
        'vulnerabilities': [],
        'error': None
    }
    
    # Headers profissionais para evitar bloqueios
    headers = {
        'User-Agent': 'SentinelWeb-SecurityScanner/1.0 (WordPress Health Check)',
        'Accept': 'text/html,application/json,*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    base_url = None
    
    # Tenta conectar com HTTPS, depois HTTP
    for protocol in protocols:
        try:
            test_url = f"{protocol}://{clean_domain}"
            response = requests.get(test_url, headers=headers, timeout=timeout, allow_redirects=True, verify=False)
            
            if response.status_code < 400:
                base_url = test_url
                break
        except Exception:
            continue
    
    if not base_url:
        result['error'] = "Não foi possível conectar ao site"
        return result
    
    try:
        # ========================================
        # TESTE 1: Detecção de WordPress e Versão
        # ========================================
        
        # 1.1 - Verifica meta generator no HTML principal
        try:
            response = requests.get(base_url, headers=headers, timeout=timeout, allow_redirects=True, verify=False)
            html_content = response.text.lower()
            
            # Procura por indicadores de WordPress
            wp_indicators = [
                '/wp-content/',
                '/wp-includes/',
                'wordpress',
                'wp-json'
            ]
            
            has_wp_indicators = any(indicator in html_content for indicator in wp_indicators)
            
            # Procura versão no meta generator
            version_match = re.search(r'<meta name="generator" content="wordpress\s+([0-9.]+)"', html_content)
            if version_match:
                result['is_wordpress'] = True
                result['wp_version'] = version_match.group(1)
                print(f"✅ WordPress detectado via meta generator: versão {result['wp_version']}")
            elif has_wp_indicators:
                result['is_wordpress'] = True
                print(f"✅ WordPress detectado via indicadores no HTML")
                
        except Exception as e:
            print(f"⚠️ Erro ao verificar HTML principal: {e}")
        
        # 1.2 - Tenta acessar readme.html
        if not result['wp_version']:
            try:
                readme_url = f"{base_url}/readme.html"
                response = requests.get(readme_url, headers=headers, timeout=timeout, verify=False)
                
                if response.status_code == 200:
                    result['is_wordpress'] = True
                    # Procura versão no readme
                    version_match = re.search(r'Version\s+([0-9.]+)', response.text, re.IGNORECASE)
                    if version_match:
                        result['wp_version'] = version_match.group(1)
                        print(f"✅ Versão WordPress detectada via readme.html: {result['wp_version']}")
                    else:
                        print(f"✅ WordPress detectado (readme.html acessível)")
            except Exception as e:
                print(f"⚠️ Erro ao verificar readme.html: {e}")
        
        # Se não detectou WordPress, retorna
        if not result['is_wordpress']:
            print(f"ℹ️  {clean_domain} não parece ser WordPress")
            return result
        
        # ========================================
        # TESTE 2: Arquivos Sensíveis Expostos
        # ========================================
        
        sensitive_files = [
            {
                'path': '/wp-content/debug.log',
                'type': 'debug_log',
                'description': 'Debug log do WordPress exposto',
                'severity': 'high',
                'risk': 'Pode conter credenciais, paths do servidor e informações sensíveis'
            },
            {
                'path': '/wp-config.php.bak',
                'type': 'backup_config',
                'description': 'Backup do wp-config.php acessível',
                'severity': 'critical',
                'risk': 'Contém credenciais do banco de dados'
            },
            {
                'path': '/wp-config.php.old',
                'type': 'backup_config',
                'description': 'Backup antigo do wp-config.php',
                'severity': 'critical',
                'risk': 'Contém credenciais do banco de dados'
            },
            {
                'path': '/.git/config',
                'type': 'git_exposed',
                'description': 'Repositório Git exposto',
                'severity': 'high',
                'risk': 'Pode expor código-fonte e histórico de commits'
            },
            {
                'path': '/xmlrpc.php',
                'type': 'xmlrpc_enabled',
                'description': 'XML-RPC ativo (possível vetor de ataque)',
                'severity': 'medium',
                'risk': 'Pode ser usado para brute force e DDoS'
            },
        ]
        
        for file_info in sensitive_files:
            try:
                file_url = f"{base_url}{file_info['path']}"
                response = requests.head(file_url, headers=headers, timeout=timeout, allow_redirects=False, verify=False)
                
                # Se não tem HEAD, tenta GET
                if response.status_code == 405 or response.status_code == 404:
                    response = requests.get(file_url, headers=headers, timeout=timeout, allow_redirects=False, verify=False)
                
                if response.status_code == 200:
                    vulnerability = {
                        'type': file_info['type'],
                        'file': file_info['path'],
                        'description': file_info['description'],
                        'severity': file_info['severity'],
                        'risk': file_info['risk'],
                        'url': file_url
                    }
                    result['vulnerabilities'].append(vulnerability)
                    print(f"🚨 Vulnerabilidade encontrada: {file_info['description']} ({file_url})")
                    
            except Exception as e:
                # Timeout ou erro de conexão é esperado se o arquivo não existe
                pass
        
        # ========================================
        # TESTE 3: User Enumeration via API
        # ========================================
        
        try:
            users_api_url = f"{base_url}/wp-json/wp/v2/users"
            response = requests.get(users_api_url, headers=headers, timeout=timeout, verify=False)
            
            if response.status_code == 200:
                try:
                    users_data = response.json()
                    
                    if isinstance(users_data, list) and len(users_data) > 0:
                        # Extrai usernames
                        usernames = []
                        for user in users_data[:5]:  # Limita a 5 usuários
                            if isinstance(user, dict) and 'slug' in user:
                                usernames.append(user['slug'])
                        
                        vulnerability = {
                            'type': 'user_enumeration',
                            'endpoint': '/wp-json/wp/v2/users',
                            'description': 'Enumeração de usuários via REST API',
                            'severity': 'medium',
                            'risk': 'Expõe usernames que podem ser usados em ataques de brute force',
                            'users_found': len(users_data),
                            'sample_users': usernames,
                            'url': users_api_url
                        }
                        result['vulnerabilities'].append(vulnerability)
                        print(f"🚨 User enumeration detectado: {len(users_data)} usuários expostos")
                        
                except ValueError:
                    # Não é JSON válido
                    pass
                    
        except Exception as e:
            print(f"⚠️ Erro ao verificar API de usuários: {e}")
        
        # ========================================
        # TESTE 4: Directory Listing
        # ========================================
        
        try:
            uploads_url = f"{base_url}/wp-content/uploads/"
            response = requests.get(uploads_url, headers=headers, timeout=timeout, verify=False)
            
            if response.status_code == 200 and 'index of' in response.text.lower():
                vulnerability = {
                    'type': 'directory_listing',
                    'directory': '/wp-content/uploads/',
                    'description': 'Listagem de diretório habilitada',
                    'severity': 'low',
                    'risk': 'Permite navegação nos arquivos do site',
                    'url': uploads_url
                }
                result['vulnerabilities'].append(vulnerability)
                print(f"⚠️ Directory listing habilitado em /wp-content/uploads/")
                
        except Exception as e:
            pass
        
        # ========================================
        # TESTE 5: Plugin CVE Scanner (OSV.dev)
        # ========================================
        
        plugins_with_cves = []
        
        try:
            # Extrai plugins do HTML
            plugins = extract_plugins_from_html(html_content)
            
            if plugins:
                # Verifica CVEs em paralelo usando asyncio
                import asyncio
                plugins_with_cves = asyncio.run(scan_plugins_vulnerabilities(plugins))
                
                # Adiciona vulnerabilidades de plugins ao resultado
                for plugin in plugins_with_cves:
                    if plugin['vulnerabilities']:
                        for cve in plugin['vulnerabilities']:
                            vulnerability = {
                                'type': 'plugin_cve',
                                'plugin_slug': plugin['slug'],
                                'plugin_version': plugin['version'],
                                'cve_id': cve['id'],
                                'description': f"CVE encontrado no plugin {plugin['slug']}",
                                'severity': cve['severity'].lower() if cve['severity'] != 'UNKNOWN' else 'medium',
                                'risk': cve['summary'],
                                'references': cve['references']
                            }
                            result['vulnerabilities'].append(vulnerability)
                
        except Exception as e:
            print(f"⚠️ Erro ao verificar CVEs de plugins: {e}")
        
        # Resultado final
        vuln_count = len(result['vulnerabilities'])
        plugins_count = len(plugins_with_cves)
        
        if vuln_count > 0:
            print(f"🔍 Scan WordPress concluído: {vuln_count} vulnerabilidade(s) encontrada(s)")
        else:
            print(f"✅ Scan WordPress concluído: Nenhuma vulnerabilidade encontrada")
        
        if plugins_count > 0:
            print(f"📦 {plugins_count} plugin(s) detectado(s)")
        
        # Adiciona lista de plugins ao resultado
        result['plugins_detected'] = plugins_with_cves
        
        return result
        
    except Exception as e:
        result['error'] = f"Erro durante scan WordPress: {str(e)}"
        print(f"❌ Erro no WordPress scan para {clean_domain}: {e}")
        return result


def check_uptime(domain: str, timeout: int = DEFAULT_TIMEOUT, must_contain_keyword: Optional[str] = None) -> Tuple[bool, Optional[int], Optional[float], Optional[str]]:
    """
    Verifica se o site está online (HTTP 200) e opcionalmente se contém uma palavra-chave.
    
    Como funciona:
    1. Faz uma requisição HTTP GET para o domínio
    2. Mede o tempo de resposta (latência)
    3. Considera online se status code for 2xx ou 3xx
    4. Se must_contain_keyword for fornecida, verifica se existe no HTML
    
    Args:
        domain: O domínio a verificar (sem protocolo)
        timeout: Tempo máximo de espera em segundos
        must_contain_keyword: Palavra-chave que deve existir no HTML (anti-defacement)
    
    Returns:
        Tuple[is_online, status_code, latency_ms, error_message]
    
    Security Note:
        - Usa timeout curto para evitar DoS na própria aplicação
        - Segue redirects (follow_redirects=True) para pegar status final
        - Verifica SSL por padrão (verify=True)
        - Verificação de keyword detecta possíveis invasões/defacement
    """
    url = f"https://{domain}"
    error_message = None
    
    try:
        start_time = time.time()
        
        # Usa httpx para requisições HTTP modernas
        # verify=False temporariamente para sites com SSL inválido não falharem no uptime check
        with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
            response = client.get(url)
        
        end_time = time.time()
        latency_ms = round((end_time - start_time) * 1000, 2)
        
        # Considera online se status for 2xx ou 3xx
        is_online = 200 <= response.status_code < 400
        
        # 🔍 VERIFICAÇÃO ANTI-DEFACEMENT
        if is_online and must_contain_keyword:
            keyword_found = must_contain_keyword.lower() in response.text.lower()
            
            if not keyword_found:
                # Site retornou 200, mas sem a palavra-chave esperada
                # Possível invasão/defacement!
                is_online = False
                error_message = f"⚠️ POSSÍVEL INVASÃO/DEFACEMENT: Palavra-chave '{must_contain_keyword}' não encontrada no HTML"
                print(f"🚨 ALERTA DE DEFACEMENT: {domain} - Keyword '{must_contain_keyword}' ausente!")
        
        return is_online, response.status_code, latency_ms, error_message
        
    except httpx.TimeoutException:
        return False, None, None, "Timeout na conexão"
    except httpx.ConnectError:
        # Tenta HTTP se HTTPS falhar
        try:
            url = f"http://{domain}"
            start_time = time.time()
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(url)
            end_time = time.time()
            latency_ms = round((end_time - start_time) * 1000, 2)
            is_online = 200 <= response.status_code < 400
            
            # 🔍 VERIFICAÇÃO ANTI-DEFACEMENT (também no HTTP)
            if is_online and must_contain_keyword:
                keyword_found = must_contain_keyword.lower() in response.text.lower()
                
                if not keyword_found:
                    is_online = False
                    error_message = f"⚠️ POSSÍVEL INVASÃO/DEFACEMENT: Palavra-chave '{must_contain_keyword}' não encontrada no HTML"
                    print(f"🚨 ALERTA DE DEFACEMENT: {domain} - Keyword '{must_contain_keyword}' ausente!")
            
            return is_online, response.status_code, latency_ms, error_message
        except:
            return False, None, None, "Erro na conexão HTTP"
    except Exception as e:
        return False, None, None, f"Erro inesperado: {str(e)}"


def check_ssl_certificate(domain: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    Verifica a validade do certificado SSL/TLS.
    
    Como funciona:
    1. Estabelece conexão SSL com o servidor
    2. Obtém o certificado
    3. Verifica data de expiração
    4. Extrai informações do emissor (CA)
    
    Args:
        domain: O domínio a verificar
        timeout: Tempo máximo de espera
    
    Returns:
        Dict com: valid, days_remaining, issuer, error
    
    Security Notes:
        - Certificados expirados ou inválidos são riscos de segurança
        - Alerta se faltar menos de 30 dias para expirar
        - Verifica apenas o certificado, não a cadeia completa (MVP)
    """
    result = {
        "valid": None,
        "days_remaining": None,
        "issuer": None,
        "error": None
    }
    
    try:
        # Cria contexto SSL que aceita qualquer certificado (para inspeção)
        context = ssl.create_default_context()
        
        # Conecta ao servidor na porta 443 (HTTPS)
        with socket.create_connection((domain, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                # Obtém o certificado em formato binário (DER)
                cert_der = ssock.getpeercert(binary_form=True)
                
                # Converte para objeto X509 para análise
                cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_der)
                
                # Data de expiração
                not_after = cert.get_notAfter().decode('utf-8')
                # Formato: YYYYMMDDhhmmssZ
                expiry_date = datetime.strptime(not_after, '%Y%m%d%H%M%SZ')
                
                # Calcula dias restantes
                days_remaining = (expiry_date - datetime.utcnow()).days
                
                # Extrai informações do emissor (CA)
                issuer = cert.get_issuer()
                issuer_str = issuer.CN if issuer.CN else str(issuer)
                
                result["valid"] = days_remaining > 0
                result["days_remaining"] = days_remaining
                result["issuer"] = issuer_str
                
    except ssl.SSLCertVerificationError as e:
        result["valid"] = False
        result["error"] = f"Certificado inválido: {str(e)}"
    except socket.timeout:
        result["error"] = "Timeout ao verificar SSL"
    except socket.gaierror:
        result["error"] = "Não foi possível resolver o domínio"
    except ConnectionRefusedError:
        result["error"] = "Conexão recusada na porta 443"
    except Exception as e:
        result["error"] = f"Erro ao verificar SSL: {str(e)}"
    
    return result


def check_port(host: str, port: int, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """
    Verifica se uma porta específica está aberta.
    
    Como funciona:
    1. Tenta estabelecer conexão TCP na porta
    2. Se conectar, a porta está aberta
    3. Se timeout ou recusar, a porta está fechada
    
    Args:
        host: O domínio ou IP
        port: Número da porta
        timeout: Tempo máximo de espera
    
    Returns:
        True se a porta está aberta, False caso contrário
    
    Security Notes:
        - Portas abertas de bancos de dados são CRÍTICAS
        - FTP (21) e Telnet (23) são inseguros por natureza
        - SSH (22) pode ser legítimo, mas deve ser monitorado
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        # connect_ex retorna 0 se a conexão foi bem sucedida
        return result == 0
        
    except socket.gaierror:
        # Não conseguiu resolver o hostname
        return False
    except socket.timeout:
        return False
    except Exception:
        return False


def scan_critical_ports(domain: str, timeout: int = 2) -> List[int]:
    """
    Escaneia portas críticas que podem representar riscos de segurança.
    
    Args:
        domain: O domínio a escanear
        timeout: Tempo máximo por porta (menor para não demorar)
    
    Returns:
        Lista de portas abertas encontradas
    
    Security Notes:
        - Este scan é básico e não substitui ferramentas como nmap
        - Portas abertas não significam necessariamente vulnerabilidade
        - Mas exposição desnecessária aumenta superfície de ataque
    """
    open_ports = []
    
    # Resolve o domínio para IP primeiro
    try:
        ip = socket.gethostbyname(domain)
    except socket.gaierror:
        return open_ports  # Retorna vazio se não resolver
    
    # Verifica cada porta crítica
    for port in CRITICAL_PORTS.keys():
        if check_port(ip, port, timeout):
            open_ports.append(port)
    
    return open_ports


def full_scan(domain: str, must_contain_keyword: Optional[str] = None) -> ScanResult:
    """
    Executa uma verificação completa do domínio.
    
    Esta é a função principal chamada pelo Celery worker.
    Executa todos os checks em sequência:
    1. Uptime Check (HTTP) + Verificação Anti-Defacement
    2. SSL Check (Certificado)
    3. Port Scan (Portas Críticas)
    
    Args:
        domain: O domínio a verificar
        must_contain_keyword: Palavra-chave que deve existir no HTML (anti-defacement)
    
    Returns:
        ScanResult com todos os dados coletados
    
    Note:
        Usa try/except em cada check para garantir que
        uma falha em um não afete os outros.
    """
    result = ScanResult()
    
    # 1. Verifica Uptime + Anti-Defacement
    try:
        is_online, status_code, latency, error_msg = check_uptime(domain, must_contain_keyword=must_contain_keyword)
        result.is_online = is_online
        result.http_status_code = status_code
        result.latency_ms = latency
        if error_msg:
            result.error_message = error_msg
    except Exception as e:
        result.is_online = False
        result.error_message = f"Erro no check de uptime: {str(e)}"
    
    # 2. Verifica SSL
    try:
        ssl_result = check_ssl_certificate(domain)
        result.ssl_valid = ssl_result["valid"]
        result.ssl_days_remaining = ssl_result["days_remaining"]
        result.ssl_issuer = ssl_result["issuer"]
        result.ssl_error = ssl_result["error"]
    except Exception as e:
        result.ssl_error = f"Erro no check de SSL: {str(e)}"
    
    # 3. Scan de Portas
    try:
        result.open_ports = scan_critical_ports(domain)
    except Exception as e:
        # Não deixa falha no port scan quebrar todo o resultado
        pass
    
    return result


# Versão assíncrona para uso futuro
async def async_full_scan(domain: str) -> ScanResult:
    """
    Versão assíncrona do full_scan.
    Útil para quando migrarmos para workers assíncronos.
    """
    # Por enquanto, apenas wrapper síncrono
    return await asyncio.get_event_loop().run_in_executor(
        None, full_scan, domain
    )


def check_pagespeed(url: str, strategy: str = "mobile", timeout: float = 30.0) -> Dict[str, Any]:
    """
    Verifica a performance de um site usando Google PageSpeed Insights API v5.
    
    Args:
        url: URL completa do site (ex: https://exemplo.com)
        strategy: 'mobile' ou 'desktop'
        timeout: Timeout da requisição (API do Google pode demorar 10-30s)
    
    Returns:
        Dict com scores e métricas:
        {
            "success": bool,
            "performance_score": int (0-100),
            "seo_score": int (0-100),
            "accessibility_score": int (0-100),
            "best_practices_score": int (0-100),
            "metrics": {
                "first_contentful_paint": float (segundos),
                "largest_contentful_paint": float (segundos),
                "cumulative_layout_shift": float,
                "speed_index": float (segundos),
                "total_blocking_time": float (ms)
            },
            "error": str (se houver)
        }
    
    Note:
        - Requer GOOGLE_PAGESPEED_API_KEY no .env
        - Quota gratuita: 25,000 requisições/dia
        - Recomendado: rodar apenas 1x por dia por site
    
    Exemplo:
        result = check_pagespeed("https://exemplo.com", strategy="mobile")
        if result["success"]:
            print(f"Performance Score: {result['performance_score']}/100")
    """
    
    # Pega API Key do ambiente
    api_key = os.getenv("GOOGLE_PAGESPEED_API_KEY", "")
    
    if not api_key:
        return {
            "success": False,
            "error": "GOOGLE_PAGESPEED_API_KEY não configurada no .env",
            "performance_score": None,
            "seo_score": None,
            "accessibility_score": None,
            "best_practices_score": None,
            "metrics": {}
        }
    
    # Garante que a URL tem protocolo
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    
    # API Endpoint
    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    
    # Parâmetros da requisição
    params = {
        "url": url,
        "strategy": strategy,  # mobile ou desktop
        "key": api_key,
        "category": ["performance", "seo", "accessibility", "best-practices"]  # Todas as categorias
    }
    
    try:
        print(f"🚀 Iniciando PageSpeed Insights para {url} ({strategy})...")
        
        response = requests.get(
            api_url,
            params=params,
            timeout=timeout
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extrai os scores (vêm de 0 a 1, convertemos para 0-100)
        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        
        performance_score = None
        seo_score = None
        accessibility_score = None
        best_practices_score = None
        
        if "performance" in categories:
            performance_score = int(categories["performance"]["score"] * 100)
        
        if "seo" in categories:
            seo_score = int(categories["seo"]["score"] * 100)
        
        if "accessibility" in categories:
            accessibility_score = int(categories["accessibility"]["score"] * 100)
        
        if "best-practices" in categories:
            best_practices_score = int(categories["best-practices"]["score"] * 100)
        
        # Extrai métricas Core Web Vitals
        audits = lighthouse.get("audits", {})
        metrics = {}
        
        # First Contentful Paint (FCP)
        if "first-contentful-paint" in audits:
            fcp = audits["first-contentful-paint"].get("numericValue", 0)
            metrics["first_contentful_paint"] = round(fcp / 1000, 2)  # ms para segundos
        
        # Largest Contentful Paint (LCP)
        if "largest-contentful-paint" in audits:
            lcp = audits["largest-contentful-paint"].get("numericValue", 0)
            metrics["largest_contentful_paint"] = round(lcp / 1000, 2)
        
        # Cumulative Layout Shift (CLS)
        if "cumulative-layout-shift" in audits:
            cls = audits["cumulative-layout-shift"].get("numericValue", 0)
            metrics["cumulative_layout_shift"] = round(cls, 3)
        
        # Speed Index
        if "speed-index" in audits:
            si = audits["speed-index"].get("numericValue", 0)
            metrics["speed_index"] = round(si / 1000, 2)
        
        # Total Blocking Time (TBT)
        if "total-blocking-time" in audits:
            tbt = audits["total-blocking-time"].get("numericValue", 0)
            metrics["total_blocking_time"] = round(tbt, 0)  # já está em ms
        
        print(f"✅ PageSpeed concluído - Performance: {performance_score}/100")
        
        return {
            "success": True,
            "performance_score": performance_score,
            "seo_score": seo_score,
            "accessibility_score": accessibility_score,
            "best_practices_score": best_practices_score,
            "metrics": metrics,
            "error": None
        }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Timeout: A API do Google demorou mais de 30 segundos para responder",
            "performance_score": None,
            "seo_score": None,
            "accessibility_score": None,
            "best_practices_score": None,
            "metrics": {}
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Erro na requisição: {str(e)}",
            "performance_score": None,
            "seo_score": None,
            "accessibility_score": None,
            "best_practices_score": None,
            "metrics": {}
        }
    
    except (KeyError, ValueError, TypeError) as e:
        return {
            "success": False,
            "error": f"Erro ao processar resposta da API: {str(e)}",
            "performance_score": None,
            "seo_score": None,
            "accessibility_score": None,
            "best_practices_score": None,
            "metrics": {}
        }


# ============================================
# VISUAL REGRESSION TESTING
# ============================================

async def take_screenshot(url: str, site_id: int, screenshot_type: str = "current") -> Optional[str]:
    """
    Captura um screenshot de uma URL usando Playwright.
    
    Args:
        url: URL completa do site (com http:// ou https://)
        site_id: ID do site no banco de dados
        screenshot_type: Tipo do screenshot ("current", "baseline")
    
    Returns:
        Caminho do arquivo salvo ou None em caso de erro
    
    Performance Notes:
        - Usa chromium headless para menor overhead
        - Timeout de 30s para evitar travar o worker
        - Aguarda networkidle para garantir conteúdo completo
    """
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    
    try:
        # Garante que o diretório existe
        screenshots_dir = "static/screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Define o nome do arquivo
        filename = f"{site_id}_{screenshot_type}.png"
        filepath = os.path.join(screenshots_dir, filename)
        
        # Normaliza a URL
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        async with async_playwright() as p:
            # Lança o browser (chromium é mais leve que firefox/webkit)
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu'
                ]
            )
            
            # Cria um contexto com viewport padrão (desktop)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            # Navega até a página com timeout de 30s
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Aguarda 2s extras para garantir que tudo carregou (JS, imagens lazy)
            await page.wait_for_timeout(2000)
            
            # Tira o screenshot em fullpage
            await page.screenshot(path=filepath, full_page=True)
            
            await browser.close()
            
            return filepath
            
    except PlaywrightTimeout:
        print(f"⏱️  Timeout ao acessar {url} para screenshot")
        return None
        
    except Exception as e:
        print(f"❌ Erro ao tirar screenshot de {url}: {str(e)}")
        return None


def compare_images(img1_path: str, img2_path: str) -> float:
    """
    Compara duas imagens e retorna a porcentagem de diferença.
    
    Args:
        img1_path: Caminho da imagem 1 (baseline)
        img2_path: Caminho da imagem 2 (current)
    
    Returns:
        Float com a porcentagem de diferença (0.0 - 100.0)
        
    Algorithm:
        1. Carrega as imagens com Pillow
        2. Redimensiona para o mesmo tamanho (usa o menor)
        3. Converte para arrays numpy
        4. Calcula a diferença absoluta pixel por pixel
        5. Retorna a média como porcentagem
        
    Performance:
        - Usa numpy para operações vetorizadas (muito rápido)
        - Redimensiona imagens grandes para evitar overhead
    """
    from PIL import Image
    import numpy as np
    
    try:
        # Verifica se os arquivos existem
        if not os.path.exists(img1_path) or not os.path.exists(img2_path):
            print(f"⚠️  Arquivo não encontrado para comparação")
            return 0.0
        
        # Carrega as imagens
        img1 = Image.open(img1_path).convert('RGB')
        img2 = Image.open(img2_path).convert('RGB')
        
        # Se tamanhos forem diferentes, redimensiona para o menor
        if img1.size != img2.size:
            # Pega as dimensões mínimas
            min_width = min(img1.width, img2.width)
            min_height = min(img1.height, img2.height)
            
            img1 = img1.resize((min_width, min_height), Image.Resampling.LANCZOS)
            img2 = img2.resize((min_width, min_height), Image.Resampling.LANCZOS)
        
        # Converte para arrays numpy
        arr1 = np.array(img1, dtype=np.float64)
        arr2 = np.array(img2, dtype=np.float64)
        
        # Calcula a diferença absoluta
        diff = np.abs(arr1 - arr2)
        
        # Calcula a média da diferença (0-255 por canal RGB)
        mean_diff = np.mean(diff)
        
        # Converte para porcentagem (255 = 100%)
        percent_diff = (mean_diff / 255.0) * 100.0
        
        return round(percent_diff, 2)
        
    except Exception as e:
        print(f"❌ Erro ao comparar imagens: {str(e)}")
        return 0.0


def create_diff_image(img1_path: str, img2_path: str, output_path: str) -> bool:
    """
    Cria uma imagem de diferença visual (útil para debug).
    
    Args:
        img1_path: Imagem baseline
        img2_path: Imagem current
        output_path: Onde salvar a imagem de diferença
        
    Returns:
        True se sucesso, False se erro
    """
    from PIL import Image
    import numpy as np
    
    try:
        # Carrega as imagens
        img1 = Image.open(img1_path).convert('RGB')
        img2 = Image.open(img2_path).convert('RGB')
        
        # Redimensiona se necessário
        if img1.size != img2.size:
            min_width = min(img1.width, img2.width)
            min_height = min(img1.height, img2.height)
            img1 = img1.resize((min_width, min_height), Image.Resampling.LANCZOS)
            img2 = img2.resize((min_width, min_height), Image.Resampling.LANCZOS)
        
        # Converte para arrays
        arr1 = np.array(img1, dtype=np.float64)
        arr2 = np.array(img2, dtype=np.float64)
        
        # Calcula a diferença e amplifica para visualização
        diff = np.abs(arr1 - arr2) * 3  # Multiplica por 3 para destacar diferenças
        diff = np.clip(diff, 0, 255)  # Garante que fica no range 0-255
        
        # Converte de volta para imagem
        diff_img = Image.fromarray(diff.astype(np.uint8))
        
        # Salva
        diff_img.save(output_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar imagem de diferença: {str(e)}")
        return False


# ============================================
# PLUGIN CVE SCANNER (OSV.dev Integration)
# ============================================

def extract_plugins_from_html(html_content: str) -> List[Dict[str, str]]:
    """
    Extrai plugins WordPress do HTML usando regex.
    
    Procura por padrões como:
    - /wp-content/plugins/plugin-name/assets/style.css?ver=1.2.3
    - /wp-content/plugins/plugin-name/js/script.js?ver=2.0.1
    
    Args:
        html_content: Conteúdo HTML da página
    
    Returns:
        Lista de dicionários: [{'slug': 'nome-plugin', 'version': '1.2.3'}]
    
    Example:
        >>> html = '<link href="/wp-content/plugins/contact-form-7/includes/css/styles.css?ver=5.9.8" />'
        >>> extract_plugins_from_html(html)
        [{'slug': 'contact-form-7', 'version': '5.9.8'}]
    """
    plugins = {}
    
    # Regex para encontrar plugins com versão
    # Padrão: /wp-content/plugins/PLUGIN-NAME/...?ver=VERSION
    pattern = r'/wp-content/plugins/([a-z0-9\-_]+)/[^"\']*\?ver=([0-9\.]+)'
    
    matches = re.finditer(pattern, html_content, re.IGNORECASE)
    
    for match in matches:
        slug = match.group(1)
        version = match.group(2)
        
        # Guarda apenas a versão mais alta de cada plugin
        if slug not in plugins or version > plugins[slug]:
            plugins[slug] = version
    
    # Converte para lista de dicionários
    result = [
        {'slug': slug, 'version': version}
        for slug, version in plugins.items()
    ]
    
    print(f"🔍 Plugins detectados: {len(result)}")
    for plugin in result:
        print(f"   - {plugin['slug']} v{plugin['version']}")
    
    return result


async def check_cves_osv_async(slug: str, version: str) -> List[Dict[str, Any]]:
    """
    Consulta a API do OSV.dev para verificar CVEs de um plugin.
    
    Args:
        slug: Nome do plugin (ex: 'contact-form-7')
        version: Versão do plugin (ex: '5.9.8')
    
    Returns:
        Lista de vulnerabilidades encontradas:
        [
            {
                'id': 'CVE-2023-1234',
                'summary': 'SQL Injection vulnerability',
                'severity': 'HIGH',
                'references': ['https://...']
            }
        ]
    """
    url = "https://api.osv.dev/v1/query"
    
    # Formato do package name para WordPress plugins no OSV.dev
    payload = {
        "package": {
            "name": slug,  # OSV.dev usa o slug direto para WordPress plugins
            "ecosystem": "WordPress"
        },
        "version": version
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            # Se não há vulnerabilidades, a resposta vem vazia
            if "vulns" not in data or not data["vulns"]:
                return []
            
            vulnerabilities = []
            
            for vuln in data["vulns"]:
                # Extrai severidade (pode não estar presente)
                severity = "UNKNOWN"
                if "severity" in vuln:
                    if isinstance(vuln["severity"], list) and len(vuln["severity"]) > 0:
                        severity = vuln["severity"][0].get("type", "UNKNOWN")
                
                # Extrai referências (links para mais informações)
                references = []
                if "references" in vuln:
                    references = [ref.get("url", "") for ref in vuln["references"] if "url" in ref]
                
                vulnerabilities.append({
                    "id": vuln.get("id", "UNKNOWN"),
                    "summary": vuln.get("summary", "No description available"),
                    "severity": severity,
                    "references": references[:3]  # Limita a 3 referências
                })
            
            return vulnerabilities
            
    except Exception as e:
        print(f"⚠️ Erro ao consultar OSV.dev para {slug}@{version}: {e}")
        return []


async def scan_plugins_vulnerabilities(plugins: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Verifica vulnerabilidades de múltiplos plugins em paralelo.
    
    Args:
        plugins: Lista de plugins [{'slug': 'nome', 'version': '1.0'}]
    
    Returns:
        Lista de plugins com vulnerabilidades:
        [
            {
                'slug': 'contact-form-7',
                'version': '5.9.8',
                'vulnerabilities': [...]
            }
        ]
    """
    if not plugins:
        return []
    
    print(f"🔒 Verificando vulnerabilidades de {len(plugins)} plugins...")
    
    # Cria tasks para verificar todos os plugins em paralelo
    tasks = [
        check_cves_osv_async(plugin['slug'], plugin['version'])
        for plugin in plugins
    ]
    
    # Executa todas as consultas em paralelo
    results = await asyncio.gather(*tasks)
    
    # Combina plugins com seus CVEs
    plugins_with_cves = []
    for i, plugin in enumerate(plugins):
        vulnerabilities = results[i]
        
        plugin_data = {
            'slug': plugin['slug'],
            'version': plugin['version'],
            'vulnerabilities': vulnerabilities
        }
        
        plugins_with_cves.append(plugin_data)
        
        if vulnerabilities:
            print(f"   🚨 {plugin['slug']} v{plugin['version']}: {len(vulnerabilities)} vulnerabilidade(s) encontrada(s)")
        else:
            print(f"   ✅ {plugin['slug']} v{plugin['version']}: Nenhuma vulnerabilidade conhecida")
    
    return plugins_with_cves


def audit_security_headers(headers: dict) -> Dict[str, Any]:
    """
    Audita headers de segurança HTTP e dá uma nota.
    
    Args:
        headers: Dict com headers HTTP da resposta
    
    Returns:
        {
            'grade': 'A' | 'B' | 'C' | 'F',
            'score': 100,
            'headers_found': [...],
            'headers_missing': [...],
            'recommendations': [...]
        }
    """
    critical_headers = {
        'strict-transport-security': 'HSTS - Força HTTPS',
        'content-security-policy': 'CSP - Previne XSS',
        'x-frame-options': 'Previne Clickjacking',
        'x-content-type-options': 'Previne MIME Sniffing',
        'referrer-policy': 'Controla informações de referência',
        'permissions-policy': 'Controla permissões de recursos'
    }
    
    headers_lower = {k.lower(): v for k, v in headers.items()}
    found = []
    missing = []
    
    for header, description in critical_headers.items():
        if header in headers_lower:
            found.append({
                'header': header,
                'value': headers_lower[header],
                'description': description
            })
        else:
            missing.append({
                'header': header,
                'description': description
            })
    
    # Calcula nota baseada nos headers críticos principais (os 4 primeiros)
    critical_count = sum(1 for h in found if h['header'] in list(critical_headers.keys())[:4])
    score = (critical_count / 4) * 100
    
    if score == 100:
        grade = 'A'
    elif score >= 75:
        grade = 'B'
    elif score >= 50:
        grade = 'C'
    else:
        grade = 'F'
    
    return {
        'grade': grade,
        'score': int(score),
        'headers_found': found,
        'headers_missing': missing,
        'recommendations': [f"Adicione header: {h['header']}" for h in missing]
    }


def detect_tech_stack(url: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    Detecta tecnologias e VERSÕES usando Wappalyzer.
    
    Args:
        url: URL completa do site (ex: https://example.com)
        timeout: Timeout em segundos
    
    Returns:
        {
            'technologies': [
                {'name': 'Nginx', 'version': '1.18.0', 'categories': ['Web Servers']},
                {'name': 'React', 'version': None, 'categories': ['JavaScript Frameworks']}
            ],
            'detected_at': datetime
        }
    """
    try:
        from Wappalyzer import Wappalyzer, WebPage
        
        wappalyzer = Wappalyzer.latest()
        webpage = WebPage.new_from_url(url, timeout=timeout)
        technologies = wappalyzer.analyze_with_versions(webpage)
        
        results = []
        for tech_name, tech_info in technologies.items():
            # Wappalyzer retorna dict com 'versions' (lista) e 'categories' (lista)
            versions = tech_info.get('versions', [])
            version = versions[0] if versions else None
            
            results.append({
                'name': tech_name,
                'version': version,
                'categories': tech_info.get('categories', []),
                'version_detected': bool(version)
            })
        
        return {
            'technologies': results,
            'detected_at': datetime.now().isoformat(),
            'success': True
        }
        
    except Exception as e:
        print(f"❌ Erro ao detectar tech stack: {e}")
        return {
            'technologies': [],
            'detected_at': datetime.now().isoformat(),
            'success': False,
            'error': str(e)
        }


def map_category_to_ecosystem(categories: List[str]) -> str:
    """
    Mapeia categorias de tecnologia para ecosystems do OSV.dev.
    
    Args:
        categories: Lista de categorias do Wappalyzer
    
    Returns:
        Ecosystem string: 'npm', 'PyPI', 'Go', etc.
    """
    category_mapping = {
        'JavaScript frameworks': 'npm',
        'JavaScript libraries': 'npm',
        'UI frameworks': 'npm',
        'Node.js': 'npm',
        'Programming languages': 'PyPI',  # Assumindo Python se não especificado
        'Web frameworks': 'PyPI',
        'Databases': 'Maven',  # Muitos DBs usam Java
    }
    
    for category in categories:
        if category in category_mapping:
            return category_mapping[category]
    
    # Default para npm (JavaScript é o mais comum na web)
    return 'npm'


def query_osv_vulnerabilities(package_name: str, version: str, ecosystem: str = 'npm') -> List[Dict]:
    """
    Consulta OSV.dev API para CVEs de um pacote específico.
    
    Args:
        package_name: Nome do pacote (ex: 'react', 'nginx')
        version: Versão exata (ex: '16.8.0')
        ecosystem: npm, PyPI, Go, Maven, etc.
    
    Returns:
        Lista de vulnerabilidades encontradas
    """
    if not version or version == 'None':
        return []  # Sem versão, não conseguimos verificar
    
    api_url = "https://api.osv.dev/v1/query"
    payload = {
        "version": version,
        "package": {
            "name": package_name.lower(),
            "ecosystem": ecosystem
        }
    }
    
    try:
        response = requests.post(api_url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            vulns = data.get('vulns', [])
            
            # Formata resultados
            results = []
            for v in vulns:
                # Extrai severity
                severity_list = v.get('severity', [])
                severity = 'UNKNOWN'
                if severity_list:
                    severity = severity_list[0].get('score', 'UNKNOWN')
                
                results.append({
                    'cve_id': v.get('id', 'N/A'),
                    'summary': v.get('summary', 'No summary available')[:200],  # Limita tamanho
                    'severity': severity,
                    'published': v.get('published', 'N/A'),
                    'modified': v.get('modified', 'N/A')
                })
            
            return results
            
        else:
            print(f"⚠️  OSV.dev retornou status {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Erro ao consultar OSV.dev: {e}")
        return []


def check_general_security(url: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    Função orquestradora: Detecta tech stack, consulta CVEs e audita headers.
    
    Args:
        url: URL completa do site
        timeout: Timeout em segundos
    
    Returns:
        {
            'tech_stack': {...},
            'vulnerabilities': [...],
            'security_headers': {...},
            'timestamp': datetime,
            'errors': [...]
        }
    """
    results = {
        'tech_stack': None,
        'vulnerabilities': [],
        'security_headers': None,
        'timestamp': datetime.now().isoformat(),
        'errors': []
    }
    
    try:
        # 1. Faz request para pegar headers
        print(f"🔍 Fazendo request para {url}...")
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        
        # 2. Audita headers de segurança (sempre funciona)
        print(f"🔐 Auditando headers de segurança...")
        results['security_headers'] = audit_security_headers(dict(response.headers))
        
        # 3. Detecta tecnologias
        print(f"🛠️  Detectando tecnologias...")
        tech_result = detect_tech_stack(url, timeout)
        results['tech_stack'] = tech_result
        
        # 4. Para cada tecnologia com versão, busca CVEs (com rate limiting)
        if tech_result.get('success') and tech_result.get('technologies'):
            print(f"🔎 Buscando vulnerabilidades...")
            for tech in tech_result['technologies']:
                if tech.get('version'):
                    ecosystem = map_category_to_ecosystem(tech.get('categories', []))
                    print(f"   • {tech['name']} v{tech['version']} ({ecosystem})...")
                    
                    vulns = query_osv_vulnerabilities(
                        package_name=tech['name'].lower(),
                        version=tech['version'],
                        ecosystem=ecosystem
                    )
                    
                    if vulns:
                        print(f"     ⚠️  {len(vulns)} vulnerabilidade(s) encontrada(s)")
                        for vuln in vulns:
                            vuln['technology'] = tech['name']
                            vuln['version'] = tech['version']
                            results['vulnerabilities'].append(vuln)
                    
                    # Rate limiting: espera 1 segundo entre requests ao OSV.dev
                    time.sleep(1)
        
        print(f"✅ Scan concluído!")
        
    except Exception as e:
        error_msg = f"Erro em check_general_security: {str(e)}"
        results['errors'].append(error_msg)
        print(f"❌ {error_msg}")
    
    return results


if __name__ == "__main__":
    # Teste manual do scanner
    import sys
    
    if len(sys.argv) > 1:
        test_domain = sys.argv[1]
    else:
        test_domain = "google.com"
    
    print(f"🔍 Escaneando {test_domain}...")
    result = full_scan(test_domain)
    
    print(f"\n📊 Resultados:")
    print(f"   Online: {'✅' if result.is_online else '❌'}")
    print(f"   Status HTTP: {result.http_status_code}")
    print(f"   Latência: {result.latency_ms}ms")
    print(f"   SSL Válido: {'✅' if result.ssl_valid else '❌'}")
    print(f"   Dias para SSL expirar: {result.ssl_days_remaining}")
    print(f"   Emissor SSL: {result.ssl_issuer}")
    print(f"   Portas Abertas: {result.open_ports if result.open_ports else 'Nenhuma'}")
