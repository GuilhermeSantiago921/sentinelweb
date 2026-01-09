# 🐛 Fix: Internal Server Error no Dashboard

## Problema
Após adicionar um site, ao acessar `/dashboard`, retorna **Internal Server Error (500)**.

## Causa Raiz
O erro ocorre quando:
1. Usuário não tem `plan_status` definido (campo NULL ou vazio)
2. Usuário tem `plan_status` inválido (diferente de 'free', 'pro', 'agency')
3. Erro não tratado ao calcular estatísticas

## Solução Aplicada

### 1. Validação de `plan_status`
```python
# Garante que o usuário tem um plan_status válido
if not user.plan_status or user.plan_status not in ['free', 'pro', 'agency']:
    user.plan_status = 'free'
    db.commit()
```

### 2. Try/Catch com Log Detalhado
```python
try:
    # ... código do dashboard ...
except Exception as e:
    import traceback
    print(f"ERRO NO DASHBOARD: {str(e)}")
    print(traceback.format_exc())
    raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
```

## Como Aplicar no Servidor

```bash
cd /opt/sentinelweb
git pull
docker compose -f docker-compose.prod.yml restart web
```

## Verificar Logs de Erro

Se o erro persistir, verifique os logs:

```bash
# Ver logs do container web
docker compose -f docker-compose.prod.yml logs web --tail=100

# Acompanhar logs em tempo real
docker compose -f docker-compose.prod.yml logs -f web
```

## Correção Manual (Se Necessário)

Se alguns usuários ainda tiverem problemas, execute no container:

```bash
docker compose -f docker-compose.prod.yml exec web python << 'EOF'
from database import SessionLocal
from models import User

db = SessionLocal()
try:
    # Atualiza usuários sem plan_status
    users = db.query(User).filter(
        (User.plan_status == None) | 
        (~User.plan_status.in_(['free', 'pro', 'agency']))
    ).all()
    
    for user in users:
        user.plan_status = 'free'
        print(f"✓ Corrigido: {user.email} -> plan_status='free'")
    
    db.commit()
    print(f"\n✅ {len(users)} usuário(s) corrigido(s)")
finally:
    db.close()
EOF
```

## Prevenção

O modelo `User` já tem `default='free'` e `nullable=False`, mas para usuários antigos:

```python
# Em models.py (já corrigido)
plan_status = Column(String(20), default='free', nullable=False)
```

## Testes

1. **Adicionar site:** `/sites/add`
2. **Acessar dashboard:** `/dashboard`
3. **Verificar estatísticas:** Deve mostrar uso do plano

## Rollback (Se Necessário)

```bash
cd /opt/sentinelweb
git checkout 8a2520d  # Commit anterior
docker compose -f docker-compose.prod.yml restart web
```

---

**Status:** ✅ Corrigido  
**Versão:** 1.0  
**Data:** 09/01/2026
