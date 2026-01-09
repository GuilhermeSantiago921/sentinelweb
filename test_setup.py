"""
Script de Teste - SentinelWeb
=============================
Execute este script para validar que tudo está funcionando.
"""

import sys
import subprocess
import socket
import time

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def check_command(command):
    """Verifica se um comando existe"""
    try:
        subprocess.run([command, "--version"], 
                      capture_output=True, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_port(port, host='localhost'):
    """Verifica se uma porta está aberta"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def main():
    print_header("🛡️  SENTINELWEB - TESTE DE AMBIENTE")
    
    errors = []
    warnings = []
    
    # 1. Verifica Python
    print("✅ Python:")
    print(f"   Versão: {sys.version}")
    if sys.version_info < (3, 11):
        warnings.append("Python 3.11+ recomendado")
    
    # 2. Verifica dependências
    print("\n📦 Verificando dependências Python...")
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'celery',
        'redis',
        'httpx',
        'jinja2',
        'pydantic'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} não encontrado")
            errors.append(f"{package} não instalado")
    
    # 3. Verifica Redis
    print("\n🔴 Verificando Redis...")
    if check_port(6379):
        print("   ✅ Redis está rodando na porta 6379")
    else:
        print("   ❌ Redis não está rodando")
        errors.append("Redis não está ativo. Instale e inicie o Redis.")
    
    # 4. Verifica arquivos do projeto
    print("\n📁 Verificando arquivos do projeto...")
    required_files = [
        'main.py',
        'database.py',
        'models.py',
        'schemas.py',
        'scanner.py',
        'tasks.py',
        'celery_app.py',
        'auth.py',
        'requirements.txt',
        'docker-compose.yml'
    ]
    
    import os
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} não encontrado")
            errors.append(f"Arquivo {file} ausente")
    
    # 5. Testa o scanner
    print("\n🔍 Testando Scanner...")
    try:
        from scanner import full_scan
        result = full_scan("google.com")
        
        if result.is_online:
            print("   ✅ Scanner funcionando!")
            print(f"   → Status: Online")
            print(f"   → Latência: {result.latency_ms}ms")
            print(f"   → SSL: {'Válido' if result.ssl_valid else 'Inválido'}")
        else:
            warnings.append("Scanner retornou offline para google.com (pode ser firewall)")
            
    except Exception as e:
        print(f"   ❌ Erro ao testar scanner: {e}")
        errors.append(f"Scanner falhou: {e}")
    
    # 6. Verifica banco de dados
    print("\n💾 Verificando Banco de Dados...")
    try:
        from database import init_db, engine
        from sqlalchemy import inspect
        
        init_db()
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['users', 'sites', 'monitor_logs']
        for table in expected_tables:
            if table in tables:
                print(f"   ✅ Tabela '{table}' existe")
            else:
                print(f"   ⚠️  Tabela '{table}' será criada")
                
    except Exception as e:
        print(f"   ❌ Erro no banco: {e}")
        errors.append(f"Banco de dados falhou: {e}")
    
    # Resultado Final
    print_header("📊 RESULTADO DO TESTE")
    
    if errors:
        print("❌ ERROS ENCONTRADOS:")
        for error in errors:
            print(f"   • {error}")
        print("\n⚠️  Corrija os erros acima antes de continuar.")
        return False
    
    if warnings:
        print("⚠️  AVISOS:")
        for warning in warnings:
            print(f"   • {warning}")
    
    print("\n✅ TODOS OS TESTES PASSARAM!")
    print("\n🚀 Próximos passos:")
    print("   1. Inicie a aplicação:")
    print("      → uvicorn main:app --reload")
    print("   2. Inicie o Celery Worker:")
    print("      → celery -A celery_app worker --loglevel=info")
    print("   3. Inicie o Celery Beat:")
    print("      → celery -A celery_app beat --loglevel=info")
    print("   4. Acesse: http://localhost:8000")
    print("\n   Ou use Docker: docker-compose up --build")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")
        sys.exit(1)
