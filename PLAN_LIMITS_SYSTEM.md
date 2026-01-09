# 🔒 Sistema de Limites por Plano - Implementado

## ✅ O Que Foi Feito

Implementamos um sistema completo de validação e restrições por plano, garantindo que os usuários respeitem os limites de cada tier.

---

## 📋 Limites por Plano

### 🆓 Plano Free
- **Sites:** 1 site
- **Intervalo mínimo:** 10 minutos
- **Features:** Monitoramento básico, SSL check
- **Preço:** Grátis

### ⭐ Plano Pro
- **Sites:** 20 sites
- **Intervalo mínimo:** 1 minuto
- **Features:** Monitoramento básico, SSL, Telegram, Heartbeat, Tech Scanner
- **Preço:** R$ 49/mês

### 🚀 Plano Agency
- **Sites:** 100 sites
- **Intervalo mínimo:** 30 segundos
- **Features:** Todas as features + Visual Regression + PageSpeed
- **Preço:** R$ 149/mês

---

## 🛡️ Validações Implementadas

### 1. **Limite de Sites**
- Ao tentar adicionar um site, o sistema verifica se o usuário atingiu o limite do plano
- Se atingiu, exibe mensagem de erro com sugestão de upgrade

### 2. **Intervalo de Verificação**
- Valida o intervalo mínimo permitido para cada plano
- Usuários Free não podem verificar sites com intervalo menor que 10 minutos
- Pro: mínimo 1 minuto
- Agency: mínimo 30 segundos

### 3. **Dashboard com Indicador de Uso**
- Card visual mostrando uso atual vs limite
- Barra de progresso com cores:
  - 🟢 Verde: 0-49% (OK)
  - 🟡 Amarelo: 50-79% (Atenção)
  - 🔴 Vermelho: 80-100% (Crítico)
- Alertas quando próximo do limite
- Botão de upgrade para planos inferiores

---

## 📁 Arquivos Criados/Modificados

### Novo Arquivo: `plan_limits.py`
```python
# Contém:
- PLAN_LIMITS: Dicionário com todos os limites
- can_add_site(): Valida se pode adicionar site
- validate_check_interval(): Valida intervalo
- has_feature(): Verifica acesso a features
- get_usage_stats(): Estatísticas de uso do plano
```

### Modificado: `main.py`
- **Rota `/sites/add` (POST):**
  - Validação de limite de sites antes de adicionar
  - Validação de intervalo mínimo
  - Mensagens de erro personalizadas com sugestão de upgrade

- **Rota `/dashboard` (GET):**
  - Adiciona estatísticas de uso do plano
  - Passa `plan_usage` para o template

### Modificado: `templates/dashboard.html`
- Card de uso do plano no topo do dashboard
- Barra de progresso visual
- Alertas contextuais
- Botão de upgrade (exceto para Agency)

---

## 🧪 Como Testar

### 1. **Teste de Limite Free (1 site)**
```bash
# Acesse como usuário Free
# Tente adicionar 2 sites
# Resultado: Primeiro site OK, segundo bloqueado com mensagem de upgrade
```

### 2. **Teste de Upgrade Manual (Admin)**
```python
# Via admin panel ou SQL:
UPDATE users SET plan_status = 'pro' WHERE email = 'usuario@email.com';

# Agora o usuário pode adicionar até 20 sites
```

### 3. **Visualizar Uso no Dashboard**
```bash
# Faça login
# No topo do dashboard, veja:
# "Plano Pro - Uso atual: 5 de 20 sites (25%)"
# Barra de progresso verde
```

---

## 🎯 Exemplos de Mensagens de Erro

### Limite de Sites Atingido (Free)
```
❌ Você atingiu o limite do Plano Free (1 site).

🚀 Faça upgrade para monitorar mais sites:
• Pro: Até 20 sites por R$ 49/mês
• Agency: Até 100 sites por R$ 149/mês

Entre em contato com o suporte para fazer upgrade.
```

### Intervalo Inválido
```
❌ O intervalo mínimo para o Plano Free é de 10 minuto(s).
Faça upgrade para intervalos menores.
```

---

## 🔄 Próximos Passos (Fase 3 - Integração Asaas)

1. **Webhook de Pagamento:**
   - Quando pagamento confirmado → Upgrade automático do plano
   - Quando cancelamento → Downgrade para Free

2. **Expiração de Planos:**
   - Verificar mensalmente se pagamento foi recebido
   - Downgrade automático se não pago

3. **Página de Upgrade:**
   - Interface para usuário solicitar upgrade
   - Gerar cobrança via API Asaas
   - Redirecionar para boleto/PIX

4. **Notificações:**
   - Email quando atingir 80% do limite
   - Email quando limite excedido
   - Telegram quando próximo do fim do período

---

## 📊 Métricas de Negócio

O sistema agora permite:
- ✅ **Monetização clara** por tier
- ✅ **Upsell automatizado** (mensagens de upgrade)
- ✅ **Visibilidade de uso** para o usuário
- ✅ **Controle de recursos** por plano
- ✅ **Incentivo ao upgrade** quando próximo do limite

---

## 🚀 Status Atual

✅ **IMPLEMENTADO:**
- Limites por plano
- Validações em tempo real
- Dashboard com uso visual
- Mensagens de erro contextuais
- Sugestões de upgrade

⏳ **PENDENTE (Fase 3):**
- Integração com API Asaas
- Webhooks de pagamento
- Upgrade/downgrade automático
- Página de checkout

---

## 📞 Contato para Upgrade

Atualmente, para fazer upgrade, o usuário deve:
1. Ver mensagem de limite atingido
2. Clicar em "Fazer Upgrade"
3. Entrar em contato com suporte
4. Admin atualiza manualmente: `/admin/users` → Editar Plano

**Futuro (com Asaas):**
- Clique em "Fazer Upgrade"
- Escolhe método (Boleto/PIX/Cartão)
- Gera cobrança automaticamente
- Upgrade instantâneo após confirmação
