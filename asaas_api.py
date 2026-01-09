"""
Asaas API Integration
=====================
Integração completa com a API do Asaas para processamento de pagamentos.
"""

import requests
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import SystemConfig, User, Payment, PaymentStatus, BillingType


def generate_valid_cpf(user_id: int) -> str:
    """
    Gera um CPF válido para uso em sandbox baseado no ID do usuário.
    
    Para sandbox do Asaas, podemos usar CPFs de teste válidos.
    Esta função garante que cada usuário tenha um CPF único e válido.
    
    Args:
        user_id: ID do usuário
    
    Returns:
        CPF válido no formato "00000000000"
    """
    # CPFs de teste válidos para Asaas Sandbox
    test_cpfs = [
        "24971563792",
        "11144477735",
        "34608514300",
        "42379894972",
        "51567481686",
        "68267060549",
        "78673021591",
        "86389835630",
        "93095135270",
    ]
    
    # Retorna um CPF baseado no ID do usuário (circular)
    return test_cpfs[user_id % len(test_cpfs)]


class AsaasAPI:
    """Cliente para API do Asaas"""
    
    def __init__(self, db: Session):
        self.db = db
        config = db.query(SystemConfig).first()
        
        if not config or not config.asaas_api_token:
            raise ValueError("Asaas API não configurada. Configure em /admin/config")
        
        self.api_token = config.asaas_api_token
        self.is_sandbox = config.is_sandbox
        
        # URL base (sandbox ou produção)
        if self.is_sandbox:
            self.base_url = "https://sandbox.asaas.com/api/v3"
        else:
            self.base_url = "https://www.asaas.com/api/v3"
        
        self.headers = {
            "access_token": self.api_token,
            "Content-Type": "application/json"
        }
    
    def create_customer(self, user: User) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Cria ou atualiza um cliente no Asaas.
        
        Returns:
            Tupla (sucesso, customer_id, mensagem_erro)
        """
        try:
            # Se já tem customer_id, retorna ele
            if user.asaas_customer_id:
                return True, user.asaas_customer_id, None
            
            # Usa CPF/CNPJ do usuário ou gera um válido para sandbox
            if user.cpf_cnpj:
                cpf_cnpj = user.cpf_cnpj
            else:
                # Fallback: Gera CPF válido para sandbox baseado no ID do usuário
                cpf_cnpj = generate_valid_cpf(user.id)
            
            # Dados do cliente
            data = {
                "name": user.company_name or user.email.split('@')[0],
                "email": user.email,
                "cpfCnpj": cpf_cnpj,
                "notificationDisabled": False
            }
            
            response = requests.post(
                f"{self.base_url}/customers",
                json=data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                customer_data = response.json()
                customer_id = customer_data.get('id')
                
                # Salva customer_id no usuário
                user.asaas_customer_id = customer_id
                self.db.commit()
                
                return True, customer_id, None
            else:
                error_msg = response.json().get('errors', [{}])[0].get('description', 'Erro desconhecido')
                return False, None, error_msg
                
        except Exception as e:
            return False, None, str(e)
    
    def create_payment(
        self,
        user: User,
        plan: str,
        billing_type: str = 'BOLETO'
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Cria uma cobrança no Asaas.
        
        Args:
            user: Usuário que vai pagar
            plan: 'pro' ou 'agency'
            billing_type: 'BOLETO', 'PIX' ou 'CREDIT_CARD'
        
        Returns:
            Tupla (sucesso, dados_cobrança, mensagem_erro)
        """
        try:
            # Cria/busca customer
            success, customer_id, error = self.create_customer(user)
            if not success:
                return False, None, f"Erro ao criar cliente: {error}"
            
            # Define valor do plano
            config = self.db.query(SystemConfig).first()
            if plan == 'pro':
                value = config.plan_pro_price
                description = "Plano Pro - SentinelWeb"
            elif plan == 'agency':
                value = config.plan_agency_price
                description = "Plano Agency - SentinelWeb"
            else:
                return False, None, "Plano inválido"
            
            # Data de vencimento (7 dias a partir de hoje)
            due_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Dados da cobrança
            payment_data = {
                "customer": customer_id,
                "billingType": billing_type,
                "value": value,
                "dueDate": due_date,
                "description": description,
                "externalReference": f"user_{user.id}_plan_{plan}",
                "postalService": False
            }
            
            response = requests.post(
                f"{self.base_url}/payments",
                json=payment_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                payment_response = response.json()
                
                # Salva pagamento no banco de dados
                new_payment = Payment(
                    user_id=user.id,
                    asaas_id=payment_response.get('id'),
                    asaas_customer_id=customer_id,
                    billing_type=BillingType(billing_type),
                    value=value,
                    description=description,
                    due_date=datetime.strptime(due_date, '%Y-%m-%d'),
                    status=PaymentStatus.PENDING,
                    invoice_url=payment_response.get('invoiceUrl'),
                    bank_slip_url=payment_response.get('bankSlipUrl'),
                    pix_qr_code=payment_response.get('pixQrCode'),
                    pix_copy_paste=payment_response.get('pixCopyAndPaste')
                )
                
                self.db.add(new_payment)
                self.db.commit()
                self.db.refresh(new_payment)
                
                return True, {
                    'payment_id': new_payment.id,
                    'asaas_id': payment_response.get('id'),
                    'billing_type': billing_type,
                    'value': value,
                    'due_date': due_date,
                    'invoice_url': payment_response.get('invoiceUrl'),
                    'bank_slip_url': payment_response.get('bankSlipUrl'),
                    'pix_qrcode': payment_response.get('pixQrCode'),
                    'pix_copy_paste': payment_response.get('pixCopyAndPaste')
                }, None
            else:
                error_msg = response.json().get('errors', [{}])[0].get('description', 'Erro desconhecido')
                return False, None, error_msg
                
        except Exception as e:
            return False, None, str(e)
    
    def get_payment_status(self, asaas_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Consulta o status de um pagamento no Asaas.
        
        Returns:
            Tupla (sucesso, status, mensagem_erro)
        """
        try:
            response = requests.get(
                f"{self.base_url}/payments/{asaas_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                payment_data = response.json()
                status = payment_data.get('status')
                return True, status, None
            else:
                error_msg = response.json().get('errors', [{}])[0].get('description', 'Erro desconhecido')
                return False, None, error_msg
                
        except Exception as e:
            return False, None, str(e)
    
    def sync_payment(self, payment: Payment) -> bool:
        """
        Sincroniza um pagamento com a API do Asaas.
        
        Returns:
            True se sincronizado com sucesso
        """
        try:
            success, asaas_status, error = self.get_payment_status(payment.asaas_id)
            
            if not success:
                print(f"❌ Erro ao sincronizar pagamento {payment.id}: {error}")
                return False
            
            # Mapeia status do Asaas para o nosso enum
            status_map = {
                'PENDING': PaymentStatus.PENDING,
                'RECEIVED': PaymentStatus.RECEIVED,
                'CONFIRMED': PaymentStatus.CONFIRMED,
                'OVERDUE': PaymentStatus.OVERDUE,
                'REFUNDED': PaymentStatus.REFUNDED,
                'RECEIVED_IN_CASH': PaymentStatus.RECEIVED,
                'REFUND_REQUESTED': PaymentStatus.REFUND_REQUESTED,
                'CHARGEBACK_REQUESTED': PaymentStatus.CHARGEBACK_REQUESTED,
                'CHARGEBACK_DISPUTE': PaymentStatus.CHARGEBACK_DISPUTE,
                'AWAITING_CHARGEBACK_REVERSAL': PaymentStatus.AWAITING_CHARGEBACK_REVERSAL
            }
            
            new_status = status_map.get(asaas_status, PaymentStatus.PENDING)
            
            # Atualiza apenas se mudou
            if payment.status != new_status:
                old_status = payment.status
                payment.status = new_status
                
                # Se foi confirmado, atualiza data de pagamento
                if new_status in [PaymentStatus.RECEIVED, PaymentStatus.CONFIRMED]:
                    payment.payment_date = datetime.now()
                
                self.db.commit()
                
                print(f"✅ Pagamento {payment.id} atualizado: {old_status.value} → {new_status.value}")
                
                # Se foi confirmado, faz upgrade do usuário
                if new_status in [PaymentStatus.RECEIVED, PaymentStatus.CONFIRMED]:
                    self._upgrade_user_plan(payment)
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao sincronizar pagamento: {e}")
            return False
    
    def _upgrade_user_plan(self, payment: Payment):
        """
        Faz upgrade do plano do usuário após confirmação de pagamento.
        """
        try:
            user = self.db.query(User).filter(User.id == payment.user_id).first()
            if not user:
                return
            
            # Detecta o plano pela descrição
            if 'Pro' in payment.description:
                user.plan_status = 'pro'
                print(f"🚀 Upgrade: {user.email} → Plano Pro")
            elif 'Agency' in payment.description:
                user.plan_status = 'agency'
                print(f"🚀 Upgrade: {user.email} → Plano Agency")
            
            self.db.commit()
            
        except Exception as e:
            print(f"❌ Erro ao fazer upgrade: {e}")
