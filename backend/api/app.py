"""
API principal da Kymera Labs.
FastAPI com autenticação JWT, endpoints REST e WebSocket para sensores em tempo real.
"""
import asyncio
import json
import random
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

from backend.seguranca.auth import autenticar_usuario, gerar_token, usuario_atual
from backend.ml.preditor import prever_rul, detectar_anomalia
from backend.agente.roteador import consultar

DIR_DADOS = Path(__file__).parent.parent.parent / "dados" / "raw"

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Kymera Labs API iniciando...")
    yield
    print("Kymera Labs API encerrando...")


app = FastAPI(
    title="Kymera Labs API",
    description="Plataforma de Manutenção Preditiva Industrial com IA",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ────────────────────────────────────────────────────────────────────

class TokenResposta(BaseModel):
    access_token: str
    token_type: str
    username: str
    papel: str


class ConsultaRequest(BaseModel):
    pergunta: str


class ConsultaResposta(BaseModel):
    pergunta: str
    resposta: str


# ── Auth ───────────────────────────────────────────────────────────────────────

@app.post("/auth/login", response_model=TokenResposta, tags=["Autenticação"])
async def login(form: OAuth2PasswordRequestForm = Depends()):
    usuario = autenticar_usuario(form.username, form.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos.",
        )
    token = gerar_token({"sub": usuario["username"]})
    return TokenResposta(
        access_token=token,
        token_type="bearer",
        username=usuario["username"],
        papel=usuario["papel"],
    )


# ── Motores ────────────────────────────────────────────────────────────────────

@app.get("/motores/{motor_id}/rul", tags=["Motores"])
@limiter.limit("30/minute")
async def get_rul(
    request: Request,
    motor_id: int,
    usuario: dict = Depends(usuario_atual),
):
    df = pd.read_csv(DIR_DADOS / "teste.csv")
    df_motor = df[df["motor_id"] == motor_id]
    if df_motor.empty:
        df = pd.read_csv(DIR_DADOS / "treino.csv")
        df_motor = df[df["motor_id"] == motor_id]
    if df_motor.empty:
        raise HTTPException(status_code=404, detail=f"Motor {motor_id} não encontrado.")
    return prever_rul(df_motor)


@app.get("/motores/{motor_id}/anomalia", tags=["Motores"])
@limiter.limit("30/minute")
async def get_anomalia(
    request: Request,
    motor_id: int,
    usuario: dict = Depends(usuario_atual),
):
    df = pd.read_csv(DIR_DADOS / "teste.csv")
    df_motor = df[df["motor_id"] == motor_id]
    if df_motor.empty:
        raise HTTPException(status_code=404, detail=f"Motor {motor_id} não encontrado.")
    return detectar_anomalia(df_motor)


@app.get("/frota/status", tags=["Frota"])
@limiter.limit("30/minute")
async def get_status_frota(
    request: Request,
    usuario: dict = Depends(usuario_atual),
):
    df = pd.read_csv(DIR_DADOS / "teste.csv")
    motor_ids = df["motor_id"].unique()

    resultado = {"normal": [], "atencao": [], "alerta": [], "critico": []}

    for motor_id in motor_ids:
        df_motor = df[df["motor_id"] == int(motor_id)]
        try:
            pred = prever_rul(df_motor)
            resultado[pred["status"]].append({
                "motor_id": int(motor_id),
                "rul_previsto": float(pred["rul_previsto"]),
                "ciclo_atual": int(pred["ciclo_atual"]),
            })
        except Exception:
            continue

    resultado["total"] = int(len(motor_ids))
    resultado["resumo"] = {k: len(v) for k, v in resultado.items() if isinstance(v, list)}
    return resultado


# ── Agente KYRA ────────────────────────────────────────────────────────────────

@app.post("/agente/consultar", response_model=ConsultaResposta, tags=["Agente KYRA"])
@limiter.limit("10/minute")
async def consultar_kyra(
    request: Request,
    body: ConsultaRequest,
    usuario: dict = Depends(usuario_atual),
):
    resposta = consultar(body.pergunta)
    return ConsultaResposta(pergunta=body.pergunta, resposta=resposta)


# ── WebSocket - Sensores em tempo real ────────────────────────────────────────

class GerenciadorConexoes:
    def __init__(self):
        self.ativas: list[WebSocket] = []

    async def conectar(self, ws: WebSocket):
        await ws.accept()
        self.ativas.append(ws)

    def desconectar(self, ws: WebSocket):
        self.ativas.remove(ws)

    async def broadcast(self, mensagem: dict):
        for ws in self.ativas.copy():
            try:
                await ws.send_json(mensagem)
            except Exception:
                self.ativas.remove(ws)


gerenciador = GerenciadorConexoes()


def _simular_leitura(motor_id: int, ciclo: int) -> dict:
    """Simula uma leitura de sensor com degradação progressiva."""
    degradacao = min(ciclo / 300, 1.0)
    return {
        "motor_id": motor_id,
        "ciclo": ciclo,
        "temp_saida_hpc": round(1590 + degradacao * 60 + random.gauss(0, 5), 2),
        "eficiencia_hpc": round(0.0305 - degradacao * 0.004 + random.gauss(0, 0.0005), 5),
        "velocidade_core": round(47.5 - degradacao * 1.2 + random.gauss(0, 0.2), 2),
        "pressao_saida_lpt": round(9065 - degradacao * 200 + random.gauss(0, 20), 2),
        "eficiencia_fan": round(8.42 - degradacao * 0.1 + random.gauss(0, 0.02), 4),
        "timestamp": asyncio.get_event_loop().time(),
    }


@app.websocket("/ws/sensores")
async def websocket_sensores(ws: WebSocket):
    await gerenciador.conectar(ws)
    ciclos = {i: random.randint(50, 250) for i in range(1, 6)}
    try:
        while True:
            motor_id = random.randint(1, 5)
            ciclos[motor_id] += 1
            leitura = _simular_leitura(motor_id, ciclos[motor_id])
            await gerenciador.broadcast(leitura)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        gerenciador.desconectar(ws)


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/health", tags=["Sistema"])
async def health():
    return {"status": "ok", "servico": "Kymera Labs API", "versao": "1.0.0"}
