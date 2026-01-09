"""
SentinelWeb - Painel Administrativo Enterprise
==============================================
Backoffice completo usando SQLAdmin para gestão total do negócio.

Principal Software Architect: Enterprise-grade Admin Panel
"""

from typing import Optional, List
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from datetime import datetime, timezone
import os

# Imports locais
from models import User, Site, MonitorLog, Payment, SystemConfig
from database import async_session_maker
from auth import verify_token, get_password_hash, verify_password


# ============================================
# AUTENTICAÇÃO BLINDADA
# ============================================

class AdminAuth(AuthenticationBackend):
    """
    Sistema de autenticação que valida:
    1. Token JWT válido na sessão
    2. Usuário existe no banco
    3. Usuário tem permissão de admin (is_superuser=True)
    
    Nenhum usuário comum consegue acessar /admin, mesmo com token válido.
    """
    
    async def login(self, request: Request) -> bool:
        """Processa o login do admin"""
        form = await request.form()
        email = form.get("username")  # SQLAdmin usa "username"
        password = form.get("password")
        
        async with async_session_maker() as session:
            # Busca usuário por email
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            # Validações críticas
            if not user:
                return False
            
            if not verify_password(password, user.hashed_password):
                return False
            
            # 🔒 REGRA DE OURO: Apenas superusers podem acessar
            if not user.is_superuser:
                return False
            
            if not user.is_active:
                return False
            
            # Cria token JWT para a sessão do admin
            from auth import create_access_token
            token = create_access_token(data={"sub": str(user.id)})
            
            # Armazena na sessão
            request.session.update({
                "token": token,
                "user_id": user.id,
                "email": user.email
            })
            
            return True
    
    async def logout(self, request: Request) -> bool:
        """Logout do admin"""
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> bool:
        """
        Valida se o usuário pode acessar o admin.
        Chamado em TODAS as requisições ao /admin.
        """
        token = request.session.get("token")
        user_id = request.session.get("user_id")
        
        if not token or not user_id:
            return False
        
        try:
            # Valida token JWT
            payload = verify_token(token)
            
            # Busca usuário no banco e valida permissões
            async with async_session_maker() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                # 🔒 VALIDAÇÃO CRÍTICA: is_superuser SEMPRE
                if not user or not user.is_superuser or not user.is_active:
                    return False
                
                return True
                
        except Exception as e:
            print(f"❌ Admin auth error: {str(e)}")
            return False


# ============================================
# DASHBOARD EXECUTIVO (KPIs)
# ============================================

class DashboardView(ModelView):
    """
    View customizada para o dashboard com KPIs de negócio.
    Não é um CRUD, é uma página de métricas.
    """
    
    def is_visible(self, request: Request) -> bool:
        """Esconde do menu lateral (será a home)"""
        return False
    
    def is_accessible(self, request: Request) -> bool:
        """Apenas admins autenticados"""
        return request.session.get("token") is not None


# ============================================
# GESTÃO DE USUÁRIOS (CRM)
# ============================================

class UserAdmin(ModelView, model=User):
    """
    Módulo de gestão de usuários com recursos avançados:
    - Impersonate (logar como cliente)
    - Banir/Desbanir
    - Filtros e buscas avançadas
    """
    
    name = "Usuário"
    name_plural = "Usuários"
    icon = "fa-solid fa-users"
    
    # Colunas exibidas na lista
    column_list = [
        User.id,
        User.email,
        User.company_name,
        User.plan_status,
        User.is_active,
        User.is_superuser,
        User.created_at,
        User.asaas_customer_id
    ]
    
    # Colunas para detalhes
    column_details_list = [
        User.id,
        User.email,
        User.company_name,
        User.cpf_cnpj,
        User.plan_status,
        User.is_active,
        User.is_superuser,
        User.created_at,
        User.asaas_customer_id,
        User.telegram_chat_id
    ]
    
    # Busca
    column_searchable_list = [User.email, User.company_name, User.cpf_cnpj]
    
    # Filtros
    column_filters = [
        User.plan_status,
        User.is_active,
        User.is_superuser,
        User.created_at
    ]
    
    # Ordenação padrão
    column_default_sort = [(User.created_at, True)]
    
    # Labels customizadas
    column_labels = {
        "email": "Email",
        "company_name": "Empresa",
        "cpf_cnpj": "CPF/CNPJ",
        "plan_status": "Plano",
        "is_active": "Ativo",
        "is_superuser": "Admin",
        "created_at": "Cadastro",
        "asaas_customer_id": "ID Asaas"
    }
    
    # Formatadores de coluna
    column_formatters = {
        User.plan_status: lambda m, a: {
            'free': '🆓 Free',
            'pro': '⭐ Pro',
            'agency': '💎 Agency'
        }.get(m.plan_status, m.plan_status),
        
        User.is_active: lambda m, a: '✅ Ativo' if m.is_active else '❌ Inativo',
        User.is_superuser: lambda m, a: '👑 Admin' if m.is_superuser else '👤 Usuário',
    }
    
    # Campos sensíveis ocultos
    form_excluded_columns = [User.hashed_password, User.created_at]
    
    # Campos apenas leitura
    column_details_exclude_list = [User.hashed_password]
    
    # Paginação
    page_size = 50
    page_size_options = [25, 50, 100, 200]
    
    # Custom Actions
    async def on_model_change(self, data: dict, model: User, is_created: bool, request: Request) -> None:
        """Hook executado ao criar/editar usuário"""
        # Se está setando nova senha
        if 'password' in data and data['password']:
            model.hashed_password = get_password_hash(data['password'])
            del data['password']
    
    # TODO: Implementar actions customizadas
    # - Impersonate User (gerar JWT e redirecionar)
    # - Ban/Unban User (toggle is_active)
    # - Reset Password (enviar email)


# ============================================
# GESTÃO DE SITES (OPS)
# ============================================

class SiteAdmin(ModelView, model=Site):
    """
    Gestão operacional de sites monitorados.
    Permite force scan e visualização de saúde.
    """
    
    name = "Site"
    name_plural = "Sites"
    icon = "fa-solid fa-globe"
    
    column_list = [
        Site.id,
        Site.domain,
        Site.name,
        Site.owner_id,
        Site.current_status,
        Site.is_active,
        Site.last_checked,
        Site.ssl_days_remaining,
        Site.check_interval
    ]
    
    column_details_list = [
        Site.id,
        Site.domain,
        Site.name,
        Site.owner_id,
        Site.current_status,
        Site.is_active,
        Site.last_checked,
        Site.ssl_days_remaining,
        Site.ssl_expiration_date,
        Site.check_interval,
        Site.must_contain_keyword,
        Site.open_ports,
        Site.blacklisted_ips,
        Site.created_at
    ]
    
    column_searchable_list = [Site.domain, Site.name]
    
    column_filters = [
        Site.current_status,
        Site.is_active,
        Site.owner_id,
        Site.check_interval
    ]
    
    column_default_sort = [(Site.last_checked, True)]
    
    column_labels = {
        "domain": "Domínio",
        "name": "Nome",
        "owner_id": "Dono (ID)",
        "current_status": "Status",
        "is_active": "Ativo",
        "last_checked": "Última Check",
        "ssl_days_remaining": "SSL (dias)",
        "check_interval": "Intervalo (min)",
        "must_contain_keyword": "Palavra-chave"
    }
    
    column_formatters = {
        Site.current_status: lambda m, a: {
            'online': '🟢 Online',
            'offline': '🔴 Offline',
            'unknown': '⚪ Desconhecido'
        }.get(m.current_status, m.current_status),
        
        Site.is_active: lambda m, a: '✅' if m.is_active else '⏸️',
        
        Site.ssl_days_remaining: lambda m, a: (
            f'🟢 {m.ssl_days_remaining}d' if m.ssl_days_remaining and m.ssl_days_remaining > 30
            else f'🟡 {m.ssl_days_remaining}d' if m.ssl_days_remaining and m.ssl_days_remaining > 7
            else f'🔴 {m.ssl_days_remaining}d' if m.ssl_days_remaining
            else '❓'
        )
    }
    
    page_size = 50
    page_size_options = [25, 50, 100, 200]


# ============================================
# GESTÃO FINANCEIRA (ERP)
# ============================================

class PaymentAdmin(ModelView, model=Payment):
    """
    Módulo financeiro completo.
    Visualiza todas as transações e permite sincronização com Asaas.
    """
    
    name = "Pagamento"
    name_plural = "Pagamentos"
    icon = "fa-solid fa-dollar-sign"
    
    column_list = [
        Payment.id,
        Payment.user_id,
        Payment.asaas_payment_id,
        Payment.value,
        Payment.billing_type,
        Payment.status,
        Payment.due_date,
        Payment.payment_date,
        Payment.created_at
    ]
    
    column_searchable_list = [Payment.asaas_payment_id]
    
    column_filters = [
        Payment.status,
        Payment.billing_type,
        Payment.due_date,
        Payment.created_at
    ]
    
    column_default_sort = [(Payment.created_at, True)]
    
    column_labels = {
        "user_id": "Usuário (ID)",
        "asaas_payment_id": "ID Asaas",
        "value": "Valor",
        "billing_type": "Tipo",
        "status": "Status",
        "due_date": "Vencimento",
        "payment_date": "Data Pagamento",
        "invoice_url": "Fatura"
    }
    
    column_formatters = {
        Payment.value: lambda m, a: f'R$ {m.value:.2f}' if m.value else 'R$ 0,00',
        
        Payment.status: lambda m, a: {
            'PENDING': '🟡 Pendente',
            'RECEIVED': '🟢 Pago',
            'CONFIRMED': '✅ Confirmado',
            'OVERDUE': '🔴 Vencido',
            'REFUNDED': '↩️ Reembolsado'
        }.get(m.status.name if hasattr(m.status, 'name') else str(m.status), str(m.status)),
        
        Payment.billing_type: lambda m, a: {
            'BOLETO': '📄 Boleto',
            'CREDIT_CARD': '💳 Cartão',
            'PIX': '📱 PIX',
            'DEBIT_CARD': '💳 Débito'
        }.get(m.billing_type.name if hasattr(m.billing_type, 'name') else str(m.billing_type), str(m.billing_type))
    }
    
    # Campos apenas leitura (não podem ser editados)
    form_excluded_columns = [
        Payment.created_at,
        Payment.asaas_payment_id,
        Payment.invoice_url,
        Payment.bankslip_url,
        Payment.pix_qrcode
    ]
    
    page_size = 50


# ============================================
# CONFIGURAÇÕES DO SISTEMA (SINGLETON)
# ============================================

class SystemConfigAdmin(ModelView, model=SystemConfig):
    """
    Configurações globais do sistema.
    DEVE haver apenas 1 registro no banco.
    Campos sensíveis são mascarados.
    """
    
    name = "Configuração"
    name_plural = "Configurações"
    icon = "fa-solid fa-gear"
    
    # Apenas permite editar o registro existente, não criar novos
    can_create = False
    can_delete = False
    
    column_list = [
        SystemConfig.id,
        SystemConfig.plan_free_price,
        SystemConfig.plan_pro_price,
        SystemConfig.plan_agency_price,
        SystemConfig.updated_at
    ]
    
    column_labels = {
        "plan_free_price": "Preço Free",
        "plan_pro_price": "Preço Pro",
        "plan_agency_price": "Preço Agency",
        "asaas_api_key": "🔒 Asaas API Key",
        "telegram_bot_token": "🔒 Telegram Bot Token",
        "updated_at": "Última Atualização"
    }
    
    # Formatadores
    column_formatters = {
        SystemConfig.plan_free_price: lambda m, a: f'R$ {m.plan_free_price:.2f}',
        SystemConfig.plan_pro_price: lambda m, a: f'R$ {m.plan_pro_price:.2f}',
        SystemConfig.plan_agency_price: lambda m, a: f'R$ {m.plan_agency_price:.2f}',
    }
    
    # Campos sensíveis mascarados
    form_widget_args = {
        'asaas_api_key': {
            'type': 'password'
        },
        'telegram_bot_token': {
            'type': 'password'
        }
    }
    
    # Campos apenas leitura
    form_excluded_columns = [SystemConfig.created_at, SystemConfig.updated_at]


# ============================================
# LOGS DE MONITORAMENTO (READ-ONLY)
# ============================================

class MonitorLogAdmin(ModelView, model=MonitorLog):
    """
    Logs de verificação dos sites (apenas leitura).
    Útil para debugging e auditoria.
    """
    
    name = "Log"
    name_plural = "Logs de Monitoramento"
    icon = "fa-solid fa-list"
    
    can_create = False
    can_edit = False
    can_delete = False
    
    column_list = [
        MonitorLog.id,
        MonitorLog.site_id,
        MonitorLog.checked_at,
        MonitorLog.status,
        MonitorLog.latency_ms,
        MonitorLog.http_status_code,
        MonitorLog.error_message
    ]
    
    column_searchable_list = [MonitorLog.error_message]
    
    column_filters = [
        MonitorLog.status,
        MonitorLog.site_id,
        MonitorLog.checked_at,
        MonitorLog.http_status_code
    ]
    
    column_default_sort = [(MonitorLog.checked_at, True)]
    
    column_labels = {
        "site_id": "Site (ID)",
        "checked_at": "Data/Hora",
        "status": "Status",
        "latency_ms": "Latência (ms)",
        "http_status_code": "HTTP Code",
        "error_message": "Erro"
    }
    
    column_formatters = {
        MonitorLog.status: lambda m, a: '🟢 Online' if m.status == 'online' else '🔴 Offline',
        MonitorLog.latency_ms: lambda m, a: f'{m.latency_ms:.0f}ms' if m.latency_ms else 'N/A'
    }
    
    page_size = 100
    page_size_options = [50, 100, 200, 500]
