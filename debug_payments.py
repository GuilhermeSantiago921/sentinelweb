#!/usr/bin/env python3
"""
Debug: Verifica pagamentos no banco de dados
"""

from database import SessionLocal
from models import Payment, PaymentStatus, User
from sqlalchemy import func

db = SessionLocal()

try:
    print("=" * 60)
    print("  DEBUG: VERIFICAÇÃO DE PAGAMENTOS")
    print("=" * 60)
    print()
    
    # Total de pagamentos
    total = db.query(Payment).count()
    print(f"📊 Total de pagamentos no banco: {total}")
    print()
    
    if total == 0:
        print("❌ Nenhum pagamento encontrado no banco!")
        print("   Execute: docker-compose exec web python create_sample_payments.py")
    else:
        # Lista todos os pagamentos
        payments = db.query(Payment).order_by(Payment.created_at.desc()).all()
        
        print("📋 LISTA DE PAGAMENTOS:")
        print("-" * 60)
        for p in payments:
            user = db.query(User).filter(User.id == p.user_id).first()
            print(f"ID: {p.id} | Valor: R$ {p.value:.2f} | Status: {p.status.value}")
            print(f"   Usuário: {user.email if user else 'N/A'}")
            print(f"   Tipo: {p.billing_type.value} | Vencimento: {p.due_date.strftime('%d/%m/%Y')}")
            print()
        
        # Estatísticas
        print("=" * 60)
        print("📈 ESTATÍSTICAS:")
        print("-" * 60)
        
        received = db.query(Payment).filter(
            Payment.status.in_([PaymentStatus.RECEIVED, PaymentStatus.CONFIRMED])
        ).count()
        print(f"✅ Recebidos/Confirmados: {received}")
        
        pending = db.query(Payment).filter(Payment.status == PaymentStatus.PENDING).count()
        print(f"⏳ Pendentes: {pending}")
        
        overdue = db.query(Payment).filter(Payment.status == PaymentStatus.OVERDUE).count()
        print(f"❌ Vencidos: {overdue}")
        
        # Receita
        from datetime import datetime
        now = datetime.now()
        first_day = datetime(now.year, now.month, 1)
        
        monthly_revenue = db.query(func.sum(Payment.value)).filter(
            Payment.status.in_([PaymentStatus.RECEIVED, PaymentStatus.CONFIRMED]),
            Payment.payment_date >= first_day
        ).scalar() or 0.0
        
        total_revenue = db.query(func.sum(Payment.value)).filter(
            Payment.status.in_([PaymentStatus.RECEIVED, PaymentStatus.CONFIRMED])
        ).scalar() or 0.0
        
        print(f"\n💰 Receita Mensal: R$ {monthly_revenue:.2f}")
        print(f"💰 Receita Total: R$ {total_revenue:.2f}")
        
        # Teste de properties
        print("\n" + "=" * 60)
        print("🔍 TESTE DE PROPERTIES:")
        print("-" * 60)
        first_payment = payments[0] if payments else None
        if first_payment:
            print(f"Pagamento ID: {first_payment.id}")
            print(f"  is_paid: {first_payment.is_paid}")
            print(f"  is_overdue: {first_payment.is_overdue}")
            print(f"  days_until_due: {first_payment.days_until_due}")
            print(f"  status_label: {first_payment.status_label}")
            print(f"  status_color: {first_payment.status_color}")

except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

print("\n" + "=" * 60)
