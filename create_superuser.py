#!/usr/bin/env python3
"""
Script para criar o primeiro superusuário (admin) do SentinelWeb.

Uso:
    python create_superuser.py

Ou dentro do Docker:
    docker-compose exec web python create_superuser.py
"""

import sys
from getpass import getpass
from database import SessionLocal
from models import User
from auth import get_password_hash


def create_superuser():
    """Cria um superusuário interativamente"""
    
    print("\n" + "="*50)
    print("  SENTINELWEB - Criar Superusuário (Admin)")
    print("="*50 + "\n")
    
    db = SessionLocal()
    
    try:
        # Input de email
        while True:
            email = input("Email do administrador: ").strip()
            if not email:
                print("❌ Email não pode ser vazio!")
                continue
            
            if "@" not in email:
                print("❌ Email inválido!")
                continue
            
            # Verifica se já existe
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                print(f"❌ Já existe um usuário com o email '{email}'!")
                continue
            
            break
        
        # Input de senha
        while True:
            password = getpass("Senha (mínimo 6 caracteres): ")
            if len(password) < 6:
                print("❌ A senha deve ter no mínimo 6 caracteres!")
                continue
            
            password_confirm = getpass("Confirme a senha: ")
            if password != password_confirm:
                print("❌ As senhas não coincidem!")
                continue
            
            break
        
        # Input de empresa (opcional)
        company_name = input("Nome da empresa (opcional): ").strip() or "Admin"
        
        # Cria o superusuário
        hashed_password = get_password_hash(password)
        admin = User(
            email=email,
            hashed_password=hashed_password,
            company_name=company_name,
            is_superuser=True,
            is_active=True,
            plan_status='agency'  # Admin tem acesso total
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("\n" + "="*50)
        print("✅ SUPERUSUÁRIO CRIADO COM SUCESSO!")
        print("="*50)
        print(f"\n📧 Email: {admin.email}")
        print(f"🏢 Empresa: {admin.company_name}")
        print(f"🆔 ID: {admin.id}")
        print(f"👑 Tipo: Superadmin (acesso total)")
        print(f"\n🔗 Acesse: http://localhost:8000/login")
        print(f"🔗 Admin Panel: http://localhost:8000/admin")
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro ao criar superusuário: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_superuser()
