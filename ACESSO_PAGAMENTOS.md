# 🔐 GUIA DE ACESSO - MÓDULO FINANCEIRO

## ✅ Status: Sistema Operacional

- **20 pagamentos** criados no banco de dados
- **Receita Mensal**: R$ 694,00
- **Receita Total**: R$ 1.090,00
- **Admin**: admin@sentinelweb.com (ativo)

---

## 🚀 COMO ACESSAR

### Passo 1: Fazer Login como Admin

1. Abra o navegador em: **http://localhost:8000/login**

2. Use as credenciais do admin:
   - **Email**: `admin@sentinelweb.com`
   - **Senha**: A senha que você definiu ao criar o usuário

3. Se não lembra a senha, rode:
   ```bash
   docker-compose exec web python create_superuser.py
   ```
   E crie um novo admin com senha conhecida.

---

### Passo 2: Acessar o Painel de Pagamentos

Após fazer login, você pode acessar:

1. **Dashboard Admin**: http://localhost:8000/admin
   - Verá 5 cards de KPIs
   - O 4º card mostra "💰 Receita Mensal"

2. **Configurações Asaas**: http://localhost:8000/admin/config
   - Configure o token da API
   - Defina modo sandbox
   - Configure preços dos planos

3. **Lista de Pagamentos**: http://localhost:8000/admin/payments
   - Veja todos os 20 pagamentos
   - Filtros por status
   - Export CSV

---

## 🔍 VERIFICAÇÃO RÁPIDA

Se quiser testar sem navegador, use curl com cookie:

```bash
# 1. Fazer login e salvar cookie
curl -c cookies.txt -X POST http://localhost:8000/login \
  -d "email=admin@sentinelweb.com" \
  -d "password=SUA_SENHA_AQUI"

# 2. Acessar página de pagamentos com cookie
curl -b cookies.txt http://localhost:8000/admin/payments
```

---

## 🐛 TROUBLESHOOTING

### Problema: "Página em branco" ou "401 Unauthorized"
**Solução**: Você não está logado como admin
- Faça logout: http://localhost:8000/logout
- Faça login novamente com credenciais de admin

### Problema: "Não consigo fazer login"
**Solução**: Crie um novo superuser
```bash
docker-compose exec web python create_superuser.py
```

### Problema: "Página carrega mas está vazia"
**Solução**: Verifique se há pagamentos no banco
```bash
docker-compose exec web python debug_payments.py
```

Se não houver pagamentos, crie alguns:
```bash
docker-compose exec web python create_sample_payments.py
```

---

## 📊 O QUE VOCÊ DEVE VER

### Dashboard Admin (/admin)
```
┌─────────────────────────────────────────────────────┐
│ Total Usuários │ Sites │ MRR │ 💰 Receita Mensal │  │
│       2        │   3   │ R$0 │   R$ 694,00      │  │
└─────────────────────────────────────────────────────┘
```

### Página de Pagamentos (/admin/payments)
```
┌────────────────────────────────────────────────┐
│  KPI Cards (5)                                 │
│  - Receita Mensal: R$ 694,00                   │
│  - Receita Total: R$ 1.090,00                  │
│  - Recebidos: 10 | Pendentes: 6 | Vencidos: 4 │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│  Filtros                                       │
│  [Todos] [Pendentes] [Recebidos] [Vencidos]   │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│  Tabela com 20 pagamentos                      │
│  ID | Usuário | Valor | Status | Tipo | Ações │
│  ─────────────────────────────────────────────│
│  11 | guilh...| R$49  | ✅ Rec.| PIX  | 🔄 📄│
│  12 | admin@..| R$149 | ✔️ Conf| Cart | 🔄 📄│
│  ...                                           │
└────────────────────────────────────────────────┘
```

---

## 🎯 TESTE COMPLETO

Execute este script para verificar tudo:

```bash
cd "/Users/guilherme/Documents/Sistema de monitoramento/sentinelweb"

# 1. Verificar admin existe
docker-compose exec web python -c "
from database import SessionLocal
from models import User
db = SessionLocal()
admin = db.query(User).filter(User.is_superuser == True).first()
print('✅ Admin:' if admin else '❌ Sem admin:', admin.email if admin else 'N/A')
db.close()
"

# 2. Verificar pagamentos existem
docker-compose exec web python debug_payments.py

# 3. Verificar servidor está rodando
curl -I http://localhost:8000/health

# 4. Acessar admin (precisa estar logado)
open http://localhost:8000/admin
```

---

## 📝 CREDENCIAIS PADRÃO

Se você executou `create_superuser.py`, as credenciais padrão são:

- **Email**: admin@sentinelweb.com
- **Senha**: admin123 (ou a que você definiu)
- **Superuser**: Sim
- **Ativo**: Sim

---

## 🆘 SUPORTE

Se ainda não conseguir acessar:

1. Verifique logs do container:
   ```bash
   docker-compose logs web --tail=50
   ```

2. Reinicie o container:
   ```bash
   docker-compose restart web
   ```

3. Acesse o container diretamente:
   ```bash
   docker-compose exec web bash
   python
   >>> from database import SessionLocal
   >>> from models import Payment
   >>> db = SessionLocal()
   >>> db.query(Payment).count()
   20
   ```

---

**Tudo está funcionando! Basta fazer login como admin. ✅**
