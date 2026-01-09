# General Tech Scanner - Documentação

## 📋 Visão Geral

O **General Tech Scanner** é um módulo de segurança do SentinelWeb que detecta tecnologias, versões e vulnerabilidades em sites **não-WordPress**. 

Ele complementa o WordPress Scanner, fornecendo análise de segurança para sites feitos com React, Node.js, Nginx, Angular, Vue.js e outras tecnologias modernas.

---

## 🎯 Funcionalidades

### 1. **Detecção de Tech Stack**
- Identifica automaticamente as tecnologias usadas no site
- Detecta versões quando possível (crucial para análise de CVEs)
- Categoriza tecnologias (Web Server, JavaScript Framework, Database, etc.)
- Usa biblioteca **Wappalyzer** para análise precisa

**Exemplo de tecnologias detectadas:**
```json
[
  {"name": "Nginx", "version": "1.18.0", "categories": ["Web Servers"]},
  {"name": "React", "version": "17.0.2", "categories": ["JavaScript Frameworks"]},
  {"name": "jQuery", "version": "3.6.0", "categories": ["JavaScript Libraries"]}
]
```

### 2. **Análise de Vulnerabilidades (CVEs)**
- Para cada tecnologia com **versão detectada**, consulta a API **OSV.dev**
- OSV.dev (Open Source Vulnerabilities) é mantido pelo Google
- Retorna CVEs conhecidos com severidade, descrição e data de publicação
- **IMPORTANTE**: Sem a versão, não é possível verificar vulnerabilidades

**Exemplo de CVE encontrado:**
```json
{
  "cve_id": "CVE-2021-23337",
  "technology": "lodash",
  "version": "4.17.19",
  "severity": "HIGH",
  "summary": "Command injection in lodash template function",
  "published": "2021-02-15"
}
```

### 3. **Auditoria de Security Headers**
- Analisa headers HTTP de segurança
- Dá uma nota de **A** a **F** baseado em headers críticos
- Sempre funciona, independente de detecção de versões
- Headers verificados:
  - `Strict-Transport-Security` (HSTS) - Força HTTPS
  - `Content-Security-Policy` (CSP) - Previne XSS
  - `X-Frame-Options` - Previne Clickjacking
  - `X-Content-Type-Options` - Previne MIME Sniffing
  - `Referrer-Policy` - Controla informações de referência
  - `Permissions-Policy` - Controla permissões de recursos

**Sistema de Notas:**
- **A**: Todos os 4 headers críticos principais presentes (100%)
- **B**: 3 de 4 headers presentes (75%)
- **C**: 2 de 4 headers presentes (50%)
- **F**: Menos de 2 headers (< 50%)

---

## 🔧 Como Funciona

### Fluxo de Execução

1. **Trigger Automático**
   - Celery task `scan_site` detecta que o site **não é WordPress**
   - Chama função `check_general_security(url)`

2. **Coleta de Dados**
   - Faz request HTTP para obter headers
   - Audita security headers (sempre funciona)

3. **Detecção de Tecnologias**
   - Usa **Wappalyzer** para analisar HTML, headers e JavaScript
   - Extrai nomes e versões de tecnologias

4. **Consulta de CVEs**
   - Para cada tecnologia **com versão**, consulta OSV.dev API
   - Mapeia categoria → ecosystem (npm, PyPI, Maven, etc.)
   - Rate limiting: 1 segundo entre requests

5. **Armazenamento**
   - Salva `tech_stack` (JSON) no banco
   - Salva `general_vulnerabilities` (JSON) no banco
   - Salva `security_headers_grade` (A/B/C/F)
   - Atualiza `last_tech_scan` timestamp

6. **Alertas Telegram**
   - **CVEs Críticos/Altos**: Envia alerta imediato
   - **Security Headers F**: Alerta sobre falta de proteção

---

## 📊 Campos do Banco de Dados

### Tabela `sites`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `tech_stack` | TEXT (JSON) | Lista de tecnologias detectadas com versões |
| `security_headers_grade` | VARCHAR(1) | Nota dos headers: 'A', 'B', 'C' ou 'F' |
| `general_vulnerabilities` | TEXT (JSON) | Array de CVEs encontrados |
| `last_tech_scan` | DATETIME | Timestamp da última varredura |

---

## 🛠️ Funções do Scanner

### `audit_security_headers(headers: dict) -> Dict`
Audita headers de segurança HTTP.

**Entrada:**
```python
headers = {
    'strict-transport-security': 'max-age=31536000',
    'x-frame-options': 'SAMEORIGIN'
}
```

**Saída:**
```python
{
    'grade': 'C',
    'score': 50,
    'headers_found': [
        {'header': 'strict-transport-security', 'value': '...', 'description': 'HSTS - Força HTTPS'},
        {'header': 'x-frame-options', 'value': 'SAMEORIGIN', 'description': 'Previne Clickjacking'}
    ],
    'headers_missing': [
        {'header': 'content-security-policy', 'description': 'CSP - Previne XSS'},
        {'header': 'x-content-type-options', 'description': 'Previne MIME Sniffing'}
    ],
    'recommendations': [
        'Adicione header: content-security-policy',
        'Adicione header: x-content-type-options'
    ]
}
```

---

### `detect_tech_stack(url: str, timeout: int = 5) -> Dict`
Detecta tecnologias usando Wappalyzer.

**Entrada:**
```python
url = "https://example.com"
```

**Saída:**
```python
{
    'success': True,
    'technologies': [
        {
            'name': 'Nginx',
            'version': '1.18.0',
            'categories': ['Web Servers'],
            'version_detected': True
        },
        {
            'name': 'React',
            'version': None,
            'categories': ['JavaScript Frameworks'],
            'version_detected': False
        }
    ],
    'detected_at': '2024-01-15T10:30:00'
}
```

---

### `query_osv_vulnerabilities(package_name: str, version: str, ecosystem: str) -> List[Dict]`
Consulta OSV.dev API para CVEs.

**Entrada:**
```python
package_name = "react"
version = "16.8.0"
ecosystem = "npm"
```

**Saída:**
```python
[
    {
        'cve_id': 'CVE-2020-15168',
        'summary': 'Prototype pollution in react-dom',
        'severity': 'MODERATE',
        'published': '2020-09-01',
        'modified': '2020-09-15'
    }
]
```

**API Endpoint:**
```
POST https://api.osv.dev/v1/query
Content-Type: application/json

{
  "version": "16.8.0",
  "package": {
    "name": "react",
    "ecosystem": "npm"
  }
}
```

---

### `map_category_to_ecosystem(categories: List[str]) -> str`
Mapeia categorias do Wappalyzer para ecosystems do OSV.dev.

**Mapeamento:**
- `JavaScript frameworks` → `npm`
- `JavaScript libraries` → `npm`
- `UI frameworks` → `npm`
- `Node.js` → `npm`
- `Programming languages` → `PyPI` (assume Python)
- `Web frameworks` → `PyPI`
- `Databases` → `Maven` (muitos usam Java)
- **Default**: `npm` (mais comum na web)

---

### `check_general_security(url: str, timeout: int = 5) -> Dict`
Função orquestradora que executa todos os checks.

**Entrada:**
```python
url = "https://example.com"
```

**Saída:**
```python
{
    'tech_stack': { ... },  # Resultado de detect_tech_stack()
    'vulnerabilities': [    # CVEs de todas as tecnologias
        {
            'cve_id': 'CVE-2021-23337',
            'technology': 'lodash',
            'version': '4.17.19',
            'severity': 'HIGH',
            'summary': '...'
        }
    ],
    'security_headers': { ... },  # Resultado de audit_security_headers()
    'timestamp': '2024-01-15T10:30:00',
    'errors': []
}
```

---

## 🚨 Sistema de Alertas

### Telegram - CVEs Críticos/Altos
```
🚨 VULNERABILIDADES CRÍTICAS DETECTADAS

🌐 Site: Meu Site React
🔗 Domínio: example.com
⚠️ CVEs Encontrados: 3

🔴 CVE-2021-23337
   Tecnologia: lodash 4.17.19
   Severidade: HIGH
   Command injection in lodash template function

🔴 CVE-2020-15168
   Tecnologia: react-dom 16.8.0
   Severidade: CRITICAL
   Prototype pollution vulnerability

... e mais 1 vulnerabilidade(s).
```

### Telegram - Security Headers Grade F
```
⚠️ SECURITY HEADERS CRÍTICOS AUSENTES

🌐 Site: Meu Site React
🔗 Domínio: example.com
📊 Nota: F (Falhou)

Headers Faltando:
• strict-transport-security: HSTS - Força HTTPS
• content-security-policy: CSP - Previne XSS
• x-frame-options: Previne Clickjacking
• x-content-type-options: Previne MIME Sniffing

⚠️ Sem esses headers, seu site está vulnerável a
ataques como XSS, clickjacking e MIME sniffing.
```

---

## 🎨 Interface Frontend

### Card "Tech Stack & Segurança"

Aparece apenas para sites **não-WordPress** na página de detalhes.

**Componentes:**
1. **Security Headers Grade** (grande, destaque)
   - Nota A: Verde, "Excelente!"
   - Nota F: Vermelho, "CRÍTICO!"
   - Nota B/C: Amarelo, "Alguns headers faltando"

2. **Tecnologias Detectadas** (grid 2 colunas)
   - Nome da tecnologia
   - Versão (ou "Versão não detectada")
   - Máximo 8 tecnologias exibidas

3. **Vulnerabilidades** (lista)
   - CVE ID
   - Tecnologia + Versão
   - Severidade (bold)
   - Resumo (truncado)
   - Máximo 3 CVEs exibidos

4. **Footer**
   - Timestamp da última varredura

---

## 🔍 Limitações Conhecidas

### 1. **Versão Nem Sempre É Detectada**
- Wappalyzer pode não encontrar a versão de todas as tecnologias
- Sem versão, **não é possível verificar CVEs**
- Frontend mostra "Versão não detectada" nesses casos

**Solução:**
- Mensagem clara para o usuário
- Headers de segurança como indicador alternativo

### 2. **OSV.dev Não Tem Todas as Tecnologias**
- Base de dados focada em open source
- Tecnologias proprietárias podem não ter dados
- Rate limiting recomendado: 1 request/segundo

**Solução:**
- Delay de 1 segundo entre requests
- Tratamento de erros gracioso (não quebra o scan)

### 3. **Ecosystem Mapping Pode Ser Impreciso**
- Categoria "Programming Languages" → assumimos PyPI
- Pode haver falsos positivos

**Solução:**
- Mapeamento conservador (default: npm)
- Logs detalhados para debugging

---

## 📈 Exemplos de Uso

### Scan Manual de um Site
```python
from scanner import check_general_security

url = "https://react-example.com"
result = check_general_security(url, timeout=10)

print(f"Tecnologias: {len(result['tech_stack']['technologies'])}")
print(f"Vulnerabilidades: {len(result['vulnerabilities'])}")
print(f"Security Grade: {result['security_headers']['grade']}")
```

### Consultar CVE de uma Tecnologia
```python
from scanner import query_osv_vulnerabilities

vulns = query_osv_vulnerabilities(
    package_name="react",
    version="16.8.0",
    ecosystem="npm"
)

for v in vulns:
    print(f"{v['cve_id']}: {v['severity']} - {v['summary']}")
```

### Auditar Headers de um Site
```python
import httpx
from scanner import audit_security_headers

response = httpx.get("https://example.com")
audit = audit_security_headers(dict(response.headers))

print(f"Grade: {audit['grade']}")
print(f"Score: {audit['score']}/100")
print(f"Headers faltando: {len(audit['headers_missing'])}")
```

---

## 🚀 Tecnologias Suportadas

### Frameworks JavaScript
- React, Angular, Vue.js, Svelte
- jQuery, Lodash, Underscore
- Next.js, Nuxt.js, Gatsby

### Web Servers
- Nginx, Apache, IIS, LiteSpeed
- Caddy, Traefik

### Linguagens Backend
- Node.js, Python, Ruby, PHP, Go
- Java, .NET

### Databases
- MySQL, PostgreSQL, MongoDB
- Redis, Memcached

### CDNs & Cloud
- Cloudflare, Akamai, AWS
- Google Cloud, Azure

---

## 📚 Referências

- **OSV.dev API**: https://osv.dev/docs/
- **Wappalyzer**: https://www.wappalyzer.com/
- **Security Headers**: https://securityheaders.com/
- **OWASP Security Headers**: https://owasp.org/www-project-secure-headers/

---

## 🎯 Roadmap Futuro

- [ ] Suporte a análise de dependências JavaScript (package.json)
- [ ] Integração com National Vulnerability Database (NVD)
- [ ] Histórico de mudanças de tech stack
- [ ] Comparação de security grade ao longo do tempo
- [ ] Recomendações automáticas de atualização
- [ ] Scan de subdomínios com tech stack diferente

---

**Última atualização:** 2024-01-15  
**Versão:** 1.0.0
