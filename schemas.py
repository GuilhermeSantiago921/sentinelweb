"""
SentinelWeb - Schemas Pydantic
==============================
Validação de dados de entrada e saída da API.
Separa a lógica de validação dos modelos do banco.
"""

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
import re


# ============================================
# SCHEMAS DE USUÁRIO
# ============================================

class UserBase(BaseModel):
    """Schema base para usuário"""
    email: EmailStr
    company_name: Optional[str] = None
    telegram_chat_id: Optional[str] = None


class UserCreate(UserBase):
    """Schema para criação de usuário"""
    password: str
    password_confirm: str
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        """Valida força mínima da senha"""
        if len(v) < 6:
            raise ValueError('Senha deve ter no mínimo 6 caracteres')
        return v
    
    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v, info):
        """Valida se as senhas coincidem"""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('As senhas não coincidem')
        return v


class UserLogin(BaseModel):
    """Schema para login"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema para atualização de perfil do usuário"""
    company_name: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    cpf_cnpj: Optional[str] = None


class UserResponse(UserBase):
    """Schema de resposta do usuário (sem senha)"""
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# SCHEMAS DE SITE
# ============================================

class SiteBase(BaseModel):
    """Schema base para site"""
    domain: str
    name: Optional[str] = None
    check_interval: Optional[int] = 5
    must_contain_keyword: Optional[str] = None  # Palavra-chave para verificação anti-defacement
    
    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v):
        """
        Valida e limpa o domínio.
        Remove protocolos e barras finais.
        """
        # Remove protocolo se presente
        v = re.sub(r'^https?://', '', v)
        # Remove barra final
        v = v.rstrip('/')
        # Remove www. opcional para padronização
        # v = re.sub(r'^www\.', '', v)
        
        # Validação básica de formato de domínio
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
        if not re.match(domain_pattern, v.replace('www.', '')):
            raise ValueError('Formato de domínio inválido')
        
        return v
    
    @field_validator('check_interval')
    @classmethod
    def validate_interval(cls, v):
        """Intervalo mínimo de 1 minuto, máximo de 60"""
        if v < 1:
            return 1
        if v > 60:
            return 60
        return v


class SiteCreate(SiteBase):
    """Schema para criação de site"""
    pass


class SiteUpdate(BaseModel):
    """Schema para atualização de site"""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    check_interval: Optional[int] = None
    must_contain_keyword: Optional[str] = None


class SiteResponse(SiteBase):
    """Schema de resposta do site"""
    id: int
    is_active: bool
    current_status: str
    last_check: Optional[datetime] = None
    last_latency: Optional[float] = None
    ssl_days_remaining: Optional[int] = None
    ssl_valid: Optional[bool] = None
    domain_expiration_date: Optional[datetime] = None
    open_ports: Optional[str] = None
    must_contain_keyword: Optional[str] = None
    is_blacklisted: Optional[bool] = False
    blacklisted_in: Optional[str] = None
    is_wordpress: Optional[bool] = False
    wp_version: Optional[str] = None
    vulnerabilities_found: Optional[str] = None
    performance_score: Optional[int] = None
    seo_score: Optional[int] = None
    accessibility_score: Optional[int] = None
    best_practices_score: Optional[int] = None
    last_pagespeed_check: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# SCHEMAS DE MONITOR LOG
# ============================================

class MonitorLogResponse(BaseModel):
    """Schema de resposta do log de monitoramento"""
    id: int
    site_id: int
    status: str
    http_status_code: Optional[int] = None
    latency_ms: Optional[float] = None
    ssl_valid: Optional[bool] = None
    ssl_days_remaining: Optional[int] = None
    open_ports: Optional[str] = None
    error_message: Optional[str] = None
    checked_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# SCHEMAS DE RESPOSTA GERAL
# ============================================

class MessageResponse(BaseModel):
    """Schema para mensagens simples"""
    message: str
    success: bool = True


class DashboardStats(BaseModel):
    """Schema para estatísticas do dashboard"""
    total_sites: int
    sites_online: int
    sites_offline: int
    sites_unknown: int
    ssl_expiring_soon: int  # Sites com SSL expirando em < 30 dias
    sites_with_open_ports: int
