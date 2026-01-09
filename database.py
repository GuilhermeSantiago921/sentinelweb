"""
SentinelWeb - Configuração do Banco de Dados
============================================
Este módulo configura a conexão com PostgreSQL (produção) ou SQLite (dev).
Suporta pool de conexões e configurações otimizadas.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
import os

# URL do banco de dados
# Produção: postgresql://user:password@host:port/database
# Desenvolvimento: sqlite:///./sentinelweb.db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentinelweb.db")

# Configuração específica por tipo de banco
if DATABASE_URL.startswith("sqlite"):
    # SQLite - Desenvolvimento
    # check_same_thread=False permite uso com múltiplas threads (necessário para FastAPI)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,  # SQLite não precisa de pool
        echo=False  # Mude para True para debug de queries SQL
    )
    print("📦 Usando SQLite (Desenvolvimento)")
    
elif DATABASE_URL.startswith("postgresql"):
    # PostgreSQL - Produção
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,  # Conexões simultâneas no pool
        max_overflow=40,  # Conexões extras em picos
        pool_timeout=30,  # Timeout para obter conexão
        pool_recycle=3600,  # Recicla conexões a cada 1h
        pool_pre_ping=True,  # Verifica conexão antes de usar
        echo=False,
        connect_args={
            "connect_timeout": 10,
            "options": "-c timezone=utc"
        }
    )
    print("🐘 Usando PostgreSQL (Produção)")
    
else:
    raise ValueError(
        f"Tipo de banco não suportado: {DATABASE_URL.split(':')[0]}\n"
        "Use: postgresql://... ou sqlite:///..."
    )

# SessionLocal: Fábrica de sessões do banco
# autocommit=False: Transações manuais para maior controle
# autoflush=False: Evita flush automático, melhor performance
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos ORM
Base = declarative_base()


def get_db():
    """
    Dependency Injection para FastAPI.
    Garante que a sessão do banco seja fechada após cada request.
    
    Uso:
        @app.get("/")
        def route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas.
    Chamado na inicialização da aplicação.
    """
    from models import User, Site, MonitorLog  # Import aqui para evitar circular import
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados inicializado com sucesso!")
