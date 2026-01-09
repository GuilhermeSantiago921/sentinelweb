"""
Migração: Cria tabelas do Módulo Financeiro

Adiciona:
- system_config: Configurações globais do sistema (Singleton)
- payments: Registro de pagamentos/cobranças do Asaas
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "sentinelweb.db"


def migrate():
    """Executa a migração para criar tabelas financeiras"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("🔧 Iniciando migração: Módulo Financeiro (Asaas)...")
        
        # 1. Cria tabela system_config
        print("  ➕ Criando tabela: system_config...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asaas_api_token TEXT,
                asaas_webhook_secret VARCHAR(255),
                is_sandbox BOOLEAN NOT NULL DEFAULT 1,
                plan_free_price REAL NOT NULL DEFAULT 0.0,
                plan_pro_price REAL NOT NULL DEFAULT 49.0,
                plan_agency_price REAL NOT NULL DEFAULT 149.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """)
        print("  ✅ system_config criada")
        
        # 2. Insere configuração inicial (Singleton)
        cursor.execute("SELECT COUNT(*) FROM system_config")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("  ➕ Inserindo configuração inicial...")
            cursor.execute("""
                INSERT INTO system_config (is_sandbox, plan_free_price, plan_pro_price, plan_agency_price)
                VALUES (1, 0.0, 49.0, 149.0)
            """)
            print("  ✅ Configuração inicial inserida")
        else:
            print("  ⏭️  Configuração inicial já existe")
        
        # 3. Cria tabela payments
        print("  ➕ Criando tabela: payments...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                asaas_id VARCHAR(255) NOT NULL UNIQUE,
                asaas_customer_id VARCHAR(255),
                value REAL NOT NULL,
                description VARCHAR(500),
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                billing_type VARCHAR(50) NOT NULL DEFAULT 'boleto',
                due_date DATETIME NOT NULL,
                payment_date DATETIME,
                confirmed_date DATETIME,
                invoice_url VARCHAR(500),
                bank_slip_url VARCHAR(500),
                invoice_number VARCHAR(100),
                external_reference VARCHAR(255),
                original_value REAL,
                interest_value REAL DEFAULT 0.0,
                discount_value REAL DEFAULT 0.0,
                net_value REAL,
                pix_qr_code TEXT,
                pix_copy_paste TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        print("  ✅ payments criada")
        
        # 4. Cria índices para performance
        print("  ➕ Criando índices...")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_payments_user_id 
            ON payments(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_payments_asaas_id 
            ON payments(asaas_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_payments_status 
            ON payments(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_payments_due_date 
            ON payments(due_date)
        """)
        
        print("  ✅ 4 índices criados")
        
        # Commit das mudanças
        conn.commit()
        print("\n✨ Migração concluída com sucesso!")
        print("📊 Tabelas criadas:")
        print("   • system_config (Singleton para configurações)")
        print("   • payments (Registro de cobranças)")
        print("🔐 4 índices criados para performance")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro durante migração: {e}")
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
