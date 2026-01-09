"""
Migração: Adiciona campos de Tech Stack e Segurança Geral na tabela sites

Adiciona:
- tech_stack (TEXT): Tecnologias detectadas (JSON)
- security_headers_grade (VARCHAR(1)): Nota dos headers de segurança
- general_vulnerabilities (TEXT): CVEs encontrados (JSON)
- last_tech_scan (DATETIME): Timestamp da última varredura
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "sentinelweb.db"


def migrate():
    """Executa a migração para adicionar campos de tech stack"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("🔧 Iniciando migração: Tech Stack & Security Scanner...")
        
        # Verifica se as colunas já existem
        cursor.execute("PRAGMA table_info(sites)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 1. Adiciona coluna tech_stack
        if 'tech_stack' not in columns:
            print("  ➕ Adicionando coluna: tech_stack...")
            cursor.execute("""
                ALTER TABLE sites 
                ADD COLUMN tech_stack TEXT
            """)
            print("  ✅ tech_stack adicionada")
        else:
            print("  ⏭️  tech_stack já existe")
        
        # 2. Adiciona coluna security_headers_grade
        if 'security_headers_grade' not in columns:
            print("  ➕ Adicionando coluna: security_headers_grade...")
            cursor.execute("""
                ALTER TABLE sites 
                ADD COLUMN security_headers_grade VARCHAR(1)
            """)
            print("  ✅ security_headers_grade adicionada")
        else:
            print("  ⏭️  security_headers_grade já existe")
        
        # 3. Adiciona coluna general_vulnerabilities
        if 'general_vulnerabilities' not in columns:
            print("  ➕ Adicionando coluna: general_vulnerabilities...")
            cursor.execute("""
                ALTER TABLE sites 
                ADD COLUMN general_vulnerabilities TEXT
            """)
            print("  ✅ general_vulnerabilities adicionada")
        else:
            print("  ⏭️  general_vulnerabilities já existe")
        
        # 4. Adiciona coluna last_tech_scan
        if 'last_tech_scan' not in columns:
            print("  ➕ Adicionando coluna: last_tech_scan...")
            cursor.execute("""
                ALTER TABLE sites 
                ADD COLUMN last_tech_scan DATETIME
            """)
            print("  ✅ last_tech_scan adicionada")
        else:
            print("  ⏭️  last_tech_scan já existe")
        
        # Commit das mudanças
        conn.commit()
        print("\n✨ Migração concluída com sucesso!")
        print("📊 Novos campos disponíveis para General Tech Stack & Security Scanner")
        
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
