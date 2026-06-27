"""
Autenticação JWT com bcrypt.
Gera e valida tokens de acesso para a API Kymera Labs.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "kymera_dev_secret_troque_em_producao")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


# Usuários em memória para demo - em produção usar PostgreSQL
USUARIOS_DEMO = {
    "admin": {
        "username": "admin",
        "senha_hash": _hash("kymera2026"),
        "papel": "admin",
    },
    "operador": {
        "username": "operador",
        "senha_hash": _hash("operador123"),
        "papel": "operador",
    },
}


def verificar_senha(senha: str, hash_: str) -> bool:
    return bcrypt.checkpw(senha.encode(), hash_.encode())


def gerar_token(dados: dict, expira_em: Optional[timedelta] = None) -> str:
    payload = dados.copy()
    expiracao = datetime.now(timezone.utc) + (expira_em or timedelta(minutes=EXPIRE_MINUTES))
    payload.update({"exp": expiracao})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def autenticar_usuario(username: str, senha: str) -> Optional[dict]:
    usuario = USUARIOS_DEMO.get(username.strip())
    if not usuario:
        return None
    if not verificar_senha(senha.strip(), usuario["senha_hash"]):
        return None
    return usuario


async def usuario_atual(token: str = Depends(oauth2_scheme)) -> dict:
    """Dependency do FastAPI - valida o JWT em cada request protegido."""
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credenciais_invalidas
    except JWTError:
        raise credenciais_invalidas

    usuario = USUARIOS_DEMO.get(username)
    if usuario is None:
        raise credenciais_invalidas
    return usuario
