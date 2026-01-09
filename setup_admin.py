#!/usr/bin/env python3
"""
SentinelWeb - Setup do Painel Administrativo
============================================
Cria o primeiro superusuário para acessar o /admin.

Execute este script após instalar as dependências:
    python setup_admin.py
"""

import sys
import os
from getpass import getpass

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models import User, SystemConfig
from auth import get_password_hash


def create_superuser():
    """Cria o primeiro superusuário"""
    print("=" * 60)
    print("   SENTINELWEB - SETUP DO PAINEL ADMINISTRATIVO")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    
    try:
        # Verifica se já existe algum superuser
        existing_super = db.query(User).filter(User.is_superuser == True).first()
        
        if existing_super:
            print("⚠️  Já existe um superusuário cadastrado:")
            print(f"   Email: {existing_super.email}")
            print()
            choice = input("Deseja criar outro? (s/N): ").strip().lower()
            if choice != 's':
                print("\n✅ Setup cancelado.")
                return
        
        print("\n📝 Preencha os dados do superusuário:\n")
        
        # Coleta dados
        email = input("Email: ").strip()
        
        # Valida email
        if not email or '@' not in email:
            print("❌ Email inválido!")
            return
        
        # Verifica se já existe
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ Já existe um usuário com o email {email}")
            
            if not existing_user.is_superuser:
                choice = input("   Deseja torná-lo superusuário? (s/N): ").strip().lower()
                if choice == 's':
                    existing_user.is_superuser = True
                    db.commit()
                    print(f"\n✅ {email} agora é superusuário!")
            return
        
        company_name = input("Nome da Empresa: ").strip() or "Admin"
        
        password = getpass("Senha: ")
        password_confirm = getpass("Confirme a senha: ")
        
        if password != password_confirm:
            print("❌ As senhas não coincidem!")
            return
        
        if len(password) < 8:
            print("❌ A senha deve ter pelo menos 8 caracteres!")
            return
        
        # Cria o superuser
        superuser = User(
            email=email,
            company_name=company_name,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=True,
            plan_status='agency'  # Superusers têm acesso completo
        )
        
        db.add(superuser)
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ SUPERUSUÁRIO CRIADO COM SUCESSO!")
        print("=" * 60)
        print(f"\n📧 Email: {email}")
        print(f"👑 Permissão: Superusuário")
        print(f"\n🔗 Acesse o painel em: http://localhost:8000/admin")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro ao criar superusuário: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def ensure_system_config():
    """Garante que existe uma config do sistema"""
    db = SessionLocal()
    
    try:
        config = db.query(SystemConfig).first()
        
        if not config:
            print("\n📦 Criando configuração padrão do sistema...")
            
            config = SystemConfig(
                plan_free_price=0.0,
                plan_pro_price=49.0,
                plan_agency_price=149.0,
                asaas_api_key=os.getenv("ASAAS_API_KEY", ""),
                telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "")
            )
            
            db.add(config)
            db.commit()
            
            print("✅ Configuração criada!")
        
    except Exception as e:
        print(f"⚠️  Erro ao criar config: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🚀 Iniciando setup do painel administrativo...\n")
    
    # Garante config do sistema
    ensure_system_config()
    
    # Cria superuser
    create_superuser()
    
    print("\n✨ Setup concluído!\n")
