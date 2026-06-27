"""
Testes da engenharia de features.
"""
import numpy as np
import pandas as pd
import pytest

from backend.ml.features import construir_features, selecionar_features, SENSORES_RELEVANTES, JANELAS


def _df_sintetico(n_ciclos: int = 30, motor_id: int = 1) -> pd.DataFrame:
    """Cria um DataFrame sintetico com dados de um motor."""
    rng = np.random.default_rng(42)
    dados = {"motor_id": motor_id, "ciclo": list(range(1, n_ciclos + 1))}
    sensores = [
        "temp_entrada", "temp_saida_lpc", "temp_saida_hpc", "temp_saida_lpt",
        "pressao_entrada", "pressao_saida_fan", "pressao_saida_lpc",
        "pressao_saida_hpc", "pressao_saida_lpt", "velocidade_fan",
        "velocidade_core", "eficiencia_fan", "eficiencia_lpc", "eficiencia_hpc",
        "eficiencia_lpt", "razao_bypass", "razao_combustivel",
        "temperatura_ambiente", "pressao_ambiente", "razao_pressao_total",
        "eficiencia_total",
    ]
    for s in sensores:
        dados[s] = rng.normal(loc=100, scale=5, size=n_ciclos).tolist()
    return pd.DataFrame(dados)


def test_construir_features_retorna_dataframe():
    df = _df_sintetico()
    resultado = construir_features(df)
    assert isinstance(resultado, pd.DataFrame)


def test_construir_features_preserva_linhas():
    df = _df_sintetico(n_ciclos=30)
    resultado = construir_features(df)
    assert len(resultado) == 30


def test_construir_features_cria_colunas_rolling():
    df = _df_sintetico(n_ciclos=30)
    resultado = construir_features(df)
    for sensor in SENSORES_RELEVANTES:
        for janela in JANELAS:
            assert f"{sensor}_media{janela}" in resultado.columns
            assert f"{sensor}_std{janela}" in resultado.columns


def test_selecionar_features_retorna_lista():
    df = _df_sintetico(n_ciclos=30)
    df_feat = construir_features(df)
    colunas = selecionar_features(df_feat)
    assert isinstance(colunas, list)
    assert len(colunas) > 0


def test_selecionar_features_inclui_ciclo_norm():
    df = _df_sintetico(n_ciclos=30)
    df_feat = construir_features(df)
    colunas = selecionar_features(df_feat)
    assert "ciclo_norm" in colunas


def test_construir_features_com_motor_unico():
    df = _df_sintetico(n_ciclos=5, motor_id=99)
    resultado = construir_features(df)
    assert resultado["motor_id"].iloc[0] == 99
