"""
SentinelWeb - Aplicação Principal FastAPI
=========================================
Este é o ponto de entrada da aplicação.
Configura rotas, templates e middlewares.
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
import os

# Imports locais
from database import get_db, init_db, engine
from models import User, Site, MonitorLog, HeartbeatCheck, SystemConfig, Payment, PaymentStatus, BillingType
from schemas import (
    UserCreate, UserLogin, UserUpdate, SiteCreate, SiteUpdate, 
    SiteResponse, MessageResponse, DashboardStats
)
from auth import (
    get_password_hash, create_access_token, authenticate_user,
    get_current_user, get_optional_user, get_user_by_email
)
from tasks import scan_site, scan_all_sites


# ============================================
# DEPENDÊNCIAS DE SEGURANÇA
# ============================================

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependência que verifica se o usuário é superadmin.
    Usado para proteger rotas administrativas.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Você não tem permissão de administrador."
        )
    return current_user

# ============================================
# INICIALIZAÇÃO DO FASTAPI
# ============================================

app = FastAPI(
    title="SentinelWeb",
    description="Sistema de Monitoramento de Sites e Segurança Básica",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

# ============================================
# MIDDLEWARES DE SEGURANÇA
# ============================================

# CORS: Configuração de origens permitidas
from fastapi.middleware.cors import CORSMiddleware

# Em produção, especifique domínios exatos
allowed_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Se APP_DOMAIN estiver configurado, adiciona à lista
if os.getenv("APP_DOMAIN"):
    allowed_origins.append(f"https://{os.getenv('APP_DOMAIN')}")
    allowed_origins.append(f"http://{os.getenv('APP_DOMAIN')}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Headers de Segurança Adicionais
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Trusted Host: Previne HTTP Host Header attacks
trusted_hosts = ["localhost", "127.0.0.1"]
if os.getenv("APP_DOMAIN"):
    trusted_hosts.append(os.getenv("APP_DOMAIN"))
    trusted_hosts.append(f"www.{os.getenv('APP_DOMAIN')}")

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=trusted_hosts
)

# Configura arquivos estáticos (screenshots, etc)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configura templates Jinja2
templates = Jinja2Templates(directory="templates")

# Adiciona filtro personalizado para formatação de data
def format_datetime(value, format="%d/%m/%Y %H:%M"):
    if value is None:
        return "Nunca"
    if isinstance(value, str):
        return value
    return value.strftime(format)

def format_latency(value):
    if value is None:
        return "N/A"
    return f"{value:.0f}ms"

def from_json(value):
    """Converte string JSON para objeto Python"""
    if value is None or value == "":
        return []
    try:
        import json
        return json.loads(value)
    except:
        return []

templates.env.filters["datetime"] = format_datetime
templates.env.filters["latency"] = format_latency
templates.env.filters["from_json"] = from_json


# ============================================
# EVENTO DE INICIALIZAÇÃO
# ============================================

@app.on_event("startup")
async def startup_event():
    """Inicializa o banco de dados na inicialização"""
    init_db()


# ============================================
# HEALTH CHECK ENDPOINT (PRODUÇÃO)
# ============================================

@app.get("/health", response_class=JSONResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Endpoint de health check para monitoramento.
    Verifica conectividade com banco de dados e Redis.
    
    Usado por:
    - Docker healthcheck
    - Nginx upstream check
    - Monitoramento externo (UptimeRobot, Pingdom)
    - Load balancers
    
    Returns:
        JSON com status do sistema
    """
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "sentinelweb",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Verifica database
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Verifica Redis (Celery broker)
    try:
        from celery_app import celery_app
        celery_app.broker_connection().ensure_connection(max_retries=1)
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Status code baseado na saúde
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(content=health_status, status_code=status_code)


# ============================================
# ROTAS PÚBLICAS (SEM AUTENTICAÇÃO)
# ============================================

@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Landing Page - redireciona para dashboard se logado"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    # Busca preços do banco de dados
    config = db.query(SystemConfig).first()
    
    # Se não existir configuração, usa valores padrão
    if not config:
        config = SystemConfig(
            plan_free_price=0.0,
            plan_pro_price=49.0,
            plan_agency_price=149.0
        )
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "plan_free_price": config.plan_free_price,
        "plan_pro_price": config.plan_pro_price,
        "plan_agency_price": config.plan_agency_price
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    user: Optional[User] = Depends(get_optional_user)
):
    """Página de login"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": None
    })


@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Processa o login"""
    user = authenticate_user(db, email, password)
    
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Email ou senha incorretos"
        })
    
    # Cria token JWT
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Redireciona para dashboard com cookie
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=86400,  # 24 horas
        samesite="lax"
    )
    
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    user: Optional[User] = Depends(get_optional_user)
):
    """Página de cadastro"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("register.html", {
        "request": request,
        "error": None
    })


@app.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    company_name: str = Form(None),
    cpf_cnpj: str = Form(...),
    db: Session = Depends(get_db)
):
    """Processa o cadastro"""
    # Validações
    if password != password_confirm:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "As senhas não coincidem"
        })
    
    if len(password) < 6:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "A senha deve ter no mínimo 6 caracteres"
        })
    
    # Valida CPF/CNPJ
    cpf_cnpj_clean = cpf_cnpj.replace(".", "").replace("-", "").replace("/", "")
    if len(cpf_cnpj_clean) not in [11, 14]:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos"
        })
    
    # Verifica se email já existe
    existing_user = get_user_by_email(db, email)
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Este email já está cadastrado"
        })
    
    # Cria o usuário
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        hashed_password=hashed_password,
        company_name=company_name,
        cpf_cnpj=cpf_cnpj_clean
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Login automático após cadastro
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )
    
    return response


@app.get("/logout")
async def logout():
    """Faz logout removendo o cookie"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response


# ============================================
# ROTA PÚBLICA DE PING (HEARTBEAT)
# ============================================

@app.get("/ping/{slug}")
async def heartbeat_ping(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Rota ultra-rápida para receber pings de heartbeat.
    
    Esta rota é chamada por scripts/cron jobs para indicar
    que estão funcionando. Deve ser extremamente rápida.
    
    Exemplo de uso em script bash:
        curl https://sentinelweb.com/ping/a1b2c3d4
    
    Exemplo em Python:
        import requests
        requests.get('https://sentinelweb.com/ping/a1b2c3d4')
    
    Args:
        slug: Identificador único do heartbeat check
    
    Returns:
        JSON com status OK
    
    Performance:
        - Query simples por índice único
        - Update mínimo de 4 campos
        - Sem cálculos pesados
        - Sem I/O adicional
        - Resposta em <50ms
    """
    from datetime import datetime, timezone, timedelta
    
    # Busca heartbeat (query otimizada por índice único)
    heartbeat = db.query(HeartbeatCheck).filter(
        HeartbeatCheck.slug == slug,
        HeartbeatCheck.is_active == True
    ).first()
    
    if not heartbeat:
        raise HTTPException(status_code=404, detail="Heartbeat not found")
    
    # Update ultra-rápido (apenas 5 campos)
    now = datetime.now(timezone.utc)
    heartbeat.last_ping = now
    heartbeat.next_expected_ping = now + timedelta(seconds=heartbeat.expected_period)
    heartbeat.status = 'up'
    heartbeat.total_pings += 1
    heartbeat.alert_sent = False  # Reset flag de alerta
    
    db.commit()
    
    # Resposta mínima (formato curl-friendly)
    return {
        "ok": True,
        "name": heartbeat.name,
        "timestamp": now.isoformat()
    }


# ============================================
# ROTA PÚBLICA - STATUS PAGE
# ============================================

@app.get("/status/{user_id}", response_class=HTMLResponse)
async def public_status_page(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Página pública de status dos sites de um usuário.
    
    Esta página é acessível sem login e mostra o status
    atual de todos os sites monitorados por um usuário.
    
    Args:
        user_id: ID do usuário dono dos sites
    
    Returns:
        Página HTML com status público dos sites
    
    Note:
        Não requer autenticação - é uma página pública
    """
    # Busca o usuário
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Status page não encontrada")
    
    # Busca apenas sites ativos do usuário
    sites = db.query(Site).filter(
        Site.owner_id == user_id,
        Site.is_active == True
    ).order_by(Site.domain).all()
    
    # Calcula estatísticas
    total_sites = len(sites)
    sites_online = sum(1 for s in sites if s.current_status == "online")
    sites_offline = sum(1 for s in sites if s.current_status == "offline")
    
    stats = {
        "total": total_sites,
        "online": sites_online,
        "offline": sites_offline,
        "uptime_percentage": round((sites_online / total_sites * 100) if total_sites > 0 else 0, 1)
    }
    
    return templates.TemplateResponse("public_status.html", {
        "request": request,
        "company_name": user.company_name or "Status Page",
        "sites": sites,
        "stats": stats,
        "now": datetime.utcnow
    })


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user: User = Depends(get_current_user)
):
    """Página de perfil do usuário"""
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user
    })


@app.get("/subscription", response_class=HTMLResponse)
async def subscription_page(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Página de gerenciamento de assinatura e faturas.
    
    Mostra:
    - Plano atual do usuário
    - Status da assinatura
    - Histórico de faturas (pagas e pendentes)
    - Links para pagamento de faturas pendentes
    """
    from services.asaas import AsaasService
    
    # Define nome legível do plano
    plan_names = {
        'free': 'Gratuito',
        'pro': 'Profissional',
        'agency': 'Agência'
    }
    plan_name = plan_names.get(user.plan_status, user.plan_status.title())
    
    # Inicializa variáveis
    payment_history = []
    subscription_details = None
    has_asaas_integration = False
    
    # Se o usuário tem customer_id, busca dados no Asaas
    if user.asaas_customer_id:
        has_asaas_integration = True
        
        try:
            asaas_service = AsaasService(db)
            
            # Busca histórico de pagamentos
            payment_history = asaas_service.get_subscription_payments(
                user.asaas_customer_id
            )
            
            # Busca assinaturas ativas (se houver)
            try:
                subscriptions = asaas_service.get_customer_subscriptions(
                    user.asaas_customer_id
                )
                if subscriptions and len(subscriptions) > 0:
                    subscription_details = subscriptions[0]  # Pega a primeira assinatura ativa
            except Exception as sub_error:
                print(f"⚠️ Erro ao buscar assinaturas: {str(sub_error)}")
                # Continua sem detalhes de assinatura
            
            print(f"✅ Dados carregados: {len(payment_history)} faturas encontradas")
            
        except Exception as e:
            print(f"❌ Erro ao carregar dados do Asaas: {str(e)}")
            # Continua renderizando a página mesmo com erro
    
    # Formata os valores para exibição
    for payment in payment_history:
        # Formata data para padrão brasileiro
        if payment.get('due_date'):
            try:
                from datetime import datetime
                date_obj = datetime.strptime(payment['due_date'], '%Y-%m-%d')
                payment['due_date_formatted'] = date_obj.strftime('%d/%m/%Y')
            except:
                payment['due_date_formatted'] = payment['due_date']
        
        # Formata valor para moeda brasileira
        payment['value_formatted'] = f"R$ {payment['value']:.2f}".replace('.', ',')
        
        # Define status legível em português
        status_map = {
            'PENDING': 'Pendente',
            'RECEIVED': 'Pago',
            'CONFIRMED': 'Confirmado',
            'OVERDUE': 'Vencido',
            'REFUNDED': 'Reembolsado',
            'RECEIVED_IN_CASH': 'Pago em Dinheiro',
            'REFUND_REQUESTED': 'Reembolso Solicitado',
            'CHARGEBACK_REQUESTED': 'Chargeback Solicitado',
            'CHARGEBACK_DISPUTE': 'Disputa de Chargeback',
            'AWAITING_CHARGEBACK_REVERSAL': 'Aguardando Reversão',
            'DUNNING_REQUESTED': 'Cobrança Solicitada',
            'DUNNING_RECEIVED': 'Cobrança Recebida',
            'AWAITING_RISK_ANALYSIS': 'Análise de Risco'
        }
        payment['status_text'] = status_map.get(payment['status'], payment['status'])
        
        # Define tipo de pagamento legível
        billing_type_map = {
            'BOLETO': 'Boleto',
            'CREDIT_CARD': 'Cartão de Crédito',
            'PIX': 'PIX',
            'DEBIT_CARD': 'Cartão de Débito',
            'TRANSFER': 'Transferência',
            'DEPOSIT': 'Depósito'
        }
        payment['billing_type_text'] = billing_type_map.get(
            payment['billing_type'], 
            payment['billing_type']
        )
    
    return templates.TemplateResponse("subscription.html", {
        "request": request,
        "user": user,
        "plan_name": plan_name,
        "payment_history": payment_history,
        "subscription_details": subscription_details,
        "has_asaas_integration": has_asaas_integration
    })


# ============================================
# ROTAS PROTEGIDAS (REQUEREM AUTENTICAÇÃO)
# ============================================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dashboard principal com lista de sites"""
    from plan_limits import get_usage_stats
    
    # Busca sites do usuário
    sites = db.query(Site).filter(Site.owner_id == user.id).order_by(Site.domain).all()
    
    # Calcula estatísticas
    total_sites = len(sites)
    sites_online = sum(1 for s in sites if s.current_status == "online")
    sites_offline = sum(1 for s in sites if s.current_status == "offline")
    sites_unknown = total_sites - sites_online - sites_offline
    
    # Sites com SSL expirando em 30 dias
    ssl_expiring = sum(1 for s in sites if s.ssl_days_remaining and s.ssl_days_remaining < 30)
    
    # Sites com portas abertas
    sites_with_ports = sum(1 for s in sites if s.open_ports)
    
    stats = {
        "total": total_sites,
        "online": sites_online,
        "offline": sites_offline,
        "unknown": sites_unknown,
        "ssl_expiring": ssl_expiring,
        "open_ports": sites_with_ports
    }
    
    # Estatísticas de uso do plano
    plan_usage = get_usage_stats(user, db)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "sites": sites,
        "stats": stats,
        "plan_usage": plan_usage,
        "now": datetime.utcnow
    })


@app.get("/sites/add", response_class=HTMLResponse)
async def add_site_page(
    request: Request,
    user: User = Depends(get_current_user)
):
    """Página para adicionar novo site"""
    return templates.TemplateResponse("site_form.html", {
        "request": request,
        "user": user,
        "site": None,
        "error": None
    })


@app.post("/sites/add")
async def add_site(
    request: Request,
    domain: str = Form(...),
    name: str = Form(None),
    check_interval: int = Form(5),
    must_contain_keyword: str = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adiciona um novo site"""
    import re
    from plan_limits import can_add_site, validate_check_interval
    
    # VALIDAÇÃO 1: Verifica limite de sites do plano
    can_add, error_message = can_add_site(user, db)
    if not can_add:
        return templates.TemplateResponse("site_form.html", {
            "request": request,
            "user": user,
            "site": None,
            "error": error_message
        })
    
    # VALIDAÇÃO 2: Verifica intervalo mínimo do plano
    is_valid_interval, interval_error = validate_check_interval(user, check_interval)
    if not is_valid_interval:
        return templates.TemplateResponse("site_form.html", {
            "request": request,
            "user": user,
            "site": None,
            "error": interval_error
        })
    
    # Limpa o domínio
    domain = re.sub(r'^https?://', '', domain).rstrip('/')
    
    # Limpa a keyword (remove espaços extras)
    if must_contain_keyword:
        must_contain_keyword = must_contain_keyword.strip()
        if not must_contain_keyword:  # Se ficou vazio após strip
            must_contain_keyword = None
    
    # Verifica se já existe para este usuário
    existing = db.query(Site).filter(
        Site.domain == domain,
        Site.owner_id == user.id
    ).first()
    
    if existing:
        return templates.TemplateResponse("site_form.html", {
            "request": request,
            "user": user,
            "site": None,
            "error": "Este domínio já está cadastrado"
        })
    
    # Cria o site
    new_site = Site(
        domain=domain,
        name=name or domain,
        check_interval=check_interval,
        must_contain_keyword=must_contain_keyword,
        owner_id=user.id,
        current_status="unknown"
    )
    
    db.add(new_site)
    db.commit()
    db.refresh(new_site)
    
    # Agenda scan imediato
    scan_site.delay(new_site.id)
    
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/sites/{site_id}", response_class=HTMLResponse)
async def site_detail(
    request: Request,
    site_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Página de detalhes completos do site (Raio-X)"""
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.owner_id == user.id
    ).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site não encontrado")
    
    # Busca últimos logs para estatísticas
    recent_logs = db.query(MonitorLog).filter(
        MonitorLog.site_id == site_id
    ).order_by(MonitorLog.checked_at.desc()).limit(100).all()
    
    # Calcula estatísticas
    total_checks = len(recent_logs)
    online_checks = len([log for log in recent_logs if log.status == "online"])
    uptime_percent = (online_checks / total_checks * 100) if total_checks > 0 else 0
    
    # Latência média
    latencies = [log.latency_ms for log in recent_logs if log.latency_ms is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else None
    
    # Calcula dias até expiração do domínio
    domain_days_remaining = None
    if site.domain_expiration_date:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        # Garante que ambos os datetimes tenham timezone
        expiration = site.domain_expiration_date
        if expiration.tzinfo is None:
            # Se não tem timezone, assume UTC
            expiration = expiration.replace(tzinfo=timezone.utc)
        
        delta = expiration - now
        domain_days_remaining = delta.days
    
    return templates.TemplateResponse("site_details.html", {
        "request": request,
        "user": user,
        "site": site,
        "uptime_percent": uptime_percent,
        "avg_latency": avg_latency,
        "total_checks": total_checks,
        "domain_days_remaining": domain_days_remaining,
        "now": datetime.now(timezone.utc)
    })


@app.get("/sites/{site_id}/logs", response_class=HTMLResponse)
async def site_logs(
    request: Request,
    site_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Página antiga com logs detalhados (mantida para referência)"""
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.owner_id == user.id
    ).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site não encontrado")
    
    # Busca últimos 50 logs
    logs = db.query(MonitorLog).filter(
        MonitorLog.site_id == site.id
    ).order_by(MonitorLog.checked_at.desc()).limit(50).all()
    
    # Calcula média de latência dos últimos 24h
    yesterday = datetime.utcnow() - timedelta(days=1)
    avg_latency = db.query(func.avg(MonitorLog.latency_ms)).filter(
        MonitorLog.site_id == site.id,
        MonitorLog.checked_at >= yesterday,
        MonitorLog.latency_ms.isnot(None)
    ).scalar()
    
    # Calcula uptime % dos últimos 7 dias
    week_ago = datetime.utcnow() - timedelta(days=7)
    total_checks = db.query(MonitorLog).filter(
        MonitorLog.site_id == site.id,
        MonitorLog.checked_at >= week_ago
    ).count()
    
    online_checks = db.query(MonitorLog).filter(
        MonitorLog.site_id == site.id,
        MonitorLog.checked_at >= week_ago,
        MonitorLog.status == "online"
    ).count()
    
    uptime_percent = (online_checks / total_checks * 100) if total_checks > 0 else 0
    
    return templates.TemplateResponse("site_detail.html", {
        "request": request,
        "user": user,
        "site": site,
        "logs": logs,
        "avg_latency": avg_latency,
        "uptime_percent": uptime_percent
    })


@app.get("/sites/{site_id}/edit", response_class=HTMLResponse)
async def edit_site_page(
    request: Request,
    site_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Página para editar site"""
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.owner_id == user.id
    ).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site não encontrado")
    
    return templates.TemplateResponse("site_form.html", {
        "request": request,
        "user": user,
        "site": site,
        "error": None
    })


@app.post("/sites/{site_id}/edit")
async def edit_site(
    request: Request,
    site_id: int,
    name: str = Form(None),
    check_interval: int = Form(5),
    must_contain_keyword: str = Form(None),
    is_active: bool = Form(True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza um site"""
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.owner_id == user.id
    ).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site não encontrado")
    
    # Limpa a keyword (remove espaços extras)
    if must_contain_keyword:
        must_contain_keyword = must_contain_keyword.strip()
        if not must_contain_keyword:  # Se ficou vazio após strip
            must_contain_keyword = None
    
    site.name = name or site.domain
    site.check_interval = check_interval
    site.must_contain_keyword = must_contain_keyword
    site.is_active = is_active
    
    db.commit()
    
    return RedirectResponse(url=f"/sites/{site_id}", status_code=302)


@app.post("/sites/{site_id}/delete")
async def delete_site(
    site_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove um site"""
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.owner_id == user.id
    ).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site não encontrado")
    
    db.delete(site)
    db.commit()
    
    return RedirectResponse(url="/dashboard", status_code=302)


@app.post("/sites/{site_id}/scan")
async def trigger_scan(
    site_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dispara scan manual de um site"""
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.owner_id == user.id
    ).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site não encontrado")
    
    # Agenda scan
    scan_site.delay(site.id)
    
    return RedirectResponse(url=f"/sites/{site_id}", status_code=302)


@app.post("/api/scan-all")
async def api_scan_all(
    user: User = Depends(get_current_user)
):
    """Dispara scan de todos os sites do usuário"""
    scan_all_sites.delay()
    return {"message": "Scan agendado para todos os sites"}


@app.get("/api/sites/{site_id}/history")
async def get_site_history(
    site_id: int,
    hours: int = 24,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna histórico de performance do site para gráficos.
    
    Otimizado para visualização com ApexCharts:
    - Agrupa dados a cada 30 minutos para melhor performance
    - Retorna latência média e status de disponibilidade
    - Últimas 24 horas por padrão
    
    Args:
        site_id: ID do site
        hours: Número de horas de histórico (padrão: 24)
    
    Returns:
        JSON com dados otimizados para gráficos
    """
    from datetime import datetime, timedelta, timezone
    
    # Verifica se o site pertence ao usuário
    site = db.query(Site).filter(
        Site.id == site_id,
        Site.owner_id == user.id
    ).first()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site não encontrado")
    
    # Calcula período
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=hours)
    
    # Busca logs do período
    logs = db.query(MonitorLog).filter(
        MonitorLog.site_id == site_id,
        MonitorLog.checked_at >= start_time
    ).order_by(MonitorLog.checked_at.asc()).all()
    
    if not logs:
        # Retorna dados vazios se não houver histórico
        return {
            "categories": [],
            "latency": [],
            "status": [],
            "uptime_hours": [],
            "total_checks": 0,
            "avg_latency": 0,
            "uptime_percent": 0
        }
    
    # Agrupa dados a cada 30 minutos para otimização
    interval_minutes = 30
    grouped_data = {}
    
    for log in logs:
        # Arredonda para o intervalo mais próximo
        log_time = log.checked_at
        if log_time.tzinfo is None:
            log_time = log_time.replace(tzinfo=timezone.utc)
        
        # Cria chave do intervalo (arredonda para 30 min)
        interval_key = log_time.replace(
            minute=(log_time.minute // interval_minutes) * interval_minutes,
            second=0,
            microsecond=0
        )
        
        if interval_key not in grouped_data:
            grouped_data[interval_key] = {
                'latencies': [],
                'statuses': [],
                'count': 0
            }
        
        grouped_data[interval_key]['count'] += 1
        
        if log.latency_ms is not None:
            grouped_data[interval_key]['latencies'].append(log.latency_ms)
        
        # 1 = online, 0 = offline
        grouped_data[interval_key]['statuses'].append(
            1 if log.status == 'online' else 0
        )
    
    # Prepara dados para o gráfico
    categories = []
    latency_data = []
    status_data = []
    
    for interval_time in sorted(grouped_data.keys()):
        data = grouped_data[interval_time]
        
        # Formata horário (HH:MM)
        categories.append(interval_time.strftime('%H:%M'))
        
        # Calcula latência média do intervalo
        if data['latencies']:
            avg_latency = sum(data['latencies']) / len(data['latencies'])
            latency_data.append(round(avg_latency, 2))
        else:
            latency_data.append(None)  # Null para offline
        
        # Calcula status (1 = todos online, 0 = algum offline)
        if data['statuses']:
            avg_status = sum(data['statuses']) / len(data['statuses'])
            status_data.append(round(avg_status, 2))
        else:
            status_data.append(0)
    
    # Calcula uptime por hora (para as barras)
    uptime_hours = []
    current_hour = start_time.replace(minute=0, second=0, microsecond=0)
    
    while current_hour <= now:
        next_hour = current_hour + timedelta(hours=1)
        
        # Filtra logs dessa hora
        hour_logs = [
            log for log in logs
            if current_hour <= (log.checked_at if log.checked_at.tzinfo else log.checked_at.replace(tzinfo=timezone.utc)) < next_hour
        ]
        
        if hour_logs:
            online_count = sum(1 for log in hour_logs if log.status == 'online')
            hour_uptime = (online_count / len(hour_logs)) * 100
            
            uptime_hours.append({
                'hour': current_hour.strftime('%d/%m %H:00'),
                'uptime': round(hour_uptime, 1),
                'checks': len(hour_logs)
            })
        else:
            uptime_hours.append({
                'hour': current_hour.strftime('%d/%m %H:00'),
                'uptime': None,
                'checks': 0
            })
        
        current_hour = next_hour
    
    # Estatísticas gerais
    total_checks = len(logs)
    online_checks = sum(1 for log in logs if log.status == 'online')
    uptime_percent = (online_checks / total_checks * 100) if total_checks > 0 else 0
    
    all_latencies = [log.latency_ms for log in logs if log.latency_ms is not None]
    avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0
    
    return {
        "categories": categories,
        "latency": latency_data,
        "status": status_data,
        "uptime_hours": uptime_hours,
        "total_checks": total_checks,
        "avg_latency": round(avg_latency, 2),
        "uptime_percent": round(uptime_percent, 2)
    }


@app.put("/api/profile")
async def update_profile(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    company_name: str = Form(None),
    cpf_cnpj: str = Form(...)
):
    """Atualiza informações do perfil do usuário"""
    # Validações
    if password != password_confirm:
        return JSONResponse(status_code=400, content={"error": "As senhas não coincidem"})
    
    if len(password) < 6:
        return JSONResponse(status_code=400, content={"error": "A senha deve ter no mínimo 6 caracteres"})
    
    # Valida CPF/CNPJ
    cpf_cnpj_clean = cpf_cnpj.replace(".", "").replace("-", "").replace("/", "")
    if len(cpf_cnpj_clean) not in [11, 14]:
        return JSONResponse(status_code=400, content={"error": "CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos"})
    
    # Atualiza usuário
    user.email = email
    user.company_name = company_name
    user.cpf_cnpj = cpf_cnpj_clean
    user.hashed_password = get_password_hash(password)
    
    db.commit()
    
    return {"message": "Perfil atualizado com sucesso"}
