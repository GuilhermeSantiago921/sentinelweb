#!/usr/bin/env python3
"""
Script de Diagnóstico - Telegram Chat ID
=========================================
Este script ajuda a identificar problemas com a configuração do Telegram.
"""

import os
import sys
import requests

# Carrega token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN não configurado!")
    print()
    print("Configure a variável de ambiente:")
    print("export TELEGRAM_BOT_TOKEN='seu_token_aqui'")
    sys.exit(1)

print("=" * 70)
print("🔍 DIAGNÓSTICO DO TELEGRAM")
print("=" * 70)
print()

# 1. Verifica token
print("1️⃣ Verificando token do bot...")
print(f"   Token: {TELEGRAM_BOT_TOKEN[:10]}...{TELEGRAM_BOT_TOKEN[-10:]}")
print(f"   Tamanho: {len(TELEGRAM_BOT_TOKEN)} caracteres")
print()

# 2. Testa API do Telegram
print("2️⃣ Testando conexão com API do Telegram...")
try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            bot_info = data['result']
            print(f"   ✅ Conectado com sucesso!")
            print(f"   🤖 Bot: @{bot_info['username']}")
            print(f"   📛 Nome: {bot_info['first_name']}")
            print(f"   🆔 Bot ID: {bot_info['id']}")
        else:
            print(f"   ❌ Erro: {data}")
            sys.exit(1)
    else:
        print(f"   ❌ Erro HTTP {response.status_code}: {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Exceção: {e}")
    sys.exit(1)

print()

# 3. Busca mensagens recentes (updates)
print("3️⃣ Buscando mensagens recentes...")
print("   (Envie uma mensagem para o bot agora se ainda não enviou)")
print()

try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            updates = data['result']
            
            if not updates:
                print("   ⚠️  Nenhuma mensagem encontrada!")
                print()
                print("   📝 INSTRUÇÕES:")
                print("   1. Abra o Telegram")
                print("   2. Busque pelo seu bot")
                print("   3. Envie uma mensagem qualquer (ex: /start)")
                print("   4. Execute este script novamente")
                print()
            else:
                print(f"   ✅ {len(updates)} mensagem(ns) encontrada(s)")
                print()
                print("=" * 70)
                print("📨 CHAT IDs ENCONTRADOS:")
                print("=" * 70)
                print()
                
                seen_chats = set()
                
                for update in updates:
                    message = update.get('message', {})
                    chat = message.get('chat', {})
                    from_user = message.get('from', {})
                    
                    chat_id = chat.get('id')
                    chat_type = chat.get('type', 'unknown')
                    
                    if chat_id and chat_id not in seen_chats:
                        seen_chats.add(chat_id)
                        
                        # Identifica se é bot ou usuário
                        is_bot = from_user.get('is_bot', False)
                        first_name = from_user.get('first_name', 'Unknown')
                        username = from_user.get('username', 'sem username')
                        
                        icon = "🤖" if is_bot else "👤"
                        type_label = "BOT" if is_bot else "USUÁRIO"
                        
                        print(f"{icon} {type_label}:")
                        print(f"   Chat ID: {chat_id}")
                        print(f"   Nome: {first_name}")
                        print(f"   Username: @{username}")
                        print(f"   Tipo de chat: {chat_type}")
                        
                        if is_bot:
                            print(f"   ⚠️  ATENÇÃO: Este é um bot! Não use este ID.")
                        else:
                            print(f"   ✅ Use este Chat ID no seu perfil!")
                        
                        print()
                
                print("=" * 70)
                print("📋 RESUMO:")
                print("=" * 70)
                print()
                
                user_chats = []
                bot_chats = []
                
                for update in updates:
                    message = update.get('message', {})
                    from_user = message.get('from', {})
                    chat_id = message.get('chat', {}).get('id')
                    
                    if chat_id:
                        if from_user.get('is_bot', False):
                            if chat_id not in bot_chats:
                                bot_chats.append(chat_id)
                        else:
                            if chat_id not in user_chats:
                                user_chats.append(chat_id)
                
                if user_chats:
                    print("✅ Chat IDs de USUÁRIOS (use um destes):")
                    for chat_id in user_chats:
                        print(f"   → {chat_id}")
                    print()
                
                if bot_chats:
                    print("❌ Chat IDs de BOTS (NÃO use estes):")
                    for chat_id in bot_chats:
                        print(f"   → {chat_id}")
                    print()
                
                print("=" * 70)
                print("🔧 PRÓXIMOS PASSOS:")
                print("=" * 70)
                print()
                print("1. Copie um Chat ID de USUÁRIO (👤) da lista acima")
                print("2. Acesse: http://localhost:8000/profile")
                print("3. Cole o Chat ID no campo 'Telegram Chat ID'")
                print("4. Clique em 'Salvar Alterações'")
                print("5. Clique em 'Enviar mensagem de teste'")
                print()
                print("Se você receber a mensagem no Telegram, está funcionando! 🎉")
                print()
        else:
            print(f"   ❌ Erro: {data}")
    else:
        print(f"   ❌ Erro HTTP {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"   ❌ Exceção: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("✅ Diagnóstico concluído!")
print("=" * 70)
