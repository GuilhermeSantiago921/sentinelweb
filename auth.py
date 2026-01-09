"""
SentinelWeb - Módulo de Autenticação
====================================
Gerencia autenticação de usuários com JWT tokens.
Inclui funções para hash de senha e verificação.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User
import os
import sys

# ============================================
# CONFIGURAÇÕES DE SEGURANÇA
# ============================================

# SECRET_KEY: OBRIGATÓRIA em produção
# Gere com: python3 -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY = os.getenv("SECRET_KEY")

# Validação de segurança: SECRET_KEY é obrigatória
if not SECRET_KEY:
    print("=" * 80)
    print("🔒 ERRO DE SEGURANÇA: SECRET_KEY não configurada!")
    print("=" * 80)
    print("\n❌ A variável SECRET_KEY é OBRIGATÓRIA para segurança do sistema.")
    print("\n📝 Para gerar uma chave forte, execute:")
    print("   python3 -c \"import secrets; print(secrets.token_urlsafe(64))\"")
    print("\n⚙️  Configure no arquivo .env:")
    print("   SECRET_KEY=sua_chave_gerada_aqui")
    print("\n" + "=" * 80)
    sys.exit(1)

# Validação adicional: SECRET_KEY deve ter comprimento mínimo
if len(SECRET_KEY) < 32:
    print("=" * 80)
    print("🔒 ERRO DE SEGURANÇA: SECRET_KEY muito curta!")
    print("=" * 80)
    print(f"\n❌ SECRET_KEY atual tem {len(SECRET_KEY)} caracteres.")
    print("✅ Mínimo recomendado: 32 caracteres")
    print("✅ Ideal: 64+ caracteres")
    print("\n📝 Gere uma nova chave forte:")
    print("   python3 -c \"import secrets; print(secrets.token_urlsafe(64))\"")
    print("\n" + "=" * 80)
    sys.exit(1)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))  # 24 horas padrão

# Contexto para hash de senhas usando bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde ao hash.
    
    Args:
        plain_password: Senha digitada pelo usuário
        hashed_password: Hash armazenado no banco
    
    Returns:
        True se a senha está correta
    """
    # Bcrypt tem limite de 72 bytes
    password_truncated = plain_password[:72]
    return pwd_context.verify(password_truncated, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera hash bcrypt da senha.
    
    Security Notes:
        - bcrypt é resistente a ataques de força bruta
        - Inclui salt automático
        - Custo computacional ajustável
        - Limite de 72 bytes (truncado automaticamente)
    """
    # Bcrypt tem limite de 72 bytes, truncar para evitar erro
    password_truncated = password[:72]
    return pwd_context.hash(password_truncated)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT para autenticação.
    
    Args:
        data: Dados a incluir no token (ex: user_id)
        expires_delta: Tempo de expiração customizado
    
    Returns:
        Token JWT assinado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decodifica e valida um token JWT.
    
    Args:
        token: Token JWT
    
    Returns:
        Payload do token ou None se inválido
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca usuário por email"""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Autentica usuário por email e senha.
    
    Args:
        db: Sessão do banco
        email: Email do usuário
        password: Senha em texto plano
    
    Returns:
        User se autenticado, None caso contrário
    """
    user = get_user_by_email(db, email)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def get_current_user_from_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Obtém o usuário atual a partir do token JWT.
    Verifica primeiro o cookie, depois o header Authorization.
    
    Este é um dependency do FastAPI usado para proteger rotas.
    """
    token = None
    
    # Primeiro tenta pegar do cookie (para navegador)
    token = request.cookies.get("access_token")
    
    # Se não tiver cookie, tenta header Authorization
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        return None
    
    # Remove "Bearer " se presente
    if token.startswith("Bearer "):
        token = token[7:]
    
    payload = decode_token(token)
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    return user


def get_current_user(
    user: Optional[User] = Depends(get_current_user_from_token)
) -> User:
    """
    Dependency que exige usuário autenticado.
    Retorna 401 se não autenticado.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_user(
    user: Optional[User] = Depends(get_current_user_from_token)
) -> Optional[User]:
    """
    Dependency que retorna usuário se autenticado, None caso contrário.
    Útil para rotas públicas que mostram conteúdo diferente se logado.
    """
    return user
