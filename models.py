"""
SentinelWeb - Modelos do Banco de Dados (ORM)
=============================================
Define as tabelas: User, Site e MonitorLog
Usando SQLAlchemy ORM para abstração do banco.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, 
    ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import datetime, timezone, timedelta


class SiteStatus(enum.Enum):
    """Enum para status do site"""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class HeartbeatStatus(enum.Enum):
    """Enum para status do heartbeat"""
    NEW = "new"      # Nunca recebeu ping
    UP = "up"        # Recebendo pings normalmente
    LATE = "late"    # Passou do período esperado mas ainda dentro da tolerância
    DOWN = "down"    # Passou do período + tolerância


class PaymentStatus(enum.Enum):
    """Enum para status do pagamento"""
    PENDING = "pending"           # Aguardando pagamento
    RECEIVED = "received"         # Pagamento recebido
    CONFIRMED = "confirmed"       # Pagamento confirmado
    OVERDUE = "overdue"          # Vencido
    REFUNDED = "refunded"        # Estornado
    REFUND_REQUESTED = "refund_requested"  # Estorno solicitado
    CHARGEBACK_REQUESTED = "chargeback_requested"  # Chargeback solicitado
    CHARGEBACK_DISPUTE = "chargeback_dispute"  # Disputa de chargeback
    AWAITING_CHARGEBACK_REVERSAL = "awaiting_chargeback_reversal"  # Aguardando reversão de chargeback
    DUNNING_REQUESTED = "dunning_requested"  # Cobrança solicitada
    DUNNING_RECEIVED = "dunning_received"  # Cobrança recebida
    AWAITING_RISK_ANALYSIS = "awaiting_risk_analysis"  # Aguardando análise de risco


class BillingType(enum.Enum):
    """Enum para tipo de cobrança"""
    BOLETO = "BOLETO"
    CREDIT_CARD = "CREDIT_CARD"
    PIX = "PIX"
    UNDEFINED = "UNDEFINED"
    TRANSFER = "TRANSFER"
    DEPOSIT = "DEPOSIT"


class User(Base):
    """
    Tabela de Usuários (Agências)
    Cada usuário pode ter múltiplos sites para monitorar.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)  # Nome da Agência
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False, nullable=False)  # Admin do sistema
    plan_status = Column(String(20), default='free', nullable=False)  # 'free', 'pro', 'agency'
    telegram_chat_id = Column(String(255), nullable=True)  # ID do chat do Telegram para notificações
    asaas_customer_id = Column(String(255), nullable=True)  # ID do cliente no Asaas
    cpf_cnpj = Column(String(18), nullable=True)  # CPF (11 dígitos) ou CNPJ (14 dígitos) do usuário
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    sites = relationship("Site", back_populates="owner", cascade="all, delete-orphan")
    heartbeat_checks = relationship("HeartbeatCheck", back_populates="owner", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Site(Base):
    """
    Tabela de Sites Monitorados
    Armazena os domínios cadastrados por cada usuário.
    """
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False, index=True)  # ex: cliente.com.br
    name = Column(String(255), nullable=True)  # Nome amigável do site
    is_active = Column(Boolean, default=True)  # Monitoramento ativo?
    check_interval = Column(Integer, default=5)  # Intervalo em minutos
    
    # Status atual (atualizado pelo worker)
    current_status = Column(String(20), default="unknown")
    last_check = Column(DateTime(timezone=True), nullable=True)
    last_latency = Column(Float, nullable=True)  # Última latência em ms
    ssl_days_remaining = Column(Integer, nullable=True)  # Dias até expirar SSL
    ssl_valid = Column(Boolean, nullable=True)
    domain_expiration_date = Column(DateTime(timezone=True), nullable=True)  # Data de expiração do domínio (Whois)
    
    # Verificação de Defacement (Desfiguração)
    must_contain_keyword = Column(String(255), nullable=True)  # Palavra-chave que deve existir no HTML (anti-defacement)
    
    # Verificação de Blacklist (RBL)
    is_blacklisted = Column(Boolean, default=False, nullable=False)  # Se o IP está em alguma blacklist
    blacklisted_in = Column(Text, nullable=True)  # Lista de RBLs onde foi encontrado (JSON string)
    
    # WordPress Security Scan
    is_wordpress = Column(Boolean, default=False, nullable=False)  # Se o site é WordPress
    wp_version = Column(String(50), nullable=True)  # Versão do WordPress detectada
    vulnerabilities_found = Column(Text, nullable=True)  # JSON com lista de vulnerabilidades encontradas
    
    # Google PageSpeed Insights (Performance Audit)
    performance_score = Column(Integer, nullable=True)  # Score de Performance (0-100)
    seo_score = Column(Integer, nullable=True)  # Score de SEO (0-100)
    accessibility_score = Column(Integer, nullable=True)  # Score de Acessibilidade (0-100)
    best_practices_score = Column(Integer, nullable=True)  # Score de Melhores Práticas (0-100)
    last_pagespeed_check = Column(DateTime(timezone=True), nullable=True)  # Última verificação PageSpeed
    
    # Alertas de portas abertas (JSON string para simplicidade no MVP)
    open_ports = Column(Text, nullable=True)  # ex: "21,22,3306"
    
    # Visual Regression Testing
    last_screenshot_path = Column(String(500), nullable=True)  # Caminho do screenshot atual
    baseline_screenshot_path = Column(String(500), nullable=True)  # Imagem de referência (baseline)
    visual_diff_percent = Column(Float, nullable=True)  # Diferença visual em % (0.0 - 100.0)
    last_visual_check = Column(DateTime(timezone=True), nullable=True)  # Última verificação visual
    visual_alert_triggered = Column(Boolean, default=False)  # Se a última verificação gerou alerta (diff > 5%)
    plugins_detected = Column(Text, nullable=True)  # Plugins WordPress detectados (JSON)
    
    # SEO Health Check (Indexabilidade)
    seo_indexable = Column(Boolean, default=True, nullable=False)  # Se o site está indexável pelos motores de busca
    seo_issues = Column(Text, nullable=True)  # JSON com lista de problemas SEO encontrados (noindex, robots.txt, etc)
    last_seo_check = Column(DateTime(timezone=True), nullable=True)  # Última verificação de SEO
    
    # General Tech Stack & Security (para sites não-WordPress)
    tech_stack = Column(Text, nullable=True)  # JSON: {"Nginx": "1.18", "React": "16.8"}
    security_headers_grade = Column(String(1), nullable=True)  # 'A', 'B', 'C', 'F'
    general_vulnerabilities = Column(Text, nullable=True)  # JSON array de CVEs encontrados
    last_tech_scan = Column(DateTime(timezone=True), nullable=True)  # Última varredura de tecnologias
    
    # Foreign Key para o usuário dono
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    owner = relationship("User", back_populates="sites")
    logs = relationship("MonitorLog", back_populates="site", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Site(id={self.id}, domain={self.domain})>"


class MonitorLog(Base):
    """
    Tabela de Logs de Monitoramento
    Histórico de todas as verificações realizadas.
    Útil para relatórios e análise de tendências.
    """
    __tablename__ = "monitor_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    
    # Resultado da verificação
    status = Column(String(20), nullable=False)  # online/offline
    http_status_code = Column(Integer, nullable=True)  # 200, 404, 500, etc
    latency_ms = Column(Float, nullable=True)  # Tempo de resposta em ms
    
    # Informações SSL
    ssl_valid = Column(Boolean, nullable=True)
    ssl_days_remaining = Column(Integer, nullable=True)
    ssl_issuer = Column(String(255), nullable=True)
    
    # Portas abertas encontradas
    open_ports = Column(Text, nullable=True)
    
    # Mensagem de erro (se houver)
    error_message = Column(Text, nullable=True)
    
    # Timestamp da verificação
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacionamento
    site = relationship("Site", back_populates="logs")
    
    def __repr__(self):
        return f"<MonitorLog(site_id={self.site_id}, status={self.status}, checked_at={self.checked_at})>"


class HeartbeatCheck(Base):
    """
    Tabela de Heartbeat Checks (Monitoramento de Cron Jobs)
    
    Permite monitorar tarefas agendadas, backups e scripts.
    O script deve fazer ping periodicamente na URL gerada.
    Se o ping não ocorrer no período esperado, gera alerta.
    """
    __tablename__ = "heartbeat_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)  # URL única para ping
    name = Column(String(200), nullable=False)  # Nome da tarefa (ex: "Backup Diário")
    description = Column(Text, nullable=True)  # Descrição opcional
    
    # Configurações de timing (em segundos)
    expected_period = Column(Integer, nullable=False)  # Ex: 86400 para 1 dia
    grace_period = Column(Integer, default=3600)  # Tolerância (ex: 3600 = 1 hora)
    
    # Status e controle
    status = Column(String(20), default='new')  # 'new', 'up', 'late', 'down'
    last_ping = Column(DateTime(timezone=True), nullable=True)
    next_expected_ping = Column(DateTime(timezone=True), nullable=True)
    
    # Alertas
    alert_sent = Column(Boolean, default=False)
    alert_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Estatísticas
    total_pings = Column(Integer, default=0)
    missed_pings = Column(Integer, default=0)
    
    # Relacionamento
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="heartbeat_checks")
    
    # Controle
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<HeartbeatCheck(name='{self.name}', slug='{self.slug}', status='{self.status}')>"
    
    @property
    def ping_url(self):
        """Retorna a URL completa para ping"""
        return f"/ping/{self.slug}"
    
    @property
    def is_overdue(self):
        """Verifica se o heartbeat está atrasado"""
        if not self.last_ping or not self.is_active:
            return False
        
        now = datetime.now(timezone.utc)
        deadline = self.last_ping + timedelta(seconds=self.expected_period + self.grace_period)
        return now > deadline
    
    @property
    def time_until_next_ping(self):
        """Retorna segundos até o próximo ping esperado"""
        if not self.last_ping:
            return 0
        
        now = datetime.now(timezone.utc)
        next_ping = self.last_ping + timedelta(seconds=self.expected_period)
        delta = next_ping - now
        return max(0, int(delta.total_seconds()))
    
    @property
    def time_since_last_ping(self):
        """Retorna segundos desde o último ping"""
        if not self.last_ping:
            return None
        
        now = datetime.now(timezone.utc)
        delta = now - self.last_ping
        return int(delta.total_seconds())


class SystemConfig(Base):
    """
    Tabela de Configuração Global do Sistema (Singleton)
    
    Esta tabela deve ter APENAS UMA LINHA.
    Armazena configurações globais como chaves de API do Asaas.
    """
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Configurações do Asaas (Gateway de Pagamento)
    asaas_api_token = Column(Text, nullable=True)  # Token da API do Asaas
    asaas_webhook_secret = Column(String(255), nullable=True)  # Secret do webhook
    is_sandbox = Column(Boolean, default=True, nullable=False)  # Ambiente: True=Sandbox, False=Produção
    
    # Configurações de Planos (Preços em Reais)
    plan_free_price = Column(Float, default=0.0, nullable=False)
    plan_pro_price = Column(Float, default=49.0, nullable=False)
    plan_agency_price = Column(Float, default=149.0, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemConfig(id={self.id}, is_sandbox={self.is_sandbox})>"
    
    @property
    def asaas_base_url(self):
        """Retorna a URL base da API do Asaas"""
        if self.is_sandbox:
            return "https://sandbox.asaas.com/api/v3"
        return "https://api.asaas.com/v3"
    
    @property
    def is_configured(self):
        """Verifica se o Asaas está configurado"""
        return bool(self.asaas_api_token)


class Payment(Base):
    """
    Tabela de Pagamentos (Cobranças Asaas)
    
    Registra todas as cobranças geradas para os usuários.
    Sincroniza com a API do Asaas via webhooks.
    """
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relação com o usuário
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Dados do Asaas
    asaas_id = Column(String(255), unique=True, index=True, nullable=False)  # ID da cobrança no Asaas (ex: pay_...)
    asaas_customer_id = Column(String(255), nullable=True)  # ID do cliente no Asaas (ex: cus_...)
    
    # Detalhes da Cobrança
    value = Column(Float, nullable=False)  # Valor em Reais
    description = Column(String(500), nullable=True)  # Descrição da cobrança
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    billing_type = Column(SQLEnum(BillingType), default=BillingType.BOLETO, nullable=False)
    
    # Datas
    due_date = Column(DateTime(timezone=True), nullable=False, index=True)  # Data de vencimento
    payment_date = Column(DateTime(timezone=True), nullable=True)  # Data do pagamento efetivo
    confirmed_date = Column(DateTime(timezone=True), nullable=True)  # Data de confirmação
    
    # URLs e Documentos
    invoice_url = Column(String(500), nullable=True)  # URL do PDF da fatura
    bank_slip_url = Column(String(500), nullable=True)  # URL do boleto (se aplicável)
    invoice_number = Column(String(100), nullable=True)  # Número da nota fiscal
    
    # Informações Adicionais
    external_reference = Column(String(255), nullable=True)  # Referência externa (ex: upgrade de plano)
    original_value = Column(Float, nullable=True)  # Valor original (antes de descontos)
    interest_value = Column(Float, default=0.0, nullable=True)  # Juros
    discount_value = Column(Float, default=0.0, nullable=True)  # Desconto
    net_value = Column(Float, nullable=True)  # Valor líquido recebido
    
    # PIX
    pix_qr_code = Column(Text, nullable=True)  # QR Code PIX (base64)
    pix_copy_paste = Column(Text, nullable=True)  # Código PIX copia e cola
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    user = relationship("User", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, asaas_id={self.asaas_id}, value={self.value}, status={self.status.value})>"
    
    @property
    def is_paid(self):
        """Verifica se o pagamento foi recebido"""
        return self.status in [PaymentStatus.RECEIVED, PaymentStatus.CONFIRMED]
    
    @property
    def is_overdue(self):
        """Verifica se o pagamento está vencido"""
        if self.is_paid:
            return False
        now = datetime.now(timezone.utc)
        due = self.due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        return now > due
    
    @property
    def days_until_due(self):
        """Retorna dias até o vencimento (negativo se vencido), None se pago"""
        if self.is_paid:
            return None
        now = datetime.now(timezone.utc)
        due = self.due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        delta = due - now
        return delta.days
    
    @property
    def status_label(self):
        """Retorna label amigável do status"""
        labels = {
            PaymentStatus.PENDING: "Pendente",
            PaymentStatus.RECEIVED: "Recebido",
            PaymentStatus.CONFIRMED: "Confirmado",
            PaymentStatus.OVERDUE: "Vencido",
            PaymentStatus.REFUNDED: "Estornado",
        }
        return labels.get(self.status, self.status.value.title())
    
    @property
    def status_color(self):
        """Retorna cor para o status (Tailwind CSS)"""
        colors = {
            PaymentStatus.PENDING: "yellow",
            PaymentStatus.RECEIVED: "green",
            PaymentStatus.CONFIRMED: "emerald",
            PaymentStatus.OVERDUE: "red",
            PaymentStatus.REFUNDED: "gray",
        }
        return colors.get(self.status, "gray")
