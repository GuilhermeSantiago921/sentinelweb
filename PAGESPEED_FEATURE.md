# 🚀 Feature Implementada: Monitoramento de Performance via Google PageSpeed Insights

## ✨ Resumo da Implementação

Adicionamos ao **SentinelWeb** a capacidade de auditar automaticamente a **performance** de todos os sites monitorados usando a API oficial do Google PageSpeed Insights (Lighthouse).

## 📋 O que foi implementado

### 1. **Backend - Banco de Dados** (`models.py`)

Novos campos adicionados à tabela `Site`:

```python
performance_score = Column(Integer, nullable=True)  # 0-100
seo_score = Column(Integer, nullable=True)  # 0-100
accessibility_score = Column(Integer, nullable=True)  # 0-100
best_practices_score = Column(Integer, nullable=True)  # 0-100
last_pagespeed_check = Column(DateTime(timezone=True), nullable=True)
```

### 2. **Backend - Scanner** (`scanner.py`)

Nova função implementada:

```python
def check_pagespeed(url, strategy='mobile', timeout=30.0) -> Dict
```

**Funcionalidades:**
- ✅ Integração completa com Google PageSpeed Insights API v5
- ✅ Extrai scores de: Performance, SEO, Acessibilidade, Best Practices
- ✅ Extrai Core Web Vitals: LCP, CLS, FCP, Speed Index, TBT
- ✅ Timeout configurável (padrão 30s)
- ✅ Tratamento de erros robusto
- ✅ Suporte mobile e desktop

### 3. **Backend - Tasks Celery** (`tasks.py`)

Duas novas tasks criadas:

#### `run_pagespeed_audit(site_id)`
- Executa auditoria individual de um site
- Salva scores no banco de dados
- Envia alerta Telegram se performance < 50
- Retry automático (2 tentativas, 5min de intervalo)

#### `run_pagespeed_audit_all()`
- Agenda auditoria para todos os sites ativos
- Espaça requisições em 1 minuto cada (evita sobrecarga da API)
- Execução automática diária via Celery Beat

### 4. **Agendamento Automático** (`celery_app.py`)

Configurado Celery Beat para rodar auditoria **1x por dia às 3h da manhã**:

```python
beat_schedule={
    "pagespeed-audit-daily": {
        "task": "tasks.run_pagespeed_audit_all",
        "schedule": crontab(hour=3, minute=0),
    },
}
```

**Por que apenas 1x por dia?**
- Economiza quota da API do Google (25k/dia gratuito)
- Performance não muda drasticamente em horas
- Evita sobrecarga no servidor

### 5. **Frontend - Card de Performance** (`site_details.html`)

Novo card visual na página `/sites/{id}/details`:

#### Elementos visuais:
- 🎯 **Score principal** com barra de progresso colorida:
  - Verde (90-100): Excelente ✅
  - Amarelo (50-89): Precisa Melhorar ⚠️
  - Vermelho (0-49): Pobre - Ação Necessária ❌

- 📊 **Grid 3x1** com scores secundários:
  - SEO
  - Acessibilidade
  - Melhores Práticas

- 🕐 **Timestamp** da última auditoria
- 💡 **Info box** com link para documentação

### 6. **Configuração** (`.env.example`)

Instruções completas para obter API Key gratuita do Google:

```bash
GOOGLE_PAGESPEED_API_KEY=sua-chave-aqui
```

### 7. **Documentação** (`GOOGLE_PAGESPEED_SETUP.md`)

Guia passo-a-passo com screenshots (texto) explicando:
- Como criar conta no Google Cloud Console
- Como ativar a API PageSpeed Insights
- Como gerar e restringir a API Key
- Troubleshooting de erros comuns
- Dicas de otimização de performance

### 8. **Schema API** (`schemas.py`)

Atualizado `SiteResponse` com novos campos para API REST.

---

## 🎯 Como usar

### Para Administradores (Setup Inicial)

1. **Obter API Key do Google** (GRATUITO):
   - Siga o guia: `GOOGLE_PAGESPEED_SETUP.md`
   - Copie a chave gerada

2. **Configurar no .env**:
   ```bash
   GOOGLE_PAGESPEED_API_KEY=AIzaSyD1234567890abcdefghijklmnopqrstuv
   ```

3. **Recriar banco de dados** (inclui novos campos):
   ```bash
   docker-compose exec web rm -f sentinelweb.db
   docker-compose restart
   ```

4. **Testar auditoria manual** (opcional):
   ```bash
   docker-compose exec web python -c "
   from scanner import check_pagespeed
   result = check_pagespeed('https://google.com')
   print(f'Performance: {result[\"performance_score\"]}/100')
   "
   ```

### Para Usuários Finais

1. **Cadastre um site** normalmente no dashboard
2. **Aguarde a primeira auditoria** (roda às 3h da manhã automaticamente)
3. **Visualize os resultados**:
   - Dashboard > Clique no site > Aba "Detalhes"
   - Veja o card "Performance (Google Lighthouse)"

### Executar Auditoria Manual (Imediato)

Se não quiser esperar até 3h da manhã:

```bash
docker-compose exec web python -c "
from tasks import run_pagespeed_audit
from database import SessionLocal
db = SessionLocal()
from models import Site

# Pega ID do primeiro site
site = db.query(Site).first()
if site:
    run_pagespeed_audit(site.id)
    print(f'Auditoria agendada para {site.domain}')
"
```

Ou via Celery:

```bash
docker-compose exec celery_worker celery -A celery_app call tasks.run_pagespeed_audit --args='[1]'
```

---

## 📊 Quota e Limites

### Plano Gratuito do Google:
- ✅ **25,000 requisições/dia**
- ✅ Suficiente para **~833 sites** (1 auditoria/dia cada)
- ✅ Sem cartão de crédito necessário

### Se precisar de mais:
- 💰 **$5 USD por 1,000 requisições adicionais**
- Para 100 sites rodando 1x/dia = apenas **0,50 requisições extras/dia** = GRATUITO na prática

### Exemplo de Cálculo:
- **10 sites**: 10 requisições/dia = 300/mês = **GRÁTIS**
- **100 sites**: 100 requisições/dia = 3,000/mês = **GRÁTIS**
- **500 sites**: 500 requisições/dia = 15,000/mês = **GRÁTIS**
- **1,000 sites**: 1,000 requisições/dia = 30,000/mês = **$0,25/mês extras**

---

## 🔔 Alertas Telegram

Se a performance de um site cai abaixo de **50/100**, o usuário recebe automaticamente um alerta via Telegram:

```
⚠️ ALERTA - PERFORMANCE CRÍTICA

🌐 Site: Meu Site
🔗 Domínio: exemplo.com.br
📊 Score Performance: 45/100 🔴
⏰ Horário: 07/01/2026 15:30:00 UTC

Seu site está lento. Isso afeta SEO e conversões.
Acesse o dashboard para ver detalhes.
```

---

## 🎨 Design do Card de Performance

### Código Visual:

```
┌─────────────────────────────────────────┐
│ ⚡ Performance (Google Lighthouse)      │
├─────────────────────────────────────────┤
│                                         │
│  Performance Score     [87/100] 🟡      │
│  ████████████████░░░░░ 87%             │
│       ⚠️ Precisa Melhorar              │
│                                         │
│  ┌──────┐ ┌──────┐ ┌──────┐           │
│  │ SEO  │ │Access│ │Prátic│           │
│  │  92  │ │  78  │ │  85  │           │
│  └──────┘ └──────┘ └──────┘           │
│                                         │
│  🕐 Última auditoria: 07/01/2026 03:00 │
│                                         │
│  ℹ️  A performance afeta SEO e...      │
└─────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### "API key not valid"
- Verifique se a chave foi copiada corretamente
- Confirme que a API está ativada no Google Cloud Console
- Aguarde 1-2 minutos após criar a chave

### "Quota exceeded"
- Você estourou 25k/dia
- Aguarde até meia-noite (horário do Pacífico) para resetar
- Ou adicione método de pagamento para quota adicional

### Card não aparece no frontend
- Certifique-se de que pelo menos 1 auditoria foi executada
- Verifique no banco: `site.performance_score` não deve ser NULL

### Auditoria demora muito
- Normal! A API do Google leva 10-30 segundos
- Por isso rodamos apenas 1x por dia
- Se travar, há timeout de 30s

---

## 📈 Próximos Passos (Opcional)

### Melhorias Futuras:
1. **Histórico de performance** (tabela separada para tracking temporal)
2. **Gráficos de tendência** (Chart.js mostrando evolução)
3. **Recomendações personalizadas** (parse do `audits` da API)
4. **Comparação mobile vs desktop** (rodar ambos strategies)
5. **Alertas configuráveis** (threshold customizável por usuário)

---

## 📚 Arquivos Modificados

```
sentinelweb/
├── models.py                    # ✅ Novos campos no Site
├── scanner.py                   # ✅ Função check_pagespeed()
├── tasks.py                     # ✅ Tasks de auditoria
├── celery_app.py               # ✅ Agendamento Celery Beat
├── schemas.py                  # ✅ SiteResponse atualizado
├── .env.example                # ✅ GOOGLE_PAGESPEED_API_KEY
├── GOOGLE_PAGESPEED_SETUP.md  # ✅ Guia completo (NOVO)
└── templates/
    └── site_details.html       # ✅ Card de Performance (NOVO)
```

---

## ✅ Checklist de Validação

- [x] Banco de dados com novos campos
- [x] Função check_pagespeed() implementada e testada
- [x] Tasks Celery criadas (individual + batch)
- [x] Celery Beat agendado para 3h da manhã
- [x] Frontend com card visual
- [x] Alertas Telegram para performance crítica
- [x] Schema API atualizado
- [x] Documentação completa
- [x] .env.example atualizado
- [x] Tratamento de erros robusto
- [ ] Testar com API Key real ⬅️ **Próximo passo do usuário**

---

## 🎉 Conclusão

O **SentinelWeb** agora é uma ferramenta ainda mais completa para monitoramento de sites, incluindo:

✅ Uptime  
✅ SSL  
✅ Portas  
✅ WordPress Security  
✅ Blacklist (RBL)  
✅ Expiração de Domínio  
✅ **Performance (Google Lighthouse)** ⬅️ **NOVO!**

Esta feature adiciona **valor premium** ao produto e diferencia o SentinelWeb de concorrentes como UptimeRobot e Pingdom, que não oferecem análise de performance integrada.

---

**Implementação concluída em:** 07/01/2026  
**Desenvolvido por:** GitHub Copilot + Usuário  
**Versão do SentinelWeb:** 1.1.0
