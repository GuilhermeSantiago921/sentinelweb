# Visual Regression Testing - Setup Guide

## 📸 Visão Geral

O SentinelWeb agora inclui **Visual Regression Testing** - monitoramento automático de mudanças visuais nos seus sites.

### Como funciona:

1. **Baseline**: Na primeira execução, o sistema captura um screenshot que serve como referência
2. **Comparação**: Em verificações subsequentes, compara o screenshot atual com o baseline
3. **Alerta**: Se a diferença visual for maior que 5%, um alerta é gerado

---

## 🚀 Instalação

### 1. Instalar Dependências Python

As dependências já foram adicionadas ao `requirements.txt`:

```bash
playwright==1.40.0
Pillow==10.2.0
numpy==1.26.3
```

### 2. Instalar Navegadores do Playwright

**Se estiver usando Docker** (recomendado):
- O Dockerfile já foi atualizado para instalar o Chromium automaticamente
- Apenas reconstrua as imagens:

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

**Se estiver rodando localmente** (sem Docker):

```bash
# Instale as dependências
pip install -r requirements.txt

# Instale os navegadores do Playwright
playwright install chromium
playwright install-deps chromium
```

---

## 🔧 Configuração

### Atualizar Banco de Dados

As novas colunas foram adicionadas ao modelo `Site`:
- `last_screenshot_path`
- `baseline_screenshot_path`
- `visual_diff_percent`
- `last_visual_check`
- `visual_alert_triggered`

**Para atualizar o banco de dados:**

```bash
# Entre no container web
docker-compose exec web bash

# Abra o Python
python

# Execute:
from database import engine, Base
from models import Site
Base.metadata.create_all(bind=engine)
exit()
```

Ou simplesmente **delete e recrie o banco de dados** (apenas para desenvolvimento):

```bash
docker-compose down -v
docker-compose up -d
```

---

## 📋 Como Usar

### 1. Via Dashboard (Interface Web)

1. Acesse os detalhes de um site
2. Veja o card "Visual Snapshot"
3. Clique em **"Capturar Primeiro Snapshot"** (primeira vez)
4. Aguarde a verificação ser processada
5. Futuras verificações compararão automaticamente

**Botões disponíveis:**
- **Verificar Agora**: Força uma verificação visual imediata
- **Definir como Padrão**: Atualiza o baseline (quando você muda o site intencionalmente)

### 2. Via API

**Disparar verificação visual:**
```bash
POST /api/sites/{site_id}/visual-check
```

**Atualizar baseline:**
```bash
POST /api/sites/{site_id}/update-baseline
```

**Ver status visual:**
```bash
GET /api/sites/{site_id}/visual-status
```

### 3. Verificação Automática (Celery Beat)

Configure no `celerybeat-schedule` para rodar automaticamente:

```python
# tasks.py já tem a função visual_check_all_sites()
# Configure para rodar 1x por dia
```

---

## 🎯 Casos de Uso

### Detectar Defacement (Desfiguração)
Se hackers modificarem o visual do site, você receberá um alerta imediato.

### Monitorar Mudanças Não Autorizadas
Detecta alterações não planejadas no layout, cores, textos, imagens.

### Validação de Deploy
Após fazer deploy de uma nova versão, compare se ficou como esperado.

### Qualidade Visual
Garante que o site está sendo renderizado corretamente.

---

## ⚙️ Configurações Avançadas

### Ajustar Threshold de Alerta

O padrão é **5%**. Para ajustar, edite em `tasks.py`:

```python
# Linha ~166
should_alert = diff_percent > 5.0  # Mude para 3.0, 10.0, etc
```

### Performance

**Recursos necessários:**
- ~200MB RAM por screenshot
- ~30s por verificação
- Screenshots são full-page (página completa)

**Para sites com muitas páginas:**
- Configure verificações espaçadas (5 min entre cada)
- Use `visual_check_all_sites()` apenas 1x por dia

---

## 📊 Estrutura de Arquivos

```
static/
└── screenshots/
    ├── {site_id}_baseline.png    # Imagem de referência
    ├── {site_id}_current.png      # Última captura
    └── {site_id}_diff.png         # Diferença visual (gerada quando > 5%)
```

---

## 🐛 Troubleshooting

### "Erro ao capturar screenshot"
- Verifique se o Playwright está instalado: `playwright --version`
- Verifique se o site permite bots (alguns bloqueiam)
- Tente acessar o site manualmente no navegador

### "Permission denied" ao salvar screenshot
- Verifique permissões do diretório `static/screenshots/`
- No Docker: `docker-compose exec web chmod -R 777 static/screenshots`

### Screenshots muito grandes
- Use compressão PNG (já implementado)
- Considere limitar altura máxima em `take_screenshot()`

### Site bloqueia bots
Alguns sites detectam Playwright/Puppeteer. Soluções:
- Use user-agent real (já implementado)
- Adicione cookies de sessão
- Configure proxy rotativo

---

## 🔐 Segurança

- Screenshots são salvos localmente (não enviados para terceiros)
- Não captura conteúdo atrás de login (apenas páginas públicas)
- Screenshots podem conter informações sensíveis - proteja o diretório

---

## 📈 Métricas

O sistema rastreia:
- **visual_diff_percent**: Porcentagem de diferença (0.0 - 100.0)
- **visual_alert_triggered**: Boolean se gerou alerta
- **last_visual_check**: Timestamp da última verificação

---

## 🚨 Alertas Telegram

Quando uma mudança > 5% é detectada:

```
🎨 ALERTA DE MUDANÇA VISUAL

🌐 Site: exemplo.com
📊 Diferença: 12.5%
⚠️ Status: Mudança significativa detectada

💡 Ação: Verifique se foi intencional.
Se sim, atualize o baseline no dashboard.
```

---

## 🎓 Algoritmo de Comparação

1. **Carrega** as duas imagens (baseline e current)
2. **Redimensiona** para o mesmo tamanho (se necessário)
3. **Converte** para arrays NumPy RGB
4. **Calcula** diferença absoluta pixel por pixel
5. **Normaliza** para porcentagem (0-100%)

**Complexidade:** O(n × m × 3) onde n×m são as dimensões da imagem

---

## 📚 Referências

- [Playwright Documentation](https://playwright.dev/python/)
- [Pillow (PIL) Docs](https://pillow.readthedocs.io/)
- [NumPy Array Operations](https://numpy.org/doc/stable/reference/arrays.html)

---

## ✅ Checklist de Implementação

- [x] Dependências adicionadas ao `requirements.txt`
- [x] Models atualizados com colunas visuais
- [x] Funções de screenshot e comparação em `scanner.py`
- [x] Task Celery `visual_check_task` criada
- [x] Endpoints API implementados
- [x] Card visual adicionado ao dashboard
- [x] Dockerfile atualizado com Playwright
- [x] Diretório `static/screenshots/` criado
- [x] Documentação completa

---

**Desenvolvido com 🎨 para o SentinelWeb**
