"""
Plan Limits - Limites e Restrições por Plano
=============================================
Define os limites de cada plano e funções de validação.
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
from models import User, Site

# ============================================
# LIMITES POR PLANO
# ============================================

PLAN_LIMITS = {
    'free': {
        'max_sites': 1,
        'check_interval_min': 10,  # minutos
        'features': ['basic_monitoring', 'ssl_check'],
        'name': 'Plano Free',
        'description': 'Teste o sistema com 1 site'
    },
    'pro': {
        'max_sites': 20,
        'check_interval_min': 1,  # minutos
        'features': ['basic_monitoring', 'ssl_check', 'telegram_alerts', 'heartbeat', 'tech_scanner'],
        'name': 'Plano Pro',
        'description': 'Para profissionais com até 20 sites'
    },
    'agency': {
        'max_sites': 100,
        'check_interval_min': 0.5,  # minutos (30 segundos)
        'features': ['basic_monitoring', 'ssl_check', 'telegram_alerts', 'heartbeat', 'tech_scanner', 'visual_regression', 'pagespeed'],
        'name': 'Plano Agency',
        'description': 'Para agências com até 100 sites'
    }
}


# ============================================
# FUNÇÕES DE VALIDAÇÃO
# ============================================

def get_plan_limits(plan_status: str) -> Dict:
    """
    Retorna os limites de um plano.
    
    Args:
        plan_status: 'free', 'pro' ou 'agency'
    
    Returns:
        Dict com os limites do plano
    """
    return PLAN_LIMITS.get(plan_status, PLAN_LIMITS['free'])


def can_add_site(user: User, db: Session) -> tuple[bool, Optional[str]]:
    """
    Verifica se o usuário pode adicionar mais um site.
    
    Args:
        user: Usuário que quer adicionar o site
        db: Sessão do banco de dados
    
    Returns:
        Tupla (pode_adicionar, mensagem_erro)
    """
    # Conta sites atuais do usuário
    current_sites = db.query(Site).filter(Site.owner_id == user.id).count()
    
    # Pega limites do plano
    limits = get_plan_limits(user.plan_status)
    max_sites = limits['max_sites']
    
    # Verifica se pode adicionar
    if current_sites >= max_sites:
        plan_name = limits['name']
        
        if user.plan_status == 'free':
            error_msg = (
                f"❌ Você atingiu o limite do {plan_name} (1 site). "
                f"<br><br>🚀 <strong>Faça upgrade para monitorar mais sites:</strong>"
                f"<br>• <strong>Pro:</strong> Até 20 sites por R$ 49/mês"
                f"<br>• <strong>Agency:</strong> Até 100 sites por R$ 149/mês"
                f"<br><br>Entre em contato com o suporte para fazer upgrade."
            )
        elif user.plan_status == 'pro':
            error_msg = (
                f"❌ Você atingiu o limite do {plan_name} ({max_sites} sites). "
                f"<br><br>🚀 <strong>Faça upgrade para o Plano Agency:</strong>"
                f"<br>• Até 100 sites por R$ 149/mês"
                f"<br><br>Entre em contato com o suporte para fazer upgrade."
            )
        else:  # agency
            error_msg = (
                f"❌ Você atingiu o limite do {plan_name} ({max_sites} sites). "
                f"<br><br>Entre em contato com o suporte para planos personalizados."
            )
        
        return False, error_msg
    
    return True, None


def validate_check_interval(user: User, check_interval: int) -> tuple[bool, Optional[str]]:
    """
    Valida se o intervalo de check está dentro do permitido para o plano.
    
    Args:
        user: Usuário
        check_interval: Intervalo em minutos
    
    Returns:
        Tupla (é_válido, mensagem_erro)
    """
    limits = get_plan_limits(user.plan_status)
    min_interval = limits['check_interval_min']
    
    if check_interval < min_interval:
        plan_name = limits['name']
        error_msg = (
            f"❌ O intervalo mínimo para o {plan_name} é de {min_interval} minuto(s). "
            f"Faça upgrade para intervalos menores."
        )
        return False, error_msg
    
    return True, None


def has_feature(user: User, feature: str) -> bool:
    """
    Verifica se o usuário tem acesso a uma feature específica.
    
    Args:
        user: Usuário
        feature: Nome da feature ('telegram_alerts', 'heartbeat', etc)
    
    Returns:
        True se tem acesso, False caso contrário
    """
    limits = get_plan_limits(user.plan_status)
    return feature in limits['features']


def get_plan_comparison() -> Dict:
    """
    Retorna comparação de todos os planos para exibição.
    
    Returns:
        Dict com informações de todos os planos
    """
    return {
        'free': {
            **PLAN_LIMITS['free'],
            'price': 0,
            'price_text': 'Grátis'
        },
        'pro': {
            **PLAN_LIMITS['pro'],
            'price': 49,
            'price_text': 'R$ 49/mês'
        },
        'agency': {
            **PLAN_LIMITS['agency'],
            'price': 149,
            'price_text': 'R$ 149/mês'
        }
    }


def get_usage_stats(user: User, db: Session) -> Dict:
    """
    Retorna estatísticas de uso do usuário em relação ao plano.
    
    Args:
        user: Usuário
        db: Sessão do banco de dados
    
    Returns:
        Dict com estatísticas de uso
    """
    limits = get_plan_limits(user.plan_status)
    current_sites = db.query(Site).filter(Site.owner_id == user.id).count()
    max_sites = limits['max_sites']
    
    return {
        'plan': user.plan_status,
        'plan_name': limits['name'],
        'current_sites': current_sites,
        'max_sites': max_sites,
        'sites_percentage': round((current_sites / max_sites * 100) if max_sites > 0 else 0, 1),
        'can_add_more': current_sites < max_sites,
        'sites_remaining': max_sites - current_sites
    }
