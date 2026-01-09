#!/usr/bin/env python3
"""
Script para criar pagamentos de exemplo para testar o módulo financeiro.
"""

from database import SessionLocal
from models import User, Payment, PaymentStatus, BillingType
from datetime import datetime, timedelta
import random

def create_sample_payments():
    db = SessionLocal()
    
    try:
        # Busca usuários existentes
        users = db.query(User).filter(User.is_active == True).all()
        
        if not users:
            print("❌ Nenhum usuário encontrado. Crie usuários primeiro.")
            return
        
        print(f"📊 Criando pagamentos de exemplo para {len(users)} usuários...\n")
        
        # Cria 10 pagamentos variados
        payments_data = [
            {
                "user": random.choice(users),
                "asaas_id": f"pay_{random.randint(100000, 999999)}",
                "value": 49.00,
                "status": PaymentStatus.RECEIVED,
                "billing_type": BillingType.PIX,
                "due_date": datetime.now() - timedelta(days=5),
                "payment_date": datetime.now() - timedelta(days=3),
                "net_value": 47.55,
                "invoice_url": "https://sandbox.asaas.com/i/12345"
            },
            {
                "user": random.choice(users),
                "asaas_id": f"pay_{random.randint(100000, 999999)}",
                "value": 149.00,
                "status": PaymentStatus.CONFIRMED,
                "billing_type": BillingType.CREDIT_CARD,
                "due_date": datetime.now() - timedelta(days=10),
                "payment_date": datetime.now() - timedelta(days=8),
                "net_value": 144.03,
                "invoice_url": "https://sandbox.asaas.com/i/12346"
            },
            {
                "user": random.choice(users),
                "asaas_id": f"pay_{random.randint(100000, 999999)}",
                "value": 49.00,
                "status": PaymentStatus.PENDING,
                "billing_type": BillingType.BOLETO,
                "due_date": datetime.now() + timedelta(days=3),
                "bank_slip_url": "https://sandbox.asaas.com/b/78901"
            },
            {
                "user": random.choice(users),
                "asaas_id": f"pay_{random.randint(100000, 999999)}",
                "value": 49.00,
                "status": PaymentStatus.OVERDUE,
                "billing_type": BillingType.BOLETO,
                "due_date": datetime.now() - timedelta(days=7),
                "bank_slip_url": "https://sandbox.asaas.com/b/78902"
            },
            {
                "user": random.choice(users),
                "asaas_id": f"pay_{random.randint(100000, 999999)}",
                "value": 149.00,
                "status": PaymentStatus.RECEIVED,
                "billing_type": BillingType.PIX,
                "due_date": datetime.now() - timedelta(days=2),
                "payment_date": datetime.now() - timedelta(days=1),
                "net_value": 144.03,
                "pix_qr_code": "00020126580014br.gov.bcb.pix...",
                "invoice_url": "https://sandbox.asaas.com/i/12347"
            },
            {
                "user": random.choice(users),
                "asaas_id": f"pay_{random.randint(100000, 999999)}",
                "value": 49.00,
                "status": PaymentStatus.PENDING,
                "billing_type": BillingType.PIX,
                "due_date": datetime.now() + timedelta(days=7),
                "pix_qr_code": "00020126580014br.gov.bcb.pix..."
            },
            {
                "user": random.choice(users),
                "asaas_id": f"pay_{random.randint(100000, 999999)}",
                "value": 149.00,
                "status": PaymentStatus.OVERDUE,
                "billing_type": BillingType.BOLETO,
                "due_date": datetime.now() - timedelta(days=15),
                "bank_slip_url": "https://sandbox.asaas.com/b/78903"
            },
            {
                "user": random.choice(users),
                "asaas_id": f"pay_{random.randint(100000, 999999)}",
                "value": 49.00,
                "status": PaymentStatus.CONFIRMED,
                "billing_type": BillingType.CREDIT_CARD,
                "due_date": datetime.now() - timedelta(days=20),
                "payment_date": datetime.now() - timedelta(days=19),
                "confirmed_date": datetime.now() - timedelta(days=18),
                "net_value": 47.55,
                "invoice_url": "https://sandbox.asaas.com/i/12348"
            },
            {
                "user": random.choice(users),
                "asaas_id": f"pay_{random.randint(100000, 999999)}",
                "value": 149.00,
                "status": PaymentStatus.RECEIVED,
                "billing_type": BillingType.PIX,
                "due_date": datetime.now(),
                "payment_date": datetime.now(),
                "net_value": 144.03,
                "invoice_url": "https://sandbox.asaas.com/i/12349"
            },
            {
                "user": random.choice(users),
                "asaas_id": f"pay_{random.randint(100000, 999999)}",
                "value": 49.00,
                "status": PaymentStatus.PENDING,
                "billing_type": BillingType.BOLETO,
                "due_date": datetime.now() + timedelta(days=2),
                "bank_slip_url": "https://sandbox.asaas.com/b/78904"
            }
        ]
        
        created_count = 0
        for payment_data in payments_data:
            payment = Payment(**payment_data)
            db.add(payment)
            created_count += 1
            
            status_icon = {
                PaymentStatus.RECEIVED: "✅",
                PaymentStatus.CONFIRMED: "✔️",
                PaymentStatus.PENDING: "⏳",
                PaymentStatus.OVERDUE: "❌"
            }.get(payment_data['status'], "📄")
            
            print(f"{status_icon} Pagamento criado: R$ {payment_data['value']:.2f} - "
                  f"{payment_data['status'].value} ({payment_data['billing_type'].value}) - "
                  f"Usuário: {payment_data['user'].email}")
        
        db.commit()
        
        print(f"\n✅ {created_count} pagamentos criados com sucesso!")
        print("\n📊 Resumo:")
        print(f"   - Recebidos/Confirmados: {sum(1 for p in payments_data if p['status'] in [PaymentStatus.RECEIVED, PaymentStatus.CONFIRMED])}")
        print(f"   - Pendentes: {sum(1 for p in payments_data if p['status'] == PaymentStatus.PENDING)}")
        print(f"   - Vencidos: {sum(1 for p in payments_data if p['status'] == PaymentStatus.OVERDUE)}")
        print(f"\n💰 Receita Total: R$ {sum(p['value'] for p in payments_data if p['status'] in [PaymentStatus.RECEIVED, PaymentStatus.CONFIRMED]):.2f}")
        
        print("\n🌐 Acesse o admin para visualizar: http://localhost:8000/admin/payments")
        
    except Exception as e:
        print(f"❌ Erro ao criar pagamentos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  CRIADOR DE PAGAMENTOS DE EXEMPLO - MÓDULO FINANCEIRO")
    print("=" * 60)
    print()
    
    create_sample_payments()
