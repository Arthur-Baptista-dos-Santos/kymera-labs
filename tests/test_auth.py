"""
Testes do módulo de autenticação JWT.
"""
import pytest
from jose import jwt

from backend.seguranca.auth import (
    autenticar_usuario,
    gerar_token,
    verificar_senha,
    SECRET_KEY,
    ALGORITHM,
)


def test_autenticar_usuario_admin_valido():
    usuario = autenticar_usuario("admin", "kymera2026")
    assert usuario is not None
    assert usuario["papel"] == "admin"


def test_autenticar_usuario_operador_valido():
    usuario = autenticar_usuario("operador", "operador123")
    assert usuario is not None
    assert usuario["papel"] == "operador"


def test_autenticar_usuario_senha_errada():
    usuario = autenticar_usuario("admin", "senha_errada")
    assert usuario is None


def test_autenticar_usuario_inexistente():
    usuario = autenticar_usuario("usuario_que_nao_existe", "qualquer")
    assert usuario is None


def test_autenticar_usuario_strip_espacos():
    usuario = autenticar_usuario(" admin ", " kymera2026 ")
    assert usuario is not None


def test_gerar_token_retorna_string():
    token = gerar_token({"sub": "admin"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_gerar_token_payload_correto():
    token = gerar_token({"sub": "admin"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "admin"
    assert "exp" in payload


def test_verificar_senha_correta():
    import bcrypt
    senha = "teste123"
    hash_ = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    assert verificar_senha(senha, hash_) is True


def test_verificar_senha_incorreta():
    import bcrypt
    hash_ = bcrypt.hashpw("outra_senha".encode(), bcrypt.gensalt()).decode()
    assert verificar_senha("senha_errada", hash_) is False
