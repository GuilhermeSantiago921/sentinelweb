#!/usr/bin/env python3
"""
Migração para adicionar tabela de Heartbeat Monitoring.

Execução:
    docker-compose exec web python migrate_heartbeat.py
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL
import sys

def migrate():
    """Cria a tabela heartbeat_checks"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Primeiro dropa a tabela se existir (para recriar do zero)
            try:
                conn.execute(text("DROP TABLE IF EXISTS heartbeat_checks"))
                print("🗑️  Tabela antiga removida")
            except:
                pass
            
            # Cria tabela heartbeat_checks do zero
            conn.execute(text("""
                CREATE TABLE heartbeat_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug VARCHAR(100) NOT NULL UNIQUE,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    expected_period INTEGER NOT NULL,
                    grace_period INTEGER DEFAULT 3600,
                    status VARCHAR(20) DEFAULT 'new',
                    last_ping DATETIME,
                    next_expected_ping DATETIME,
                    alert_sent BOOLEAN DEFAULT 0,
                    alert_sent_at DATETIME,
                    total_pings INTEGER DEFAULT 0,
                    missed_pings INTEGER DEFAULT 0,
                    owner_id INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # Cria índices para performance
            conn.execute(text("CREATE INDEX idx_heartbeat_slug ON heartbeat_checks(slug)"))
            conn.execute(text("CREATE INDEX idx_heartbeat_owner ON heartbeat_checks(owner_id)"))
            conn.execute(text("CREATE INDEX idx_heartbeat_status ON heartbeat_checks(status)"))
            conn.execute(text("CREATE INDEX idx_heartbeat_active ON heartbeat_checks(is_active)"))
            
            conn.commit()
            print("✅ Tabela heartbeat_checks criada com sucesso!")
            print("✅ Índices criados para otimização de queries!")
            return True
            
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
