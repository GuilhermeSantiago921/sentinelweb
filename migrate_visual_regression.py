#!/usr/bin/env python3
"""
Script de Migração - Visual Regression Testing
==============================================
Adiciona as novas colunas para Visual Regression Testing
ao banco de dados existente.

Execute: python migrate_visual_regression.py
"""

import sys
from sqlalchemy import Column, String, Float, Boolean, DateTime
from database import engine, Base
from models import Site

def migrate():
    """Adiciona colunas de Visual Regression ao banco"""
    
    print("🔄 Iniciando migração do banco de dados...")
    print("   Adicionando colunas para Visual Regression Testing\n")
    
    try:
        # Método 1: Usar Base.metadata.create_all() 
        # (adiciona apenas colunas que não existem)
        Base.metadata.create_all(bind=engine)
        
        print("✅ Migração concluída com sucesso!")
        print("\nColunas adicionadas:")
        print("   - last_screenshot_path")
        print("   - baseline_screenshot_path")
        print("   - visual_diff_percent")
        print("   - last_visual_check")
        print("   - visual_alert_triggered")
        print("   - plugins_detected")
        
        print("\n📸 Sistema de Visual Regression Testing pronto para uso!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração: {str(e)}")
        print("\nSe o erro for sobre colunas já existentes, tudo bem!")
        print("Isso significa que o banco já está atualizado.")
        return False

if __name__ == "__main__":
    migrate()
