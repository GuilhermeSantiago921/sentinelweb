"""
SentinelWeb - Tarefas Celery (Workers)
======================================
Define as tarefas que rodam em background:
- Scan individual de site
- Scan de todos os sites ativos

IMPORTANTE: Estas tarefas NÃO devem travar a API.
Elas rodam em processos separados (workers Celery).
"""

from celery_app import celery_app
from database import SessionLocal
from models import Site, MonitorLog, User
from scanner import full_scan, ScanResult, send_telegram_alert, check_domain_expiration, check_blacklist, check_wordpress_health, check_pagespeed, check_seo_health, check_general_security
from datetime import datetime
import logging
import json

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def scan_site(self, site_id: int) -> dict:
    """
    Executa scan completo de um site específico.
    
    Esta task:
    1. Busca o site no banco
    2. Executa o full_scan
    3. Atualiza o status do site
    4. Cria um registro de log
    
    Args:
        site_id: ID do site no banco de dados
    
    Returns:
        Dict com resultado do scan
    
    Retry Policy:
        - Máximo 3 tentativas
        - Espera 60 segundos entre tentativas
        - Falhas são logadas mas não derrubam o worker
    """
    db = SessionLocal()
    
    try:
        # Busca o site
        site = db.query(Site).filter(Site.id == site_id).first()
        
        if not site:
            logger.warning(f"Site {site_id} não encontrado no banco")
            return {"error": "Site não encontrado"}
        
        if not site.is_active:
            logger.info(f"Site {site.domain} está inativo, pulando scan")
            return {"skipped": True, "reason": "Site inativo"}
        
        logger.info(f"🔍 Iniciando scan de {site.domain}")
        
        # Guarda o status anterior para detectar mudanças
        previous_status = site.current_status
        was_online = (previous_status == "online")
        
        # Executa o scan completo (com verificação anti-defacement se configurada)
        result: ScanResult = full_scan(site.domain, must_contain_keyword=site.must_contain_keyword)
        
        # Detecta mudanças de status para disparar alertas
        is_now_online = result.is_online
        status_changed = (was_online != is_now_online)
        
        # Atualiza o site com os resultados
        site.current_status = "online" if result.is_online else "offline"
        site.last_check = datetime.utcnow()
        site.last_latency = result.latency_ms
        site.ssl_valid = result.ssl_valid
        site.ssl_days_remaining = result.ssl_days_remaining
        
        # Verifica expiração do domínio (Whois)
        try:
            domain_expiration = check_domain_expiration(site.domain)
            if domain_expiration:
                site.domain_expiration_date = domain_expiration
                logger.info(f"📅 Expiração do domínio {site.domain}: {domain_expiration.strftime('%Y-%m-%d')}")
            else:
                logger.warning(f"⚠️  Não foi possível obter data de expiração para {site.domain}")
        except Exception as e:
            logger.error(f"❌ Erro ao verificar expiração do domínio {site.domain}: {e}")
            # Não quebra o monitoramento se Whois falhar
        
        # Verifica se está em blacklist (RBL)
        try:
            is_blacklisted, blacklisted_in_list = check_blacklist(site.domain, timeout=2.0)
            site.is_blacklisted = is_blacklisted
            
            if blacklisted_in_list:
                site.blacklisted_in = json.dumps(blacklisted_in_list)
                logger.warning(f"🚨 {site.domain} está em blacklist: {', '.join(blacklisted_in_list)}")
            else:
                site.blacklisted_in = None
                
            # Envia alerta se estiver em blacklist
            if is_blacklisted:
                owner = db.query(User).filter(User.id == site.owner_id).first()
                if owner and owner.telegram_chat_id:
                    message = (
                        f"🚨 <b>ALERTA - BLACKLIST DETECTADA</b>\n\n"
                        f"🌐 <b>Site:</b> {site.name or site.domain}\n"
                        f"🔗 <b>Domínio:</b> {site.domain}\n"
                        f"⏰ <b>Horário:</b> {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC\n"
                        f"⚠️ <b>Blacklists:</b> {', '.join(blacklisted_in_list)}\n\n"
                        f"Seu IP está listado em uma ou mais blacklists. "
                        f"Isso pode afetar a reputação e entrega de emails."
                    )
                    send_telegram_alert(message, owner.telegram_chat_id)
                    logger.info(f"🚨 Alerta de blacklist enviado para {site.domain}")
                    
        except Exception as e:
            logger.error(f"❌ Erro ao verificar blacklist para {site.domain}: {e}")
            # Não quebra o monitoramento se RBL falhar
            site.is_blacklisted = False
            site.blacklisted_in = None
        
        # Verifica WordPress Security (se online)
        if result.is_online:
            try:
                wp_health = check_wordpress_health(site.domain, timeout=5)
                
                site.is_wordpress = wp_health['is_wordpress']
                site.wp_version = wp_health['wp_version']
                
                if wp_health['vulnerabilities']:
                    site.vulnerabilities_found = json.dumps(wp_health['vulnerabilities'])
                    logger.warning(f"⚠️ {len(wp_health['vulnerabilities'])} vulnerabilidade(s) WordPress encontrada(s) em {site.domain}")
                    
                    # Envia alerta Telegram se houver vulnerabilidades críticas ou high
                    critical_vulns = [v for v in wp_health['vulnerabilities'] if v.get('severity') in ['critical', 'high']]
                    
                    if critical_vulns:
                        owner = db.query(User).filter(User.id == site.owner_id).first()
                        if owner and owner.telegram_chat_id:
                            vuln_list = "\n".join([f"• {v['description']}" for v in critical_vulns[:5]])
                            message = (
                                f"🚨 <b>ALERTA - VULNERABILIDADES WORDPRESS</b>\n\n"
                                f"🌐 <b>Site:</b> {site.name or site.domain}\n"
                                f"🔗 <b>Domínio:</b> {site.domain}\n"
                                f"⏰ <b>Horário:</b> {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC\n"
                                f"⚠️ <b>Vulnerabilidades Críticas:</b> {len(critical_vulns)}\n\n"
                                f"{vuln_list}\n\n"
                                f"Recomenda-se ação imediata para corrigir as vulnerabilidades."
                            )
                            send_telegram_alert(message, owner.telegram_chat_id)
                            logger.info(f"🚨 Alerta de vulnerabilidades WordPress enviado para {site.domain}")
                else:
                    site.vulnerabilities_found = None
                
                # Salva plugins detectados (incluindo CVEs)
                if 'plugins_detected' in wp_health and wp_health['plugins_detected']:
                    site.plugins_detected = json.dumps(wp_health['plugins_detected'])
                    
                    # Conta plugins com CVEs
                    plugins_with_cves = [p for p in wp_health['plugins_detected'] if p.get('vulnerabilities')]
                    if plugins_with_cves:
                        logger.warning(f"🔌 {len(plugins_with_cves)} plugin(s) com vulnerabilidades CVE detectado(s) em {site.domain}")
                else:
                    site.plugins_detected = None
                    
                if site.is_wordpress:
                    version_info = f" (versão {site.wp_version})" if site.wp_version else ""
                    logger.info(f"✅ WordPress detectado em {site.domain}{version_info}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao verificar WordPress para {site.domain}: {e}")
                # Não quebra o monitoramento se WP scan falhar
        
        # ============================================
        # SEO HEALTH CHECK (INDEXABILIDADE)
        # ============================================
        try:
            logger.info(f"🔍 Verificando SEO Health para {site.domain}...")
            
            seo_health = check_seo_health(site.domain, timeout=5)
            
            # Estado anterior
            was_indexable = site.seo_indexable
            
            # Atualiza status SEO
            site.seo_indexable = seo_health.get('indexable', True)
            site.last_seo_check = datetime.utcnow()
            
            if seo_health.get('issues'):
                site.seo_issues = json.dumps(seo_health['issues'])
                logger.warning(f"⚠️ {len(seo_health['issues'])} problema(s) SEO detectado(s) em {site.domain}")
                
                # INCIDENTE CRÍTICO: Site bloqueou indexação
                if was_indexable and not site.seo_indexable:
                    owner = db.query(User).filter(User.id == site.owner_id).first()
                    if owner and owner.telegram_chat_id:
                        issues_text = "\n".join(seo_health['issues'])
                        message = (
                            f"💀 <b>ALERTA CRÍTICO - SITE DESINDEXADO</b>\n\n"
                            f"🌐 <b>Site:</b> {site.name or site.domain}\n"
                            f"🔗 <b>Domínio:</b> {site.domain}\n"
                            f"⏰ <b>Horário:</b> {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC\n\n"
                            f"🚨 <b>PERIGO:</b> O site está bloqueando motores de busca!\n\n"
                            f"<b>Problemas encontrados:</b>\n{issues_text}\n\n"
                            f"⚠️ <b>AÇÃO URGENTE NECESSÁRIA:</b> O site não aparecerá nas buscas do Google até isso ser corrigido!"
                        )
                        send_telegram_alert(message, owner.telegram_chat_id)
                        logger.error(f"💀 ALERTA CRÍTICO: {site.domain} está BLOQUEANDO INDEXAÇÃO!")
                
                # Site voltou a ser indexável
                elif not was_indexable and site.seo_indexable:
                    owner = db.query(User).filter(User.id == site.owner_id).first()
                    if owner and owner.telegram_chat_id:
                        message = (
                            f"✅ <b>SITE VOLTOU A SER INDEXÁVEL</b>\n\n"
                            f"🌐 <b>Site:</b> {site.name or site.domain}\n"
                            f"🔗 <b>Domínio:</b> {site.domain}\n"
                            f"⏰ <b>Horário:</b> {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC\n\n"
                            f"✅ Os bloqueios de indexação foram removidos.\n"
                            f"O Google poderá rastrear o site novamente!"
                        )
                        send_telegram_alert(message, owner.telegram_chat_id)
                        logger.info(f"✅ {site.domain} voltou a ser indexável")
            else:
                site.seo_issues = None
                logger.info(f"✅ SEO Health OK para {site.domain}")
        
        except Exception as e:
            logger.error(f"❌ Erro ao verificar SEO Health para {site.domain}: {e}")
            # Não quebra o monitoramento se SEO check falhar
        
        # 🔒 GENERAL TECH SCANNER (para sites NÃO-WordPress)
        if result.is_online and not site.is_wordpress:
            try:
                logger.info(f"🛠️ Iniciando General Tech Scanner para {site.domain}...")
                
                url = f"https://{site.domain}"
                general_sec = check_general_security(url, timeout=10)
                
                # Salva tech stack
                if general_sec.get('tech_stack') and general_sec['tech_stack'].get('success'):
                    site.tech_stack = json.dumps(general_sec['tech_stack']['technologies'])
                    site.last_tech_scan = datetime.utcnow()
                    logger.info(f"✅ {len(general_sec['tech_stack']['technologies'])} tecnologias detectadas em {site.domain}")
                
                # Salva vulnerabilidades
                if general_sec.get('vulnerabilities'):
                    site.general_vulnerabilities = json.dumps(general_sec['vulnerabilities'])
                    
                    # Alerta se encontrar CVEs críticos
                    critical_vulns = [
                        v for v in general_sec['vulnerabilities'] 
                        if 'CRITICAL' in str(v.get('severity', '')).upper() or 
                           'HIGH' in str(v.get('severity', '')).upper()
                    ]
                    
                    if critical_vulns:
                        owner = db.query(User).filter(User.id == site.owner_id).first()
                        if owner and owner.telegram_chat_id:
                            message = (
                                f"🚨 <b>VULNERABILIDADES CRÍTICAS DETECTADAS</b>\n\n"
                                f"🌐 <b>Site:</b> {site.name or site.domain}\n"
                                f"🔗 <b>Domínio:</b> {site.domain}\n"
                                f"⚠️ <b>CVEs Encontrados:</b> {len(critical_vulns)}\n\n"
                            )
                            
                            # Mostra até 3 vulnerabilidades para não ficar muito longo
                            for vuln in critical_vulns[:3]:
                                message += (
                                    f"🔴 <b>{vuln.get('cve_id')}</b>\n"
                                    f"   Tecnologia: {vuln.get('technology')} {vuln.get('version')}\n"
                                    f"   Severidade: {vuln.get('severity')}\n"
                                    f"   {vuln.get('summary', '')[:100]}...\n\n"
                                )
                            
                            if len(critical_vulns) > 3:
                                message += f"... e mais {len(critical_vulns) - 3} vulnerabilidade(s).\n"
                            
                            send_telegram_alert(message, owner.telegram_chat_id)
                            logger.warning(f"🚨 Alerta de CVE enviado para {site.domain}: {len(critical_vulns)} críticas")
                
                # Salva nota de headers de segurança
                if general_sec.get('security_headers'):
                    grade = general_sec['security_headers']['grade']
                    site.security_headers_grade = grade
                    logger.info(f"🔐 Security Headers Grade: {grade} para {site.domain}")
                    
                    # Alerta se a nota for F (péssima)
                    if grade == 'F':
                        owner = db.query(User).filter(User.id == site.owner_id).first()
                        if owner and owner.telegram_chat_id:
                            missing = general_sec['security_headers'].get('headers_missing', [])
                            message = (
                                f"⚠️ <b>SECURITY HEADERS CRÍTICOS AUSENTES</b>\n\n"
                                f"🌐 <b>Site:</b> {site.name or site.domain}\n"
                                f"🔗 <b>Domínio:</b> {site.domain}\n"
                                f"📊 <b>Nota:</b> F (Falhou)\n\n"
                                f"<b>Headers Faltando:</b>\n"
                            )
                            
                            for h in missing[:4]:  # Primeiros 4
                                message += f"• {h['header']}: {h['description']}\n"
                            
                            message += (
                                f"\n⚠️ Sem esses headers, seu site está vulnerável a "
                                f"ataques como XSS, clickjacking e MIME sniffing."
                            )
                            
                            send_telegram_alert(message, owner.telegram_chat_id)
                            logger.warning(f"⚠️ Alerta de Security Headers enviado para {site.domain}")
                
                db.commit()
                logger.info(f"✅ General Tech Scan concluído para {site.domain}")
                
            except Exception as e:
                logger.error(f"❌ Erro no General Tech Scan de {site.domain}: {e}")
                # Não quebra o monitoramento se tech scan falhar
        
        # Converte lista de portas para string
        if result.open_ports:
            site.open_ports = ",".join(map(str, result.open_ports))
        else:
            site.open_ports = None
        
        # Cria registro de log
        log_entry = MonitorLog(
            site_id=site.id,
            status="online" if result.is_online else "offline",
            http_status_code=result.http_status_code,
            latency_ms=result.latency_ms,
            ssl_valid=result.ssl_valid,
            ssl_days_remaining=result.ssl_days_remaining,
            ssl_issuer=result.ssl_issuer,
            open_ports=site.open_ports,
            error_message=result.error_message or result.ssl_error,
            checked_at=datetime.utcnow()
        )
        
        db.add(log_entry)
        db.commit()
        
        # 🚨 LÓGICA DE ALERTAS VIA TELEGRAM 🚨
        if status_changed:
            # Busca o usuário dono do site
            owner = db.query(User).filter(User.id == site.owner_id).first()
            
            if owner and owner.telegram_chat_id:
                if was_online and not is_now_online:
                    # Site CAIU (estava online, agora está offline)
                    message = (
                        f"🚨 <b>ALERTA - SITE FORA DO AR</b>\n\n"
                        f"🌐 <b>Site:</b> {site.name or site.domain}\n"
                        f"🔗 <b>Domínio:</b> {site.domain}\n"
                        f"⏰ <b>Horário:</b> {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC\n"
                        f"❌ <b>Status:</b> OFFLINE\n"
                    )
                    
                    if result.error_message:
                        message += f"📝 <b>Erro:</b> {result.error_message}\n"
                    
                    logger.info(f"🚨 Enviando alerta de QUEDA para {site.domain}")
                    send_telegram_alert(message, owner.telegram_chat_id)
                    
                elif not was_online and is_now_online:
                    # Site VOLTOU (estava offline, agora está online)
                    message = (
                        f"✅ <b>RECUPERAÇÃO - SITE VOLTOU</b>\n\n"
                        f"🌐 <b>Site:</b> {site.name or site.domain}\n"
                        f"🔗 <b>Domínio:</b> {site.domain}\n"
                        f"⏰ <b>Horário:</b> {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC\n"
                        f"✅ <b>Status:</b> ONLINE\n"
                        f"⚡ <b>Latência:</b> {result.latency_ms:.0f}ms\n"
                    )
                    
                    logger.info(f"✅ Enviando alerta de RECUPERAÇÃO para {site.domain}")
                    send_telegram_alert(message, owner.telegram_chat_id)
        
        logger.info(f"✅ Scan de {site.domain} concluído: {site.current_status}")
        
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"❌ Erro ao escanear site {site_id}: {str(e)}")
        db.rollback()
        
        # Tenta novamente se não excedeu retries
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Máximo de tentativas excedido para site {site_id}")
            return {"error": str(e)}
        
    finally:
        db.close()


@celery_app.task
def scan_all_sites() -> dict:
    """
    Escaneia todos os sites ativos.
    
    Esta task é executada periodicamente pelo Celery Beat.
    Para cada site ativo, agenda um scan_site individual.
    
    Isso permite paralelismo: múltiplos sites são escaneados
    simultaneamente por diferentes workers.
    
    Returns:
        Dict com contagem de sites agendados
    """
    db = SessionLocal()
    
    try:
        # Busca todos os sites ativos
        sites = db.query(Site).filter(Site.is_active == True).all()
        
        logger.info(f"📋 Agendando scan para {len(sites)} sites ativos")
        
        scheduled = 0
        for site in sites:
            # Agenda scan individual (não bloqueia)
            scan_site.delay(site.id)
            scheduled += 1
        
        logger.info(f"✅ {scheduled} scans agendados com sucesso")
        
        return {
            "scheduled": scheduled,
            "total_active": len(sites)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao agendar scans: {str(e)}")
        return {"error": str(e)}
        
    finally:
        db.close()


@celery_app.task
def scan_site_immediate(domain: str) -> dict:
    """
    Scan imediato de um domínio (sem salvar no banco).
    
    Útil para preview antes de cadastrar um site.
    
    Args:
        domain: Domínio a escanear
    
    Returns:
        Resultado do scan
    """
    try:
        result = full_scan(domain)
        return result.to_dict()
    except Exception as e:
        return {"error": str(e)}


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def run_pagespeed_audit(self, site_id: int) -> dict:
    """
    Executa auditoria de performance usando Google PageSpeed Insights.
    
    Esta task é SEPARADA do scan_site regular porque:
    - A API do Google demora 10-30 segundos para responder
    - Deve rodar apenas 1x por dia (não a cada 5 minutos)
    - Economiza quota da API (25k/dia no plano gratuito)
    
    Args:
        site_id: ID do site no banco de dados
    
    Returns:
        Dict com resultado da auditoria
    
    Retry Policy:
        - Máximo 2 tentativas
        - Espera 5 minutos entre tentativas
        - Se falhar, não quebra o monitoramento normal
    
    Scheduling:
        Configure no celery_app.py para rodar 1x por dia:
        
        celery_app.conf.beat_schedule = {
            'pagespeed-daily': {
                'task': 'tasks.run_pagespeed_audit_all',
                'schedule': crontab(hour=3, minute=0),  # 3am todos os dias
            }
        }
    """
    db = SessionLocal()
    
    try:
        # Busca o site
        site = db.query(Site).filter(Site.id == site_id).first()
        
        if not site:
            logger.warning(f"Site {site_id} não encontrado")
            return {"error": "Site não encontrado"}
        
        if not site.is_active:
            logger.info(f"Site {site.domain} inativo, pulando PageSpeed audit")
            return {"skipped": True, "reason": "Site inativo"}
        
        logger.info(f"🚀 Iniciando PageSpeed audit de {site.domain}")
        
        # Monta URL completa
        url = f"https://{site.domain}"
        
        # Executa auditoria (mobile first)
        result = check_pagespeed(url, strategy="mobile", timeout=30.0)
        
        if result["success"]:
            # Atualiza o site com os scores
            site.performance_score = result["performance_score"]
            site.seo_score = result["seo_score"]
            site.accessibility_score = result["accessibility_score"]
            site.best_practices_score = result["best_practices_score"]
            site.last_pagespeed_check = datetime.utcnow()
            
            db.commit()
            
            logger.info(
                f"✅ PageSpeed audit concluído - {site.domain}: "
                f"Performance {result['performance_score']}/100, "
                f"SEO {result['seo_score']}/100"
            )
            
            # Alerta se performance estiver crítica (<50)
            if result["performance_score"] and result["performance_score"] < 50:
                owner = db.query(User).filter(User.id == site.owner_id).first()
                if owner and owner.telegram_chat_id:
                    message = (
                        f"⚠️ <b>ALERTA - PERFORMANCE CRÍTICA</b>\n\n"
                        f"🌐 <b>Site:</b> {site.name or site.domain}\n"
                        f"🔗 <b>Domínio:</b> {site.domain}\n"
                        f"📊 <b>Score Performance:</b> {result['performance_score']}/100 🔴\n"
                        f"⏰ <b>Horário:</b> {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC\n\n"
                        f"Seu site está lento. Isso afeta SEO e conversões.\n"
                        f"Acesse o dashboard para ver detalhes."
                    )
                    send_telegram_alert(message, owner.telegram_chat_id)
            
            return {
                "success": True,
                "site_id": site_id,
                "domain": site.domain,
                "performance_score": result["performance_score"],
                "seo_score": result["seo_score"],
                "metrics": result["metrics"]
            }
        else:
            logger.error(f"❌ Erro no PageSpeed audit de {site.domain}: {result['error']}")
            return {
                "success": False,
                "site_id": site_id,
                "domain": site.domain,
                "error": result["error"]
            }
    
    except Exception as e:
        logger.error(f"❌ Exceção no PageSpeed audit: {str(e)}")
        # Tenta retry
        raise self.retry(exc=e)
    
    finally:
        db.close()


@celery_app.task
def run_pagespeed_audit_all() -> dict:
    """
    Executa auditoria PageSpeed em TODOS os sites ativos.
    
    Esta task deve rodar apenas 1x por dia (configurar no Celery Beat).
    Agenda auditorias individuais para cada site.
    
    Returns:
        Dict com contagem de auditorias agendadas
    
    Note:
        Com muitos sites, considere fazer em lotes para não estourar
        a quota da API do Google (25k/dia = ~17 sites por hora).
    """
    db = SessionLocal()
    
    try:
        # Busca todos os sites ativos
        sites = db.query(Site).filter(Site.is_active == True).all()
        
        logger.info(f"📋 Agendando PageSpeed audit para {len(sites)} sites")
        
        scheduled = 0
        for site in sites:
            # Agenda auditoria individual com delay progressivo (evita sobrecarga)
            # Delay de 60 segundos entre cada auditoria
            run_pagespeed_audit.apply_async(
                args=[site.id],
                countdown=scheduled * 60  # Espaça as requisições
            )
            scheduled += 1
        
        logger.info(f"✅ {scheduled} auditorias PageSpeed agendadas (1 por minuto)")
        
        return {
            "scheduled": scheduled,
            "total_active": len(sites),
            "estimated_duration_minutes": scheduled
        }
    
    except Exception as e:
        logger.error(f"❌ Erro ao agendar PageSpeed audits: {str(e)}")
        return {"error": str(e)}
    
    finally:
        db.close()


# ============================================
# VISUAL REGRESSION TESTING TASK
# ============================================

@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def visual_check_task(self, site_id: int) -> dict:
    """
    Executa verificação de regressão visual em um site.
    
    Fluxo:
    1. Verifica se já existe baseline - se não, cria uma
    2. Tira screenshot atual
    3. Compara com baseline
    4. Se diff > 5%, marca alerta
    5. Salva estatísticas no banco
    
    Args:
        site_id: ID do site no banco de dados
    
    Returns:
        Dict com resultado da verificação visual
        
    Performance:
        - Timeout total ~40s (30s playwright + 10s processamento)
        - Retry apenas 2x para não sobrecarregar worker
        - Erros de Playwright são tratados graciosamente
    """
    import asyncio
    import os
    from scanner import take_screenshot, compare_images, create_diff_image
    
    db = SessionLocal()
    
    try:
        # Busca o site
        site = db.query(Site).filter(Site.id == site_id).first()
        
        if not site:
            logger.error(f"❌ Site {site_id} não encontrado")
            return {"success": False, "error": "Site não encontrado"}
        
        if not site.is_active:
            logger.info(f"⏸️  Site {site.domain} está desativado - pulando visual check")
            return {"success": False, "error": "Site desativado"}
        
        logger.info(f"📸 Iniciando visual check de {site.domain}")
        
        # Constrói a URL completa
        url = f"https://{site.domain}" if not site.domain.startswith('http') else site.domain
        
        # Verifica se é a primeira vez (sem baseline)
        is_first_run = not site.baseline_screenshot_path or not os.path.exists(
            site.baseline_screenshot_path or ""
        )
        
        if is_first_run:
            logger.info(f"🎯 Primeira execução - criando baseline para {site.domain}")
            
            # Tira screenshot que será o baseline
            baseline_path = asyncio.run(take_screenshot(url, site_id, "baseline"))
            
            if not baseline_path:
                logger.error(f"❌ Falha ao criar baseline para {site.domain}")
                return {
                    "success": False,
                    "error": "Não foi possível capturar screenshot baseline",
                    "site_id": site_id,
                    "domain": site.domain
                }
            
            # Copia para current também (primeira vez são iguais)
            current_path = asyncio.run(take_screenshot(url, site_id, "current"))
            
            # Atualiza banco
            site.baseline_screenshot_path = baseline_path
            site.last_screenshot_path = current_path
            site.visual_diff_percent = 0.0
            site.visual_alert_triggered = False
            site.last_visual_check = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"✅ Baseline criado para {site.domain} - 0% diff")
            
            return {
                "success": True,
                "site_id": site_id,
                "domain": site.domain,
                "first_run": True,
                "baseline_path": baseline_path,
                "diff_percent": 0.0
            }
        
        # NÃO é a primeira vez - compara com baseline
        logger.info(f"🔍 Comparando com baseline existente de {site.domain}")
        
        # Tira screenshot atual
        current_path = asyncio.run(take_screenshot(url, site_id, "current"))
        
        if not current_path:
            logger.error(f"❌ Falha ao capturar screenshot atual de {site.domain}")
            # Retry se for erro temporário
            raise self.retry(exc=Exception("Falha ao capturar screenshot"))
        
        # Compara com baseline
        baseline_path = site.baseline_screenshot_path
        diff_percent = compare_images(baseline_path, current_path)
        
        logger.info(f"📊 Visual diff de {site.domain}: {diff_percent}%")
        
        # Define se deve alertar (threshold de 5%)
        should_alert = diff_percent > 5.0
        
        # Se detectou mudança significativa, cria imagem de diferença para análise
        if should_alert:
            diff_image_path = f"static/screenshots/{site_id}_diff.png"
            create_diff_image(baseline_path, current_path, diff_image_path)
            logger.warning(f"⚠️  ALERTA VISUAL: {site.domain} mudou {diff_percent}%")
            
            # Envia alerta Telegram se configurado
            if site.owner.telegram_chat_id:
                message = (
                    f"🎨 <b>ALERTA DE MUDANÇA VISUAL</b>\n\n"
                    f"🌐 <b>Site:</b> {site.name or site.domain}\n"
                    f"📊 <b>Diferença:</b> {diff_percent}%\n"
                    f"⚠️ <b>Status:</b> Mudança significativa detectada (> 5%)\n\n"
                    f"💡 <b>Ação:</b> Verifique se a mudança foi intencional.\n"
                    f"Se sim, atualize o baseline no dashboard."
                )
                send_telegram_alert(message, site.owner.telegram_chat_id)
        
        # Atualiza banco
        site.last_screenshot_path = current_path
        site.visual_diff_percent = diff_percent
        site.visual_alert_triggered = should_alert
        site.last_visual_check = datetime.utcnow()
        
        db.commit()
        
        status = "ALERTA" if should_alert else "OK"
        logger.info(f"✅ Visual check de {site.domain} concluído - Status: {status}")
        
        return {
            "success": True,
            "site_id": site_id,
            "domain": site.domain,
            "diff_percent": diff_percent,
            "alert_triggered": should_alert,
            "current_path": current_path,
            "baseline_path": baseline_path
        }
    
    except Exception as e:
        logger.error(f"❌ Erro no visual check de site {site_id}: {str(e)}")
        
        # Retry apenas para erros recuperáveis (não para sites que bloqueiam bots)
        if "timeout" in str(e).lower() or "connection" in str(e).lower():
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "error": str(e),
            "site_id": site_id
        }
    
    finally:
        db.close()


@celery_app.task
def visual_check_all_sites() -> dict:
    """
    Agenda visual check para TODOS os sites ativos.
    
    Esta task deve rodar 1x por dia (configurar no Celery Beat).
    
    Returns:
        Dict com contagem de checks agendados
        
    Note:
        Visual checks são mais pesados que health checks.
        Espaça execuções em 5 minutos para não sobrecarregar.
    """
    db = SessionLocal()
    
    try:
        sites = db.query(Site).filter(Site.is_active == True).all()
        
        logger.info(f"📸 Agendando visual check para {len(sites)} sites")
        
        scheduled = 0
        for site in sites:
            # Espaça checks em 5 minutos (300s)
            visual_check_task.apply_async(
                args=[site.id],
                countdown=scheduled * 300
            )
            scheduled += 1
        
        logger.info(f"✅ {scheduled} visual checks agendados (1 a cada 5 min)")
        
        return {
            "scheduled": scheduled,
            "total_active": len(sites),
            "estimated_duration_minutes": scheduled * 5
        }
    
    except Exception as e:
        logger.error(f"❌ Erro ao agendar visual checks: {str(e)}")
        return {"error": str(e)}
    
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def pagespeed_check_task(self, site_id: int) -> dict:
    """
    Executa verificação do Google PageSpeed Insights para um site.
    
    Analisa:
    - Performance Score (LCP, FID, CLS)
    - SEO Score
    - Acessibilidade
    - Melhores Práticas
    
    Args:
        site_id: ID do site no banco de dados
    
    Returns:
        Dict com resultados da análise
        
    Retry Policy:
        - Máximo 2 tentativas
        - Espera 120 segundos entre tentativas (API do Google pode demorar)
        - Timeout de 90s por request
        
    Note:
        A API do Google pode levar 60-90 segundos para processar.
        Este é um processo mais lento que os outros checks.
    """
    db = SessionLocal()
    
    try:
        # Busca o site
        site = db.query(Site).filter(Site.id == site_id).first()
        
        if not site:
            logger.error(f"❌ Site {site_id} não encontrado")
            return {"error": "Site não encontrado"}
        
        if not site.is_active:
            logger.info(f"⏸️ Site {site.domain} está inativo, pulando PageSpeed check")
            return {"message": "Site inativo"}
        
        logger.info(f"🚀 Iniciando PageSpeed check: {site.domain}")
        
        # Executa o check do PageSpeed
        pagespeed_result = check_pagespeed(site.domain)
        
        if pagespeed_result:
            # Salva os dados no banco
            site.performance_score = pagespeed_result.get('performance_score')
            site.seo_score = pagespeed_result.get('seo_score')
            site.accessibility_score = pagespeed_result.get('accessibility_score')
            site.best_practices_score = pagespeed_result.get('best_practices_score')
            site.last_pagespeed_check = datetime.utcnow()
            
            db.commit()
            
            logger.info(
                f"✅ PageSpeed atualizado: {site.domain} - "
                f"Performance: {site.performance_score}, "
                f"SEO: {site.seo_score}, "
                f"A11y: {site.accessibility_score}, "
                f"BP: {site.best_practices_score}"
            )
            
            # Busca o dono do site para notificação
            owner = db.query(User).filter(User.id == site.owner_id).first()
            
            # Envia alerta se performance estiver baixa
            if owner and owner.telegram_chat_id and site.performance_score is not None:
                if site.performance_score < 50:
                    message = (
                        f"⚠️ <b>PERFORMANCE CRÍTICA DETECTADA</b>\n\n"
                        f"🌐 <b>Site:</b> {site.name}\n"
                        f"🔗 <b>URL:</b> https://{site.domain}\n"
                        f"📊 <b>Performance Score:</b> {site.performance_score}/100\n"
                        f"🔍 <b>SEO:</b> {site.seo_score}/100\n"
                        f"♿ <b>Acessibilidade:</b> {site.accessibility_score}/100\n\n"
                        f"<i>Recomenda-se otimizar o site urgentemente.</i>"
                    )
                    send_telegram_alert(message, owner.telegram_chat_id)
                    logger.info(f"📱 Alerta de performance crítica enviado via Telegram")
            
            return {
                "site_id": site_id,
                "domain": site.domain,
                "performance_score": site.performance_score,
                "seo_score": site.seo_score,
                "accessibility_score": site.accessibility_score,
                "best_practices_score": site.best_practices_score,
                "status": "success"
            }
        else:
            logger.warning(f"⚠️ Falha ao obter dados do PageSpeed para {site.domain}")
            return {
                "site_id": site_id,
                "domain": site.domain,
                "status": "failed",
                "error": "Não foi possível obter dados do PageSpeed"
            }
    
    except Exception as e:
        logger.error(f"❌ Erro ao executar PageSpeed check para site {site_id}: {str(e)}")
        
        # Tenta retentar a task
        try:
            raise self.retry(exc=e)
        except Exception as retry_error:
            logger.error(f"❌ Falha após todas as tentativas: {str(retry_error)}")
            return {"error": str(e)}
    
    finally:
        db.close()


@celery_app.task(name="check_heartbeats", bind=True, max_retries=3)
def check_heartbeats(self):
    """
    Verifica todos os heartbeats e detecta os que estão atrasados.
    
    Lógica:
    - Busca heartbeats ativos que já receberam pelo menos 1 ping
    - Verifica se last_ping + expected_period + grace_period < now
    - Se sim, marca como 'down' e envia alerta
    - Se passou apenas o expected_period (mas ainda no grace), marca como 'late'
    - Roda a cada 1 minuto via Celery Beat
    
    Returns:
        Dict com estatísticas da verificação
    """
    from datetime import datetime, timezone, timedelta
    from models import HeartbeatCheck
    
    db = SessionLocal()
    
    try:
        now = datetime.now(timezone.utc)
        
        # Busca todos os heartbeats ativos
        heartbeats = db.query(HeartbeatCheck).filter(
            HeartbeatCheck.is_active == True
        ).all()
        
        stats = {
            "total_checked": len(heartbeats),
            "up": 0,
            "late": 0,
            "down": 0,
            "new": 0,
            "alerts_sent": 0
        }
        
        for hb in heartbeats:
            # Heartbeats novos (sem ping ainda)
            if not hb.last_ping:
                stats["new"] += 1
                continue
            
            # Calcula deadline final (com grace period)
            deadline = hb.last_ping + timedelta(
                seconds=hb.expected_period + hb.grace_period
            )
            
            # Calcula quando fica "late" (sem grace period)
            late_deadline = hb.last_ping + timedelta(
                seconds=hb.expected_period
            )
            
            # Verifica status
            if now > deadline:
                # OVERDUE - Passou do prazo + tolerância = DOWN
                old_status = hb.status
                hb.status = 'down'
                hb.missed_pings += 1
                stats["down"] += 1
                
                # Envia alerta apenas uma vez (quando muda de status)
                if not hb.alert_sent and old_status != 'down':
                    # Busca dono
                    owner = db.query(User).filter(User.id == hb.owner_id).first()
                    
                    if owner and owner.telegram_chat_id:
                        hours_late = int((now - deadline).total_seconds() / 3600)
                        
                        message = (
                            f"🚨 <b>HEARTBEAT PERDIDO</b>\n\n"
                            f"⚠️ <b>Tarefa:</b> {hb.name}\n"
                            f"📋 <b>Descrição:</b> {hb.description or 'N/A'}\n"
                            f"⏰ <b>Último ping:</b> {hb.last_ping.strftime('%d/%m/%Y %H:%M:%S')}\n"
                            f"🕐 <b>Atrasado há:</b> {hours_late}h\n"
                            f"⚙️ <b>Período esperado:</b> {hb.expected_period // 3600}h\n\n"
                            f"💡 <b>Ação:</b> Verifique se o cron job/script está rodando corretamente!\n"
                            f"🔗 <b>URL do ping:</b> /ping/{hb.slug}"
                        )
                        
                        if send_telegram_alert(message, owner.telegram_chat_id):
                            hb.alert_sent = True
                            hb.alert_sent_at = now
                            stats["alerts_sent"] += 1
                            logger.info(f"🚨 Alerta de heartbeat perdido enviado: {hb.name}")
                
            elif now > late_deadline:
                # LATE - Passou do prazo mas ainda dentro da tolerância
                hb.status = 'late'
                stats["late"] += 1
                
            else:
                # UP - Dentro do prazo
                hb.status = 'up'
                stats["up"] += 1
        
        db.commit()
        
        logger.info(
            f"✅ Verificação de heartbeats concluída: "
            f"{stats['up']} up, {stats['late']} late, {stats['down']} down, "
            f"{stats['new']} new, {stats['alerts_sent']} alertas enviados"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar heartbeats: {e}")
        db.rollback()
        raise
    finally:
        db.close()
