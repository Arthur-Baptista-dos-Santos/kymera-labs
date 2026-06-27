"""
Módulo de predição em tempo real.
Carrega os modelos treinados e expõe funções para:
- Prever RUL (ciclos restantes) de um motor
- Detectar anomalias nas leituras dos sensores
"""
import pickle
from pathlib import Path
from functools import lru_cache

import numpy as np
import pandas as pd

from backend.ml.features import construir_features, selecionar_features

DIR_MODELOS = Path(__file__).parent.parent.parent / "modelos"


@lru_cache(maxsize=1)
def _carregar_modelos() -> tuple:
    """Carrega os modelos do disco uma única vez e mantém em memória."""
    with open(DIR_MODELOS / "modelo_rul.pkl", "rb") as f:
        modelo_rul = pickle.load(f)
    with open(DIR_MODELOS / "modelo_anomalia.pkl", "rb") as f:
        modelo_anomalia = pickle.load(f)
    with open(DIR_MODELOS / "scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open(DIR_MODELOS / "feature_cols.pkl", "rb") as f:
        feature_cols = pickle.load(f)
    return modelo_rul, modelo_anomalia, scaler, feature_cols


def prever_rul(historico_motor: pd.DataFrame) -> dict:
    """
    Recebe o histórico de ciclos de um motor e retorna a predição de RUL.

    Args:
        historico_motor: DataFrame com colunas motor_id, ciclo e os 21 sensores.
                         Deve conter ao menos 1 linha (ciclo atual).

    Returns:
        dict com rul_previsto, ciclo_atual, status e confianca.
    """
    modelo_rul, _, scaler, feature_cols = _carregar_modelos()

    df = construir_features(historico_motor)
    ultima_leitura = df.tail(1)

    colunas_presentes = [c for c in feature_cols if c in ultima_leitura.columns]
    X = ultima_leitura[colunas_presentes].values
    X_sc = scaler.transform(X)

    rul_previsto = float(modelo_rul.predict(X_sc)[0])
    rul_previsto = max(0, round(rul_previsto, 1))

    ciclo_atual = int(historico_motor["ciclo"].max())

    if rul_previsto <= 10:
        status = "critico"
    elif rul_previsto <= 30:
        status = "alerta"
    elif rul_previsto <= 60:
        status = "atencao"
    else:
        status = "normal"

    return {
        "motor_id": int(historico_motor["motor_id"].iloc[0]),
        "ciclo_atual": ciclo_atual,
        "rul_previsto": rul_previsto,
        "status": status,
    }


def detectar_anomalia(historico_motor: pd.DataFrame) -> dict:
    """
    Recebe o histórico de ciclos de um motor e detecta se a última leitura é anômala.

    Args:
        historico_motor: DataFrame com colunas motor_id, ciclo e os 21 sensores.
                         Precisa de ao menos 20 linhas para rolling features completas.

    Returns:
        dict com is_anomalia, score e sensores_suspeitos.
    """
    _, modelo_anomalia, scaler, feature_cols = _carregar_modelos()

    df = construir_features(historico_motor)

    ultima_leitura = df.tail(1)
    colunas_presentes = [c for c in feature_cols if c in ultima_leitura.columns]
    X = ultima_leitura[colunas_presentes].fillna(0).values
    X_sc = scaler.transform(X)

    predicao = modelo_anomalia.predict(X_sc)[0]
    score = float(modelo_anomalia.score_samples(X_sc)[0])

    is_anomalia = bool(predicao == -1)

    sensores_suspeitos = []
    if is_anomalia:
        from backend.ml.features import SENSORES_RELEVANTES
        ultima_raw = historico_motor.tail(1).to_dict(orient="records")[0]
        for sensor in SENSORES_RELEVANTES:
            if sensor in ultima_raw:
                sensores_suspeitos.append(sensor)

    return {
        "is_anomalia": is_anomalia,
        "score": round(score, 4),
        "sensores_suspeitos": sensores_suspeitos,
        "severidade": "alta" if score < -0.15 else "media" if is_anomalia else "nenhuma",
    }
