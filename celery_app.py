"""
SentinelWeb - Configuração do Celery
====================================
Configura o Celery para processamento de tarefas em background.
O Redis é usado como message broker.
"""

from celery import Celery
import os

# URL do Redis - pode ser configurada via variável de ambiente
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Cria a instância do Celery
celery_app = Celery(
    "sentinelweb",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"]  # Módulo que contém as tasks
)

# Configurações do Celery
celery_app.conf.update(
    # Serialização
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="America/Sao_Paulo",
    enable_utc=True,
    
    # Configurações de retry
    task_acks_late=True,  # Confirma task só após completar
    task_reject_on_worker_lost=True,
    
    # Limites
    task_time_limit=300,  # 5 minutos máximo por task
    task_soft_time_limit=240,  # Warning em 4 minutos
    
    # Worker
    worker_prefetch_multiplier=1,  # Processa uma task por vez
    worker_concurrency=4,  # 4 workers paralelos
    
    # Beat Schedule (Tarefas Periódicas)
    beat_schedule={
        # Scan de uptime a cada 5 minutos
        "scan-all-sites-every-5-minutes": {
            "task": "tasks.scan_all_sites",
            "schedule": 300.0,  # 5 minutos em segundos
        },
        
        # PageSpeed Audit 1x por dia às 3h da manhã
        "pagespeed-audit-daily": {
            "task": "tasks.run_pagespeed_audit_all",
            "schedule": __import__('celery.schedules', fromlist=['crontab']).crontab(hour=3, minute=0),
        },
        
        # Verificação de Heartbeats a cada 1 minuto
        "check-heartbeats-every-minute": {
            "task": "check_heartbeats",
            "schedule": 60.0,  # 1 minuto em segundos
        },
    },
)
