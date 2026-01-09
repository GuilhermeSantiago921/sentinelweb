"""
Asaas Payment Gateway Service
==============================
Serviço completo para integração com a API do Asaas.
Gerencia clientes, assinaturas e pagamentos recorrentes.

Documentação oficial: https://docs.asaas.com/reference/
"""

import requests
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models import User, SystemConfig
from database import get_db


class AsaasAPIError(Exception):
    """Exceção customizada para erros da API do Asaas"""
    pass


class AsaasService:
    """
    Serviço de integração com Asaas Payment Gateway.
    
    Features:
    - Criação automática de clientes
    - Gerenciamento de assinaturas recorrentes
    - Suporte a Sandbox e Produção
    - Tratamento robusto de erros
    
    Exemplo de uso:
        service = AsaasService(db)
        customer_id = service.create_customer(user)
        subscription = service.create_subscription(user, 'pro')
    """
    
    # URLs da API Asaas
    SANDBOX_BASE_URL = "https://sandbox.asaas.com/api/v3"
    PRODUCTION_BASE_URL = "https://www.asaas.com/api/v3"
    
    # Valores dos planos (em reais)
    PLAN_PRICES = {
        'free': 0.0,
        'pro': 49.90,
        'agency': 149.90
    }
    
    def __init__(self, db: Session):
        """
        Inicializa o serviço com configurações do banco de dados.
        
        Args:
            db: Sessão do SQLAlchemy para queries
        """
        self.db = db
        self.config = self._load_config()
        self.base_url = self._get_base_url()
        self.headers = self._get_headers()
    
    def _load_config(self) -> SystemConfig:
        """Carrega configurações do sistema do banco de dados"""
        config = self.db.query(SystemConfig).first()
        
        if not config:
            raise AsaasAPIError(
                "Configuração do sistema não encontrada. "
                "Execute as migrações ou configure via Admin."
            )
        
        if not config.asaas_api_token:
            raise AsaasAPIError(
                "Token da API Asaas não configurado. "
                "Acesse /admin/config para configurar."
            )
        
        return config
    
    def _get_base_url(self) -> str:
        """
        Retorna a URL base correta baseado no modo (sandbox/production).
        
        Returns:
            URL base da API Asaas
        """
        if self.config.is_sandbox:
            return self.SANDBOX_BASE_URL
        return self.PRODUCTION_BASE_URL
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Prepara headers HTTP para requisições à API.
        
        Returns:
            Dict com headers incluindo token de autenticação
        """
        return {
            'access_token': self.config.asaas_api_token,
            'Content-Type': 'application/json',
            'User-Agent': 'SentinelWeb/1.0'
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Faz requisição HTTP à API do Asaas com tratamento de erros.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API (ex: '/customers')
            data: Payload JSON (opcional)
        
        Returns:
            Resposta JSON da API
        
        Raises:
            AsaasAPIError: Se a requisição falhar
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            # Log da requisição (útil para debug)
            print(f"🔵 Asaas API Request: {method} {endpoint}")
            if data:
                print(f"📤 Payload: {data}")
            
            # Tenta parsear JSON mesmo em caso de erro
            try:
                response_json = response.json()
            except ValueError:
                response_json = {"error": response.text}
            
            # Log da resposta
            print(f"📥 Response Status: {response.status_code}")
            print(f"📥 Response Body: {response_json}")
            
            # Verifica se houve erro HTTP
            if response.status_code >= 400:
                error_message = self._parse_error(response_json, response.status_code)
                raise AsaasAPIError(error_message)
            
            return response_json
            
        except requests.exceptions.Timeout:
            raise AsaasAPIError("Timeout ao conectar com a API do Asaas. Tente novamente.")
        
        except requests.exceptions.ConnectionError:
            raise AsaasAPIError("Erro de conexão com a API do Asaas. Verifique sua internet.")
        
        except requests.exceptions.RequestException as e:
            raise AsaasAPIError(f"Erro na requisição: {str(e)}")
    
    def _parse_error(self, response_json: Dict[str, Any], status_code: int) -> str:
        """
        Extrai mensagem de erro amigável da resposta da API.
        
        Args:
            response_json: JSON de resposta com erro
            status_code: Código HTTP do erro
        
        Returns:
            Mensagem de erro formatada
        """
        # Formato padrão de erro do Asaas
        if 'errors' in response_json and isinstance(response_json['errors'], list):
            errors = [err.get('description', err.get('code', 'Erro desconhecido')) 
                     for err in response_json['errors']]
            return f"Erro {status_code}: {', '.join(errors)}"
        
        # Mensagem direta
        if 'error' in response_json:
            return f"Erro {status_code}: {response_json['error']}"
        
        # Fallback genérico
        return f"Erro {status_code} na API do Asaas. Verifique os logs."
    
    def create_customer(self, user: User) -> str:
        """
        Cria ou recupera um cliente no Asaas.
        
        Se o usuário já tiver um asaas_customer_id salvo, apenas retorna ele.
        Caso contrário, cria um novo cliente na API e salva o ID no banco.
        
        Args:
            user: Objeto User do banco de dados
        
        Returns:
            ID do cliente no Asaas (ex: 'cus_000005494119')
        
        Raises:
            AsaasAPIError: Se falhar ao criar cliente
        
        Exemplo:
            customer_id = service.create_customer(user)
            print(f"Cliente Asaas: {customer_id}")
        """
        # Verifica se já existe customer_id salvo
        if user.asaas_customer_id:
            print(f"✅ Cliente Asaas já existe: {user.asaas_customer_id}")
            return user.asaas_customer_id
        
        # Prepara dados do cliente
        customer_data = {
            'name': user.company_name or user.email.split('@')[0],
            'email': user.email,
        }
        
        # Adiciona CPF/CNPJ se disponível
        if user.cpf_cnpj:
            customer_data['cpfCnpj'] = user.cpf_cnpj
        
        # Cria cliente na API
        print(f"📝 Criando novo cliente Asaas para {user.email}...")
        response = self._make_request('POST', '/customers', customer_data)
        
        customer_id = response.get('id')
        
        if not customer_id:
            raise AsaasAPIError("API não retornou ID do cliente criado.")
        
        # Salva customer_id no banco de dados
        user.asaas_customer_id = customer_id
        self.db.commit()
        
        print(f"✅ Cliente criado com sucesso: {customer_id}")
        return customer_id
    
    def create_subscription(
        self,
        user: User,
        plan_type: str,
        billing_type: str = 'UNDEFINED'
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Cria uma assinatura recorrente no Asaas.
        
        Fluxo:
        1. Valida o plano solicitado
        2. Cria/recupera o cliente Asaas
        3. Cria assinatura com cobrança recorrente
        4. Retorna dados para exibir no frontend
        
        Args:
            user: Objeto User do banco de dados
            plan_type: Tipo do plano ('pro' ou 'agency')
            billing_type: Forma de pagamento ('BOLETO', 'PIX', 'CREDIT_CARD', 'UNDEFINED')
        
        Returns:
            Tupla (sucesso, dados_assinatura, mensagem_erro)
        
        Raises:
            AsaasAPIError: Se falhar ao criar assinatura
        
        Exemplo:
            success, subscription, error = service.create_subscription(user, 'pro', 'PIX')
            if success:
                print(f"Link de pagamento: {subscription['invoiceUrl']}")
            else:
                print(f"Erro: {error}")
        """
        # Validação do plano
        if plan_type not in ['pro', 'agency']:
            return False, None, "Plano inválido. Use 'pro' ou 'agency'."
        
        # Validação do billing_type
        valid_billing_types = ['BOLETO', 'PIX', 'CREDIT_CARD', 'UNDEFINED']
        if billing_type not in valid_billing_types:
            return False, None, f"Tipo de pagamento inválido. Use: {', '.join(valid_billing_types)}"
        
        try:
            # Passo 1: Garante que o cliente existe no Asaas
            customer_id = self.create_customer(user)
            
            # Passo 2: Define valor do plano
            value = self.PLAN_PRICES[plan_type]
            
            if value == 0:
                return False, None, "Plano gratuito não requer assinatura."
            
            # Passo 3: Define primeira cobrança (hoje)
            next_due_date = datetime.now().strftime('%Y-%m-%d')
            
            # Passo 4: Prepara dados da assinatura
            subscription_data = {
                'customer': customer_id,
                'billingType': billing_type,
                'value': value,
                'nextDueDate': next_due_date,
                'cycle': 'MONTHLY',
                'description': f'Plano {plan_type.capitalize()} - SentinelWeb',
            }
            
            # Passo 5: Cria assinatura na API
            print(f"💳 Criando assinatura {plan_type} para {user.email}...")
            response = self._make_request('POST', '/subscriptions', subscription_data)
            
            subscription_id = response.get('id')
            
            if not subscription_id:
                return False, None, "API não retornou ID da assinatura."
            
            print(f"✅ Assinatura criada: {subscription_id}")
            
            # Passo 6: Retorna dados completos
            return True, {
                'subscription_id': subscription_id,
                'customer_id': customer_id,
                'value': value,
                'plan': plan_type,
                'billing_type': billing_type,
                'next_due_date': next_due_date,
                'status': response.get('status'),
                'invoice_url': response.get('invoiceUrl'),  # Link de pagamento
                'response': response  # Resposta completa da API
            }, None
            
        except AsaasAPIError as e:
            print(f"❌ Erro ao criar assinatura: {e}")
            return False, None, str(e)
        
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return False, None, f"Erro interno: {str(e)}"
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera detalhes de uma assinatura existente.
        
        Args:
            subscription_id: ID da assinatura no Asaas
        
        Returns:
            Dados da assinatura ou None se não encontrada
        """
        try:
            response = self._make_request('GET', f'/subscriptions/{subscription_id}')
            return response
        except AsaasAPIError:
            return None
    
    def cancel_subscription(self, subscription_id: str) -> Tuple[bool, Optional[str]]:
        """
        Cancela uma assinatura ativa.
        
        Args:
            subscription_id: ID da assinatura no Asaas
        
        Returns:
            Tupla (sucesso, mensagem_erro)
        """
        try:
            response = self._make_request('DELETE', f'/subscriptions/{subscription_id}')
            print(f"✅ Assinatura cancelada: {subscription_id}")
            return True, None
        except AsaasAPIError as e:
            print(f"❌ Erro ao cancelar assinatura: {e}")
            return False, str(e)
    
    # ============================================
    # SUBSCRIPTION MANAGEMENT METHODS
    # ============================================
    
    def get_subscription_payments(self, customer_id: str) -> list:
        """
        Busca todas as cobranças (faturas) de um cliente no Asaas.
        
        Args:
            customer_id: ID do cliente no Asaas
        
        Returns:
            Lista de dicionários com informações das faturas:
            [
                {
                    'id': 'pay_123',
                    'value': 49.90,
                    'due_date': '2026-02-08',
                    'status': 'PENDING',
                    'invoice_url': 'https://...',
                    'billing_type': 'CREDIT_CARD',
                    'description': 'Plano Pro - Mensalidade'
                }
            ]
        
        Raises:
            AsaasAPIError: Se a requisição falhar
        """
        endpoint = f"/payments?customer={customer_id}"
        
        try:
            response = self._make_request('GET', endpoint)
            
            # A API retorna {"data": [...], "hasMore": false}
            payments_data = response.get('data', [])
            
            # Simplifica os dados para o frontend
            simplified_payments = []
            
            for payment in payments_data:
                simplified_payments.append({
                    'id': payment.get('id'),
                    'value': payment.get('value', 0.0),
                    'due_date': payment.get('dueDate'),
                    'status': payment.get('status'),
                    'invoice_url': payment.get('invoiceUrl') or payment.get('bankSlipUrl'),
                    'billing_type': payment.get('billingType'),
                    'description': payment.get('description', 'Cobrança'),
                    'confirmed_date': payment.get('confirmedDate'),
                    'payment_date': payment.get('paymentDate'),
                    'installment_number': payment.get('installmentNumber'),
                    'installment_count': payment.get('installmentCount')
                })
            
            # Ordena por data de vencimento (mais recente primeiro)
            simplified_payments.sort(
                key=lambda x: x['due_date'] if x['due_date'] else '',
                reverse=True
            )
            
            print(f"✅ Encontradas {len(simplified_payments)} cobranças para o cliente {customer_id}")
            return simplified_payments
            
        except Exception as e:
            print(f"❌ Erro ao buscar cobranças: {str(e)}")
            # Retorna lista vazia ao invés de falhar
            return []
    
    def get_subscription_details(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca detalhes de uma assinatura específica no Asaas.
        
        Args:
            subscription_id: ID da assinatura no Asaas
        
        Returns:
            Dicionário com detalhes da assinatura:
            {
                'id': 'sub_123',
                'status': 'ACTIVE',
                'value': 49.90,
                'cycle': 'MONTHLY',
                'next_due_date': '2026-02-08',
                'customer_name': 'João Silva',
                'description': 'Plano Pro'
            }
            
            Retorna None se não encontrar
        
        Raises:
            AsaasAPIError: Se a requisição falhar
        """
        endpoint = f"/subscriptions/{subscription_id}"
        
        try:
            response = self._make_request('GET', endpoint)
            
            # Simplifica os dados
            subscription = {
                'id': response.get('id'),
                'status': response.get('status'),
                'value': response.get('value', 0.0),
                'cycle': response.get('cycle'),
                'next_due_date': response.get('nextDueDate'),
                'customer_name': response.get('customer', {}).get('name'),
                'description': response.get('description', ''),
                'billing_type': response.get('billingType'),
                'created_at': response.get('dateCreated')
            }
            
            print(f"✅ Detalhes da assinatura {subscription_id} recuperados")
            return subscription
            
        except Exception as e:
            print(f"❌ Erro ao buscar detalhes da assinatura: {str(e)}")
            return None
    
    def get_customer_subscriptions(self, customer_id: str) -> list:
        """
        Busca todas as assinaturas ativas de um cliente.
        
        Args:
            customer_id: ID do cliente no Asaas
        
        Returns:
            Lista de assinaturas do cliente
        """
        endpoint = f"/subscriptions?customer={customer_id}&status=ACTIVE"
        
        try:
            response = self._make_request('GET', endpoint)
            subscriptions = response.get('data', [])
            
            print(f"✅ Encontradas {len(subscriptions)} assinaturas ativas")
            return subscriptions
            
        except Exception as e:
            print(f"❌ Erro ao buscar assinaturas: {str(e)}")
            return []


# ============================================
# EXEMPLO DE USO EM ROTA
# ============================================

def example_usage():
    """
    Exemplo de como usar o AsaasService em uma rota FastAPI.
    
    Este código demonstra o fluxo completo:
    1. Inicializar o serviço
    2. Criar um cliente
    3. Criar uma assinatura
    4. Exibir link de pagamento
    """
    from fastapi import APIRouter, Depends, HTTPException
    from sqlalchemy.orm import Session
    from database import get_db
    from auth import get_current_user
    from models import User
    
    router = APIRouter()
    
    @router.post("/test/asaas/create-subscription")
    async def test_create_subscription(
        plan: str,  # 'pro' ou 'agency'
        billing_type: str = 'PIX',  # 'PIX', 'BOLETO', 'CREDIT_CARD'
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        """
        Rota de teste para criar assinatura no Asaas.
        
        Exemplo de request:
        POST /test/asaas/create-subscription?plan=pro&billing_type=PIX
        """
        try:
            # Inicializa o serviço
            asaas_service = AsaasService(db)
            
            # Cria assinatura
            success, subscription_data, error = asaas_service.create_subscription(
                user=user,
                plan_type=plan,
                billing_type=billing_type
            )
            
            if not success:
                raise HTTPException(status_code=400, detail=error)
            
            # Retorna dados para o frontend
            return {
                "message": "Assinatura criada com sucesso!",
                "subscription": subscription_data,
                "payment_url": subscription_data['invoice_url'],
                "instructions": f"Acesse o link acima para pagar via {billing_type}"
            }
            
        except AsaasAPIError as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
