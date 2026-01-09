# 💳 Área de Gerenciamento de Assinatura - SentinelWeb

## 📋 Visão Geral

A **Área de Gerenciamento de Assinatura** permite que o usuário final visualize e gerencie sua assinatura do SentinelWeb de forma completa e intuitiva.

## ✨ Funcionalidades Implementadas

### 1. **Resumo do Plano Atual**
- ✅ Nome do plano (Gratuito, Profissional, Agência)
- ✅ Status da assinatura (Ativo, Pendente, Vencido)
- ✅ Valor mensal da assinatura
- ✅ Próxima data de vencimento (se aplicável)
- ✅ Botão para contato com suporte via WhatsApp

### 2. **Histórico Completo de Faturas**
- ✅ Listagem de todas as cobranças (pagas e pendentes)
- ✅ Informações detalhadas:
  - Data de vencimento (formato brasileiro: DD/MM/AAAA)
  - Descrição da cobrança
  - Valor formatado (R$ 00,00)
  - Forma de pagamento (Boleto, PIX, Cartão, etc.)
  - Status atual da fatura
- ✅ Ações inteligentes por status:
  - **Pendente/Vencido**: Botão "Pagar Agora" em destaque
  - **Pago**: Badge "Pago" + Link discreto para recibo

### 3. **Destaque Visual**
- ✅ Faturas vencidas: Fundo vermelho claro (`bg-red-50`)
- ✅ Faturas pendentes: Fundo amarelo claro (`bg-yellow-50`)
- ✅ Faturas pagas: Fundo branco com hover cinza
- ✅ Ícones coloridos para status e formas de pagamento

---

## 🎨 Design e UX

### **Cores e Estados:**

| Status | Cor de Fundo | Badge | Ação |
|--------|-------------|-------|------|
| `PENDING` | `bg-yellow-50` | Amarelo | Botão "Pagar Agora" verde |
| `OVERDUE` | `bg-red-50` | Vermelho | Botão "Pagar Agora" verde |
| `RECEIVED` | Branco | Verde | Link "Recibo" discreto |
| `CONFIRMED` | Branco | Verde | Link "Recibo" discreto |

### **Responsividade:**
- ✅ Grid adaptável (1 coluna mobile, 3 colunas desktop)
- ✅ Tabela com scroll horizontal em telas pequenas
- ✅ Botões e textos ajustam tamanho automaticamente

---

## 🔧 Estrutura Técnica

### **1. Service Layer (`services/asaas.py`)**

Novos métodos adicionados:

```python
def get_subscription_payments(customer_id: str) -> list
```
- Busca todas as cobranças de um cliente
- Retorna lista simplificada com dados formatados
- Ordena por data de vencimento (mais recente primeiro)

```python
def get_subscription_details(subscription_id: str) -> Optional[Dict]
```
- Busca detalhes de uma assinatura específica
- Retorna informações como status, valor, próximo vencimento
- Retorna `None` se não encontrar

```python
def get_customer_subscriptions(customer_id: str) -> list
```
- Busca todas as assinaturas ativas de um cliente
- Útil para usuários com múltiplas assinaturas

### **2. Backend Route (`main.py`)**

Nova rota:

```python
@app.get("/subscription", response_class=HTMLResponse)
async def subscription_page(...)
```

**Lógica:**
1. Verifica se usuário tem `asaas_customer_id`
2. Se sim, busca histórico de pagamentos via `AsaasService`
3. Formata datas para padrão brasileiro (DD/MM/AAAA)
4. Formata valores para moeda brasileira (R$ 00,00)
5. Traduz status e billing types para português
6. Renderiza template com todos os dados

**Mapeamentos de Status:**

```python
status_map = {
    'PENDING': 'Pendente',
    'RECEIVED': 'Pago',
    'CONFIRMED': 'Confirmado',
    'OVERDUE': 'Vencido',
    'REFUNDED': 'Reembolsado',
    # ... outros status
}
```

**Mapeamentos de Formas de Pagamento:**

```python
billing_type_map = {
    'BOLETO': 'Boleto',
    'CREDIT_CARD': 'Cartão de Crédito',
    'PIX': 'PIX',
    'DEBIT_CARD': 'Cartão de Débito',
    'TRANSFER': 'Transferência',
    'DEPOSIT': 'Depósito'
}
```

### **3. Frontend Template (`templates/subscription.html`)**

**Estrutura:**

```html
<!-- Seção 1: Resumo do Plano -->
<div class="grid grid-cols-1 md:grid-cols-3">
    - Card: Nome do Plano
    - Card: Status
    - Card: Valor Mensal
</div>

<!-- Seção 2: Histórico de Faturas -->
<table>
    - Vencimento
    - Descrição
    - Valor
    - Forma de Pagamento
    - Status
    - Ações (Pagar/Ver Recibo)
</table>

<!-- Seção 3: Dicas -->
<div class="bg-blue-50">
    - Informações úteis sobre assinatura
</div>
```

**Estados Condicionais:**

1. **Sem integração Asaas** (`!has_asaas_integration`):
   - Mostra mensagem "Nenhuma fatura encontrada"
   - Sugere fazer upgrade se estiver no plano free

2. **Com integração mas sem faturas** (`payment_history.length == 0`):
   - Mostra "Processando suas faturas"

3. **Com faturas** (`payment_history.length > 0`):
   - Renderiza tabela completa

---

## 🚀 Como Usar

### **Acesso do Usuário:**

1. Faça login no SentinelWeb
2. Clique em **"Minha Assinatura"** no menu superior
3. Veja seu plano atual e histórico de faturas

### **Pagar uma Fatura Pendente:**

1. Na tabela de faturas, localize a fatura com status "Pendente" ou "Vencido"
2. Clique no botão verde **"Pagar Agora"**
3. Será redirecionado para o gateway de pagamento do Asaas
4. Complete o pagamento
5. Retorne ao SentinelWeb - o status será atualizado automaticamente via webhook

### **Ver Recibo de Pagamento:**

1. Localize uma fatura com status "Pago"
2. Clique no link discreto **"Recibo"**
3. Será aberto em nova aba com o comprovante

---

## 📊 Dados Exibidos

### **Informações do Plano:**
- Nome: Gratuito, Profissional, Agência
- Status: Ativo, Pendente, Vencido
- Valor mensal: R$ 0,00 / R$ 49,90 / R$ 149,90

### **Informações das Faturas:**
- **ID**: Identificador único da cobrança
- **Data de Vencimento**: Formato DD/MM/AAAA
- **Descrição**: Ex: "Plano Pro - Mensalidade"
- **Valor**: Formato R$ 00,00
- **Forma de Pagamento**: Boleto, PIX, Cartão, etc.
- **Status**: Pendente, Pago, Vencido, Confirmado, etc.
- **Link de Pagamento**: URL para o gateway Asaas
- **Número da Parcela**: Se for parcelado (ex: 2/12)

---

## 🔄 Integração com Asaas

### **Fluxo de Dados:**

```
1. Usuário acessa /subscription
     ↓
2. Backend verifica user.asaas_customer_id
     ↓
3. Se existir, chama AsaasService.get_subscription_payments()
     ↓
4. Service faz GET /payments?customer={id} na API Asaas
     ↓
5. Recebe lista de cobranças
     ↓
6. Formata e retorna dados simplificados
     ↓
7. Template renderiza tabela com dados
```

### **Atualização Automática:**

Quando um pagamento é confirmado:

1. Asaas envia webhook para `/webhook/asaas`
2. Webhook processa e atualiza `user.plan_type`
3. Na próxima visita a `/subscription`, status estará atualizado
4. Não é necessário atualizar manualmente

---

## 🎯 Casos de Uso

### **Usuário no Plano Free:**
- ✅ Vê card mostrando "Plano Gratuito"
- ✅ Status: "Gratuito"
- ✅ Valor: R$ 0,00
- ✅ Mensagem: "Nenhuma fatura encontrada"
- ✅ Botão: "Fazer Upgrade"

### **Usuário no Plano Pro com Fatura Pendente:**
- ✅ Vê card mostrando "Plano Profissional"
- ✅ Status: "Pendente" (amarelo)
- ✅ Valor: R$ 49,90
- ✅ Tabela com 1 fatura pendente
- ✅ Botão verde: "Pagar Agora"

### **Usuário no Plano Pro com Pagamentos Regulares:**
- ✅ Vê card mostrando "Plano Profissional"
- ✅ Status: "Ativo" (verde)
- ✅ Próximo vencimento: 08/02/2026
- ✅ Tabela com histórico completo (últimas 10 faturas)
- ✅ Faturas pagas com badge verde + link recibo

### **Usuário com Fatura Vencida:**
- ✅ Linha da tabela em vermelho claro
- ✅ Badge vermelho: "Vencido"
- ✅ Botão verde destacado: "Pagar Agora"
- ✅ Alerta visual para chamar atenção

---

## 🛠️ Personalização

### **Alterar Número do WhatsApp:**

Edite `templates/subscription.html`, linha 128:

```html
<a href="https://wa.me/5511999999999?text=..." 
```

Substitua `5511999999999` pelo número real do suporte.

### **Adicionar Mais Formas de Pagamento:**

Edite `main.py`, função `subscription_page`, adicione no `billing_type_map`:

```python
billing_type_map = {
    # ... existentes
    'NEW_TYPE': 'Novo Tipo',
}
```

### **Personalizar Cores:**

Edite `templates/subscription.html`:

```html
<!-- Fatura vencida -->
bg-red-50 hover:bg-red-100

<!-- Fatura pendente -->
bg-yellow-50 hover:bg-yellow-100

<!-- Botão pagar -->
bg-green-600 hover:bg-green-700
```

---

## ✅ Checklist de Testes

- [ ] ✅ Página carrega sem erros
- [ ] ✅ Mostra plano correto do usuário
- [ ] ✅ Status da assinatura está correto
- [ ] ✅ Valor mensal está formatado (R$ 00,00)
- [ ] ✅ Datas estão em formato brasileiro (DD/MM/AAAA)
- [ ] ✅ Faturas pendentes aparecem com fundo amarelo
- [ ] ✅ Faturas vencidas aparecem com fundo vermelho
- [ ] ✅ Botão "Pagar Agora" redireciona para Asaas
- [ ] ✅ Link "Recibo" abre em nova aba
- [ ] ✅ Menu superior tem link "Minha Assinatura"
- [ ] ✅ Usuário free vê mensagem apropriada
- [ ] ✅ Tabela é responsiva em mobile
- [ ] ✅ Ícones aparecem corretamente (Font Awesome)
- [ ] ✅ Dicas na parte inferior são exibidas

---

## 🐛 Troubleshooting

### **Erro: "Configuração do sistema não encontrada"**

**Causa**: Tabela `SystemConfig` vazia ou API token não configurado.

**Solução**:
```bash
# Acesse o admin
http://localhost:8000/admin/config

# Configure o token do Asaas
# Salve as alterações
```

### **Erro: "Nenhuma fatura encontrada" mas deveria ter**

**Possíveis causas**:
1. `user.asaas_customer_id` está vazio
2. API Asaas não tem cobranças para esse customer
3. Erro na comunicação com API

**Debug**:
```bash
# Ver logs do container
docker-compose logs web --tail 50 | grep -i asaas

# Verificar customer_id no banco
docker-compose exec web python
>>> from database import get_db
>>> from models import User
>>> db = next(get_db())
>>> user = db.query(User).filter_by(email="seu@email.com").first()
>>> print(user.asaas_customer_id)
```

### **Erro: Botão "Pagar Agora" não aparece**

**Causa**: `invoice_url` está vazio na API Asaas.

**Solução**: Verifique se a cobrança foi criada corretamente via API Asaas.

---

## 📈 Melhorias Futuras (Opcional)

1. **Filtros e Pesquisa**
   - Filtrar por período (últimos 30/60/90 dias)
   - Pesquisar por valor ou descrição
   - Exportar histórico em CSV/PDF

2. **Estatísticas**
   - Total gasto no último ano
   - Média mensal de gastos
   - Gráfico de evolução de pagamentos

3. **Notificações In-App**
   - Badge com número de faturas pendentes
   - Pop-up ao fazer login se tiver fatura vencida

4. **Gerenciamento Avançado**
   - Cancelar assinatura direto pela interface
   - Alterar plano sem contatar suporte
   - Configurar meio de pagamento preferido

5. **Parcelamento**
   - Exibir detalhes de parcelamentos
   - Progresso visual (ex: 3/12 parcelas pagas)

---

## 📝 Arquivos Modificados

### **Criados:**
- ✅ `templates/subscription.html` - Template principal
- ✅ `SUBSCRIPTION_MANAGEMENT.md` - Esta documentação

### **Modificados:**
- ✅ `services/asaas.py` - Adicionados 3 novos métodos
- ✅ `main.py` - Adicionada rota `/subscription`
- ✅ `templates/base.html` - Adicionado link no menu

---

## 🎉 Conclusão

A **Área de Gerenciamento de Assinatura** está completa e funcional!

**Recursos implementados:**
- ✅ Resumo visual do plano atual
- ✅ Histórico completo de faturas
- ✅ Ações inteligentes por status
- ✅ Design responsivo e moderno
- ✅ Integração completa com Asaas
- ✅ Formatação de datas e moedas
- ✅ Tratamento de erros robusto

**Acesso:**
http://localhost:8000/subscription

**Para testar:**
1. Faça login como um usuário com `asaas_customer_id`
2. Acesse "Minha Assinatura" no menu
3. Veja seu plano e faturas
4. Teste o botão "Pagar Agora" (sandbox do Asaas)

---

**Status**: ✅ Implementado e Pronto para Uso
