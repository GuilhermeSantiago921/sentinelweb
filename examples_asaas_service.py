"""
Exemplo de Uso do AsaasService
===============================
Script demonstrativo de como usar o AsaasService
em cenários reais do SentinelWeb.
"""

from services.asaas import AsaasService, AsaasAPIError
from database import get_db
from models import User

# ============================================
# EXEMPLO 1: Criar Cliente e Assinatura
# ============================================

def exemplo_criar_assinatura():
    """
    Cenário: Usuário clica em "Upgrade para Pro" na página /upgrade
    """
    # Simula banco de dados e usuário
    db = next(get_db())
    user = db.query(User).filter(User.email == "teste@exemplo.com").first()
    
    if not user:
        print("❌ Usuário não encontrado")
        return
    
    print("=" * 60)
    print("🚀 EXEMPLO 1: Criar Assinatura Pro com PIX")
    print("=" * 60)
    
    try:
        # Inicializa o serviço
        service = AsaasService(db)
        print(f"✅ AsaasService inicializado")
        print(f"📍 Base URL: {service.base_url}")
        print(f"🔑 Token: {service.config.asaas_api_token[:20]}...")
        print()
        
        # Cria assinatura
        print("💳 Criando assinatura...")
        success, subscription, error = service.create_subscription(
            user=user,
            plan_type='pro',
            billing_type='PIX'
        )
        
        if success:
            print()
            print("✅ SUCESSO! Assinatura criada")
            print(f"   ID da Assinatura: {subscription['subscription_id']}")
            print(f"   ID do Cliente: {subscription['customer_id']}")
            print(f"   Plano: {subscription['plan'].upper()}")
            print(f"   Valor: R$ {subscription['value']:.2f}/mês")
            print(f"   Vencimento: {subscription['next_due_date']}")
            print(f"   Status: {subscription['status']}")
            print()
            print("🔗 Link de Pagamento:")
            print(f"   {subscription['invoice_url']}")
            print()
            print("📱 Instruções:")
            print("   1. Acesse o link acima")
            print("   2. Escaneie o QR Code com o app do seu banco")
            print("   3. Confirme o pagamento de R$ 49,90")
            print("   4. Aguarde a confirmação (geralmente instantânea)")
        else:
            print(f"❌ ERRO: {error}")
    
    except AsaasAPIError as e:
        print(f"❌ Erro na API do Asaas: {e}")
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    
    finally:
        db.close()


# ============================================
# EXEMPLO 2: Verificar Assinaturas Existentes
# ============================================

def exemplo_listar_assinaturas():
    """
    Cenário: Usuário acessa "Minha Conta" para ver sua assinatura atual
    """
    db = next(get_db())
    user = db.query(User).filter(User.email == "teste@exemplo.com").first()
    
    if not user or not user.asaas_customer_id:
        print("❌ Usuário não possui assinaturas no Asaas")
        return
    
    print()
    print("=" * 60)
    print("📋 EXEMPLO 2: Listar Assinaturas do Usuário")
    print("=" * 60)
    
    try:
        service = AsaasService(db)
        
        print(f"🔍 Buscando assinaturas do cliente: {user.asaas_customer_id}")
        subscriptions = service.get_customer_subscriptions(user.asaas_customer_id)
        
        if not subscriptions:
            print("ℹ️  Nenhuma assinatura encontrada")
            return
        
        print(f"✅ Encontradas {len(subscriptions)} assinatura(s):")
        print()
        
        for i, sub in enumerate(subscriptions, 1):
            print(f"   {i}. ID: {sub['id']}")
            print(f"      Status: {sub['status']}")
            print(f"      Valor: R$ {sub['value']:.2f}/mês")
            print(f"      Ciclo: {sub['cycle']}")
            print(f"      Próximo Vencimento: {sub['nextDueDate']}")
            print(f"      Forma de Pagamento: {sub['billingType']}")
            print()
    
    except AsaasAPIError as e:
        print(f"❌ Erro: {e}")
    
    finally:
        db.close()


# ============================================
# EXEMPLO 3: Cancelar Assinatura
# ============================================

def exemplo_cancelar_assinatura(subscription_id: str):
    """
    Cenário: Usuário clica em "Cancelar Assinatura" no painel
    """
    db = next(get_db())
    
    print()
    print("=" * 60)
    print("🗑️  EXEMPLO 3: Cancelar Assinatura")
    print("=" * 60)
    
    try:
        service = AsaasService(db)
        
        print(f"⚠️  Cancelando assinatura: {subscription_id}")
        print("   Esta ação não pode ser desfeita!")
        print()
        
        success, error = service.cancel_subscription(subscription_id)
        
        if success:
            print("✅ Assinatura cancelada com sucesso")
            print()
            print("ℹ️  Próximos passos:")
            print("   1. O plano atual permanece ativo até o fim do período pago")
            print("   2. Não haverá renovação automática")
            print("   3. Após o vencimento, o plano será downgrade para Free")
        else:
            print(f"❌ Erro ao cancelar: {error}")
    
    except AsaasAPIError as e:
        print(f"❌ Erro: {e}")
    
    finally:
        db.close()


# ============================================
# EXEMPLO 4: Fluxo Completo de Checkout
# ============================================

def exemplo_fluxo_completo():
    """
    Cenário: Fluxo completo desde o upgrade até a confirmação
    """
    db = next(get_db())
    user = db.query(User).filter(User.email == "teste@exemplo.com").first()
    
    print()
    print("=" * 60)
    print("🎯 EXEMPLO 4: Fluxo Completo de Checkout")
    print("=" * 60)
    
    try:
        service = AsaasService(db)
        
        # Passo 1: Verificar configuração
        print("1️⃣  Verificando configuração do Asaas...")
        print(f"   ✅ Modo: {'Sandbox' if service.config.is_sandbox else 'Produção'}")
        print(f"   ✅ Token configurado: Sim")
        print()
        
        # Passo 2: Criar/Recuperar cliente
        print("2️⃣  Criando cliente no Asaas...")
        customer_id = service.create_customer(user)
        print(f"   ✅ Cliente ID: {customer_id}")
        print()
        
        # Passo 3: Criar assinatura Agency com Boleto
        print("3️⃣  Criando assinatura Agency com Boleto...")
        success, subscription, error = service.create_subscription(
            user=user,
            plan_type='agency',
            billing_type='BOLETO'
        )
        
        if not success:
            print(f"   ❌ Erro: {error}")
            return
        
        print(f"   ✅ Assinatura criada: {subscription['subscription_id']}")
        print()
        
        # Passo 4: Exibir informações de pagamento
        print("4️⃣  Informações de Pagamento:")
        print(f"   💰 Valor: R$ {subscription['value']:.2f}")
        print(f"   📅 Vencimento: {subscription['next_due_date']}")
        print(f"   🎫 Tipo: {subscription['billing_type']}")
        print()
        print("   🔗 Link do Boleto:")
        print(f"   {subscription['invoice_url']}")
        print()
        
        # Passo 5: Próximos passos
        print("5️⃣  Próximos Passos:")
        print("   ✅ Boleto gerado com sucesso")
        print("   📧 Email enviado para o usuário (implementar)")
        print("   ⏳ Aguardando confirmação de pagamento")
        print("   🔔 Webhook notificará quando pago (implementar)")
        print()
        
        return subscription
    
    except AsaasAPIError as e:
        print(f"❌ Erro: {e}")
    
    finally:
        db.close()


# ============================================
# EXECUTAR EXEMPLOS
# ============================================

if __name__ == "__main__":
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "ASAAS SERVICE - EXEMPLOS" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Exemplo 1: Criar assinatura
    exemplo_criar_assinatura()
    
    # Exemplo 2: Listar assinaturas
    exemplo_listar_assinaturas()
    
    # Exemplo 3: Cancelar (descomente para testar)
    # exemplo_cancelar_assinatura('sub_ABC123')
    
    # Exemplo 4: Fluxo completo
    exemplo_fluxo_completo()
    
    print()
    print("=" * 60)
    print("✅ Todos os exemplos executados!")
    print("=" * 60)
    print()
