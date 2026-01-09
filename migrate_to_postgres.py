#!/usr/bin/env python3
"""
SentinelWeb - Migração de SQLite para PostgreSQL
================================================
Script para migrar dados do banco SQLite local para PostgreSQL de produção.

Uso:
    python migrate_to_postgres.py

Pré-requisitos:
    - DATABASE_URL configurada para PostgreSQL no .env
    - SQLite database (sentinelweb.db) no diretório atual
    - Tabelas criadas no PostgreSQL (rodar Base.metadata.create_all())
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Site, SiteCheck, HeartbeatCheck, HeartbeatPing, Payment, SystemConfig
from datetime import datetime

# ============================================
# CONFIGURAÇÃO
# ============================================

SQLITE_PATH = "sqlite:///./sentinelweb.db"
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL:
    print("❌ DATABASE_URL não configurada no .env")
    print("Configure: DATABASE_URL=postgresql://user:pass@host:port/db")
    sys.exit(1)

if not POSTGRES_URL.startswith("postgresql"):
    print("❌ DATABASE_URL não é PostgreSQL")
    print(f"Atual: {POSTGRES_URL}")
    sys.exit(1)

# ============================================
# ENGINES E SESSIONS
# ============================================

print("🔧 Conectando aos bancos de dados...")

# SQLite (origem)
sqlite_engine = create_engine(SQLITE_PATH, echo=False)
SQLiteSession = sessionmaker(bind=sqlite_engine)
sqlite_session = SQLiteSession()

# PostgreSQL (destino)
postgres_engine = create_engine(POSTGRES_URL, echo=False)
PostgresSession = sessionmaker(bind=postgres_engine)
postgres_session = PostgresSession()

print("✅ Conexões estabelecidas")

# ============================================
# VERIFICAÇÃO DE TABELAS
# ============================================

print("\n🔍 Verificando estrutura do PostgreSQL...")

try:
    # Cria todas as tabelas se não existirem
    Base.metadata.create_all(bind=postgres_engine)
    print("✅ Tabelas verificadas/criadas")
except Exception as e:
    print(f"❌ Erro ao criar tabelas: {e}")
    sys.exit(1)

# ============================================
# FUNÇÕES DE MIGRAÇÃO
# ============================================

def migrate_model(model_class, name):
    """
    Migra todos os registros de um modelo específico.
    
    Args:
        model_class: Classe do modelo SQLAlchemy
        name: Nome legível do modelo para logs
    
    Returns:
        int: Número de registros migrados
    """
    print(f"\n📦 Migrando {name}...")
    
    try:
        # Busca todos os registros do SQLite
        records = sqlite_session.query(model_class).all()
        count = len(records)
        
        if count == 0:
            print(f"   ℹ️  Nenhum registro encontrado")
            return 0
        
        print(f"   📊 {count} registros encontrados")
        
        # Adiciona ao PostgreSQL
        migrated = 0
        for record in records:
            try:
                # Expunge do SQLite session
                sqlite_session.expunge(record)
                
                # Remove o ID para que o PostgreSQL gere um novo
                if hasattr(record, 'id'):
                    record.id = None
                
                # Adiciona ao PostgreSQL
                postgres_session.add(record)
                migrated += 1
                
                # Commit a cada 100 registros
                if migrated % 100 == 0:
                    postgres_session.commit()
                    print(f"   ✓ {migrated}/{count} migrados...")
                    
            except Exception as e:
                print(f"   ⚠️  Erro ao migrar registro: {e}")
                postgres_session.rollback()
                continue
        
        # Commit final
        postgres_session.commit()
        print(f"   ✅ {migrated} registros migrados com sucesso")
        
        return migrated
        
    except Exception as e:
        print(f"   ❌ Erro na migração: {e}")
        postgres_session.rollback()
        return 0

# ============================================
# MIGRAÇÃO ORDENADA
# ============================================

print("\n" + "="*60)
print("INÍCIO DA MIGRAÇÃO")
print("="*60)

start_time = datetime.now()
total_migrated = 0

# Ordem de migração (respeitando foreign keys)
migrations = [
    (User, "Usuários"),
    (SystemConfig, "Configurações do Sistema"),
    (Site, "Sites Monitorados"),
    (SiteCheck, "Verificações de Sites"),
    (HeartbeatCheck, "Heartbeat Checks"),
    (HeartbeatPing, "Heartbeat Pings"),
    (Payment, "Pagamentos"),
]

for model, name in migrations:
    migrated = migrate_model(model, name)
    total_migrated += migrated

# ============================================
# ATUALIZAÇÃO DE SEQUENCES (PostgreSQL)
# ============================================

print("\n🔧 Atualizando sequences do PostgreSQL...")

try:
    # Atualiza sequences para evitar conflitos de ID
    sequences = [
        'users_id_seq',
        'sites_id_seq',
        'site_checks_id_seq',
        'heartbeat_checks_id_seq',
        'heartbeat_pings_id_seq',
        'payments_id_seq',
        'system_config_id_seq',
    ]
    
    for seq in sequences:
        try:
            table_name = seq.replace('_id_seq', '')
            postgres_session.execute(f"""
                SELECT setval('{seq}', 
                    COALESCE((SELECT MAX(id) FROM {table_name}), 1), 
                    true
                )
            """)
        except Exception as e:
            print(f"   ⚠️  Erro ao atualizar {seq}: {e}")
    
    postgres_session.commit()
    print("✅ Sequences atualizadas")
    
except Exception as e:
    print(f"❌ Erro ao atualizar sequences: {e}")
    postgres_session.rollback()

# ============================================
# VERIFICAÇÃO PÓS-MIGRAÇÃO
# ============================================

print("\n🔍 Verificando migração...")

verification_passed = True

for model, name in migrations:
    try:
        sqlite_count = sqlite_session.query(model).count()
        postgres_count = postgres_session.query(model).count()
        
        status = "✅" if sqlite_count == postgres_count else "⚠️"
        print(f"   {status} {name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
        
        if sqlite_count != postgres_count:
            verification_passed = False
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar {name}: {e}")
        verification_passed = False

# ============================================
# RESUMO FINAL
# ============================================

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print("\n" + "="*60)
print("RESUMO DA MIGRAÇÃO")
print("="*60)
print(f"⏱️  Tempo total: {duration:.2f} segundos")
print(f"📦 Registros migrados: {total_migrated}")

if verification_passed:
    print("\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("\n📝 Próximos passos:")
    print("   1. Verifique os dados no PostgreSQL")
    print("   2. Teste a aplicação")
    print("   3. Faça backup do SQLite (sentinelweb.db)")
    print("   4. Configure DATABASE_URL permanentemente")
    print("   5. Remova ou arquive sentinelweb.db")
else:
    print("\n⚠️  MIGRAÇÃO COMPLETADA COM AVISOS")
    print("   Verifique as diferenças de contagem acima")
    print("   Alguns registros podem não ter sido migrados")

print("\n🔒 Lembre-se:")
print("   - Mantenha backup do SQLite")
print("   - Teste todas as funcionalidades")
print("   - Configure backups automáticos do PostgreSQL")

print("\n" + "="*60 + "\n")

# Fecha conexões
sqlite_session.close()
postgres_session.close()

sys.exit(0 if verification_passed else 1)
