"""
Testes de integração da API FastAPI.
Usa TestClient do FastAPI (sem servidor real).
"""
import pytest
from fastapi.testclient import TestClient

from backend.api.app import app

client = TestClient(app)


def _token_admin() -> str:
    r = client.post("/auth/login", data={"username": "admin", "password": "kymera2026"})
    return r.json()["access_token"]


def _headers_admin() -> dict:
    return {"Authorization": f"Bearer {_token_admin()}"}


# ── Auth ───────────────────────────────────────────────────────────────────────

def test_login_admin_retorna_200():
    r = client.post("/auth/login", data={"username": "admin", "password": "kymera2026"})
    assert r.status_code == 200
    dados = r.json()
    assert "access_token" in dados
    assert dados["token_type"] == "bearer"
    assert dados["username"] == "admin"
    assert dados["papel"] == "admin"


def test_login_credenciais_invalidas_retorna_401():
    r = client.post("/auth/login", data={"username": "admin", "password": "errada"})
    assert r.status_code == 401


def test_login_operador_retorna_200():
    r = client.post("/auth/login", data={"username": "operador", "password": "operador123"})
    assert r.status_code == 200
    assert r.json()["papel"] == "operador"


# ── Health ─────────────────────────────────────────────────────────────────────

def test_health_retorna_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Endpoints protegidos sem token ─────────────────────────────────────────────

def test_rul_sem_token_retorna_401():
    r = client.get("/motores/1/rul")
    assert r.status_code == 401


def test_anomalia_sem_token_retorna_401():
    r = client.get("/motores/1/anomalia")
    assert r.status_code == 401


def test_frota_sem_token_retorna_401():
    r = client.get("/frota/status")
    assert r.status_code == 401


def test_agente_sem_token_retorna_401():
    r = client.post("/agente/consultar", json={"pergunta": "teste"})
    assert r.status_code == 401


# ── Endpoints com token ────────────────────────────────────────────────────────

def test_rul_motor_valido_retorna_200():
    r = client.get("/motores/1/rul", headers=_headers_admin())
    assert r.status_code == 200
    dados = r.json()
    assert "rul_previsto" in dados
    assert "ciclo_atual" in dados
    assert "status" in dados
    assert dados["status"] in ["normal", "atencao", "alerta", "critico"]


def test_rul_motor_invalido_retorna_404():
    r = client.get("/motores/9999/rul", headers=_headers_admin())
    assert r.status_code == 404


def test_anomalia_motor_valido_retorna_200():
    r = client.get("/motores/1/anomalia", headers=_headers_admin())
    assert r.status_code == 200
    dados = r.json()
    assert "is_anomalia" in dados
    assert "score" in dados
    assert isinstance(dados["is_anomalia"], bool)


def test_frota_status_retorna_200():
    r = client.get("/frota/status", headers=_headers_admin())
    assert r.status_code == 200
    dados = r.json()
    assert "total" in dados
    assert "resumo" in dados
    assert dados["total"] > 0
