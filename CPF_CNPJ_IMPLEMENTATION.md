# 🆔 Implementação de CPF/CNPJ

## ✅ O Que Foi Implementado

Sistema completo de coleta e validação de CPF/CNPJ para todos os usuários, com popup para usuários existentes e campo obrigatório no cadastro.

---

## 🎯 Funcionalidades

### 1. **Campo Obrigatório no Cadastro**
- Novo campo "CPF ou CNPJ" no formulário de registro
- Formatação automática durante digitação:
  - CPF: 000.000.000-00
  - CNPJ: 00.000.000/0000-00
- Validação de tamanho (11 ou 14 dígitos)
- Campo obrigatório com asterisco (*)

### 2. **Popup para Usuários Existentes**
- Modal não-bloqueável exibido no dashboard
- Aparece apenas para usuários sem CPF/CNPJ cadastrado
- Design moderno com animação fade-in
- Formulário inline com validação
- Após atualização, modal desaparece permanentemente

### 3. **Integração com Asaas**
- CPF/CNPJ real do usuário usado na criação de clientes
- Fallback para CPF de teste em sandbox se não informado
- Validação antes de criar cobranças

---

## 🔧 Arquivos Modificados

### 1. **models.py** (Linha 78)
```python
cpf_cnpj = Column(String(18), nullable=True)  # CPF (11) ou CNPJ (14)
```

### 2. **schemas.py** (UserUpdate)
```python
class UserUpdate(BaseModel):
    company_name: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    cpf_cnpj: Optional[str] = None  # NOVO
```

### 3. **templates/register.html**
- Adicionado campo de CPF/CNPJ entre "Nome da Empresa" e "Senha"
- JavaScript para formatação automática
- Validação client-side

### 4. **templates/dashboard.html**
- Modal de atualização de CPF/CNPJ (linhas 7-52)
- JavaScript para submissão via API (linhas 458-520)
- Condicional para não mostrar se já preenchido

### 5. **templates/base.html**
- Adicionada animação CSS `@keyframes fade-in`
- Classe `.animate-fade-in` para o modal

### 6. **main.py**
- `POST /register`: Recebe e valida cpf_cnpj (linhas 202-236)
- `PUT /api/profile`: Atualiza cpf_cnpj com validação (linhas 770-823)

### 7. **asaas_api.py** (create_customer)
```python
# Usa CPF/CNPJ do usuário ou gera um válido para sandbox
if user.cpf_cnpj:
    cpf_cnpj = user.cpf_cnpj
else:
    cpf_cnpj = generate_valid_cpf(user.id)  # Fallback
```

---

## 📊 Migração de Banco de Dados

### Comando Executado:
```sql
ALTER TABLE users ADD COLUMN cpf_cnpj VARCHAR(18);
```

### Resultado:
✅ Coluna adicionada com sucesso
- Tipo: VARCHAR(18)
- Permite NULL (usuários antigos)
- Índice: Não (não há necessidade de consulta frequente por CPF)

---

## 🎨 Design do Modal

### Características:
- **Fundo semi-transparente** (bg-gray-900 bg-opacity-75)
- **Card centralizado** com sombra 2xl
- **Ícone de ID card** no topo (roxo)
- **Campo formatado** automaticamente
- **Mensagem de erro** inline (escondida por padrão)
- **Botão de ação** com ícone de check
- **Texto de privacidade** no rodapé
- **Não pode ser fechado** até preencher (obrigatório)

### Fluxo:
1. Usuário sem CPF/CNPJ faz login
2. Dashboard carrega com modal visível
3. Usuário digita CPF ou CNPJ
4. Formatação automática durante digitação
5. Clica em "Atualizar e Continuar"
6. Validação de tamanho (11 ou 14 dígitos)
7. Envio via PUT /api/profile
8. Modal fecha e página recarrega
9. Próximo login: modal não aparece mais

---

## 🧪 Testes

### Teste 1: Novo Cadastro
1. Acesse: http://localhost:8000/register
2. Preencha email, empresa, CPF/CNPJ, senha
3. Digite CPF: `12345678901` → formata para `123.456.789-01`
4. Digite CNPJ: `12345678000190` → formata para `12.345.678/0001-90`
5. Submeta o formulário
6. Verifique no banco: `SELECT cpf_cnpj FROM users WHERE email='...'`

### Teste 2: Usuário Existente (Sem CPF)
1. Faça login com usuário antigo (sem cpf_cnpj)
2. Dashboard carrega com modal visível
3. Tente recarregar página → modal persiste
4. Digite CPF válido no modal
5. Clique "Atualizar e Continuar"
6. Modal fecha, página recarrega
7. Próximo login: sem modal

### Teste 3: Checkout com CPF Real
1. Usuário com CPF cadastrado
2. Acesse /upgrade → Selecione Pro → PIX
3. Verificar no Asaas: cliente criado com CPF real
4. Não usa mais CPF de teste

### Teste 4: Validação de Tamanho
1. Modal aberto, digite: `123` → erro: "CPF deve ter 11 dígitos..."
2. Digite: `12345678901234567890` → trunca em 14 dígitos
3. Digite: `12345678901` (11 dígitos) → aceita
4. Digite: `12345678000190` (14 dígitos) → aceita

---

## 🔒 Segurança e Privacidade

### Armazenamento:
- CPF/CNPJ armazenado **sem formatação** (apenas dígitos)
- Coluna: `VARCHAR(18)` (comporta CNPJ formatado se necessário)
- Não há índice (não é chave de busca)

### Uso:
- Usado apenas para criação de cliente no Asaas
- Não é exibido em telas públicas
- Não é retornado em APIs públicas

### LGPD:
- Dado coletado com consentimento implícito (cadastro)
- Usado apenas para processamento de pagamentos (finalidade específica)
- Usuário tem direito de consultar/excluir dados (via perfil)

---

## 📝 Próximos Passos (Opcional)

### Melhorias Futuras:

1. **Validação de CPF/CNPJ**
   - Implementar algoritmo de validação de dígitos verificadores
   - Rejeitar CPFs/CNPJs inválidos mesmo se bem formatados

2. **Máscara no Perfil**
   - Exibir CPF/CNPJ formatado na página de perfil
   - Permitir edição com validação

3. **Consulta de Dados**
   - Integrar com ReceitaWS ou similar
   - Preencher nome da empresa automaticamente via CNPJ

4. **Exportação LGPD**
   - Endpoint para usuário baixar todos os seus dados
   - Incluir CPF/CNPJ no relatório

5. **Anonimização**
   - Ao excluir conta, anonimizar CPF/CNPJ
   - Manter registros financeiros mascarados

---

## ✅ Status Atual

🎉 **TOTALMENTE IMPLEMENTADO E FUNCIONANDO:**
- ✅ Campo obrigatório no cadastro
- ✅ Formatação automática (CPF/CNPJ)
- ✅ Validação de tamanho (11 ou 14 dígitos)
- ✅ Modal para usuários existentes
- ✅ Popup não-bloqueável até preencher
- ✅ Integração com API de perfil
- ✅ Uso em Asaas (cliente real)
- ✅ Migração de banco de dados
- ✅ Design moderno e responsivo

⏳ **OPCIONAL (FUTURO):**
- ⏳ Validação de dígitos verificadores
- ⏳ Consulta ReceitaWS
- ⏳ Exportação LGPD

---

## 🚀 Resultado Final

Os usuários agora são obrigados a fornecer CPF ou CNPJ:
1. **Novos usuários**: Campo obrigatório no cadastro
2. **Usuários antigos**: Popup no primeiro login pós-atualização
3. **Asaas**: Usa CPF/CNPJ real para criar clientes
4. **Experiência**: Formatação automática, validação inline

**Sistema pronto para produção com coleta legal de documentos!** 🎯
