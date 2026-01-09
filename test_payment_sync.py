#!/usr/bin/env python3
"""
Script de Teste - Sincronização de Pagamentos Asaas
====================================================
Testa a sincronização manual de pagamentos com a API do Asaas.

Uso:
    python test_payment_sync.py [payment_id]

Exemplos:
    python test_payment_sync.py 1          # Sincroniza pagamento ID 1
    python test_payment_sync.py            # Sincroniza todos os pendentes
"""

import sys
from database import SessionLocal
from models import Payment, PaymentStatus
from asaas_api import AsaasAPI


def sync_payment(payment_id: int):
    """Sincroniza um pagamento específico"""
    db = SessionLocal()
    
    try:
        # Busca pagamento
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            print(f"❌ Pagamento {payment_id} não encontrado")
            return False
        
        print(f"\n🔍 Pagamento #{payment.id}")
        print(f"   Asaas ID: {payment.asaas_id}")
        print(f"   Valor: R$ {payment.value:.2f}")
        print(f"   Status atual: {payment.status.value}")
        print(f"   Usuário ID: {payment.user_id}")
        
        # Tenta sincronizar
        print(f"\n🔄 Sincronizando com Asaas...")
        
        asaas = AsaasAPI(db)
        success = asaas.sync_payment(payment)
        
        if success:
            print(f"✅ Sincronização bem-sucedida!")
            print(f"   Novo status: {payment.status.value}")
            print(f"   Pago: {'Sim' if payment.is_paid else 'Não'}")
            
            if payment.payment_date:
                print(f"   Data pagamento: {payment.payment_date.strftime('%d/%m/%Y %H:%M')}")
            
            return True
        else:
            print(f"❌ Falha na sincronização")
            return False
    
    except ValueError as e:
        print(f"⚠️  {e}")
        print(f"\n💡 Dica: Configure a API do Asaas em /admin/config")
        return False
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()


def sync_all_pending():
    """Sincroniza todos os pagamentos pendentes"""
    db = SessionLocal()
    
    try:
        # Busca pagamentos pendentes
        pending_payments = db.query(Payment).filter(
            Payment.status == PaymentStatus.PENDING
        ).all()
        
        if not pending_payments:
            print("✅ Nenhum pagamento pendente para sincronizar")
            return
        
        print(f"\n📋 Encontrados {len(pending_payments)} pagamento(s) pendente(s)\n")
        
        success_count = 0
        fail_count = 0
        
        for payment in pending_payments:
            print(f"─" * 60)
            
            if sync_payment(payment.id):
                success_count += 1
            else:
                fail_count += 1
            
            print()
        
        print(f"─" * 60)
        print(f"\n📊 Resumo:")
        print(f"   ✅ Sincronizados: {success_count}")
        print(f"   ❌ Falhas: {fail_count}")
        print(f"   📝 Total: {len(pending_payments)}")
    
    finally:
        db.close()


def list_payments():
    """Lista todos os pagamentos"""
    db = SessionLocal()
    
    try:
        payments = db.query(Payment).order_by(Payment.created_at.desc()).all()
        
        if not payments:
            print("📭 Nenhum pagamento registrado")
            return
        
        print(f"\n📋 Total de {len(payments)} pagamento(s):\n")
        print(f"{'ID':<5} {'Asaas ID':<15} {'Valor':<12} {'Status':<15} {'Usuário':<8}")
        print(f"─" * 70)
        
        for payment in payments:
            status_icon = {
                PaymentStatus.PENDING: "⏳",
                PaymentStatus.RECEIVED: "✅",
                PaymentStatus.CONFIRMED: "✔️",
                PaymentStatus.OVERDUE: "❌",
                PaymentStatus.REFUNDED: "↩️"
            }.get(payment.status, "📄")
            
            print(f"{payment.id:<5} "
                  f"{payment.asaas_id[:15]:<15} "
                  f"R$ {payment.value:>8.2f} "
                  f"{status_icon} {payment.status.value:<13} "
                  f"User #{payment.user_id}")
    
    finally:
        db.close()


def main():
    """Função principal"""
    print("=" * 70)
    print("🔄 TESTE DE SINCRONIZAÇÃO - ASAAS PAYMENT GATEWAY")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        # Sincroniza pagamento específico
        try:
            payment_id = int(sys.argv[1])
            sync_payment(payment_id)
        except ValueError:
            print(f"❌ ID inválido: {sys.argv[1]}")
            print(f"\nUso: python {sys.argv[0]} [payment_id]")
            sys.exit(1)
    else:
        # Menu interativo
        print("\nEscolha uma opção:")
        print("1. Listar todos os pagamentos")
        print("2. Sincronizar todos os pendentes")
        print("3. Sincronizar pagamento específico")
        print("0. Sair")
        
        choice = input("\nOpção: ").strip()
        
        if choice == "1":
            list_payments()
        
        elif choice == "2":
            sync_all_pending()
        
        elif choice == "3":
            payment_id = input("ID do pagamento: ").strip()
            try:
                sync_payment(int(payment_id))
            except ValueError:
                print(f"❌ ID inválido: {payment_id}")
        
        elif choice == "0":
            print("👋 Até logo!")
        
        else:
            print("❌ Opção inválida")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
