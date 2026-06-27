"""
Engenharia de features para predição de RUL.
Transforma leituras brutas de sensores em features temporais.
"""
import pandas as pd
import numpy as np

SENSORES = [
    "temp_entrada_fan", "temp_saida_lpc", "temp_saida_hpc", "temp_saida_lpt",
    "pressao_entrada_fan", "pressao_saida_lpc", "pressao_saida_hpc",
    "pressao_saida_hpt", "pressao_saida_lpt", "velocidade_fan",
    "velocidade_core", "razao_pressao_fan", "razao_combustivel",
    "razao_pressao_corr_fan", "eficiencia_fan", "eficiencia_hpc",
    "eficiencia_lpt", "bleed_entalpico", "demanda_coolant_hpt",
    "demanda_coolant_lpt", "pressao_saida_fan",
]

# Sensores com sinal de degradacao visivel (usados nas features principais)
SENSORES_RELEVANTES = [
    "temp_saida_hpc", "temp_saida_lpt", "pressao_saida_lpt",
    "velocidade_core", "eficiencia_fan", "eficiencia_hpc", "eficiencia_lpt",
    "pressao_saida_hpc",
]

JANELAS = [5, 10, 20]


def construir_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe o DataFrame bruto e retorna um DataFrame com features temporais.
    Ordena por motor_id e ciclo antes de calcular as janelas deslizantes.
    """
    df = df.sort_values(["motor_id", "ciclo"]).copy()

    for sensor in SENSORES_RELEVANTES:
        grupo = df.groupby("motor_id")[sensor]
        for janela in JANELAS:
            df[f"{sensor}_media{janela}"] = grupo.transform(
                lambda x: x.rolling(janela, min_periods=1).mean()
            )
            df[f"{sensor}_std{janela}"] = grupo.transform(
                lambda x: x.rolling(janela, min_periods=1).std().fillna(0)
            )

    # Ciclo normalizado por motor: posicao relativa na vida util observada ate agora
    max_ciclo = df.groupby("motor_id")["ciclo"].transform("max")
    df["ciclo_norm"] = df["ciclo"] / max_ciclo

    # Variacao absoluta do ciclo atual em relacao ao anterior (por motor)
    df["delta_ciclo"] = df.groupby("motor_id")["ciclo"].diff().fillna(1)

    return df


def selecionar_features(df: pd.DataFrame) -> list[str]:
    """Retorna a lista de colunas usadas como input do modelo."""
    features = ["ciclo_norm", "delta_ciclo"] + SENSORES

    for sensor in SENSORES_RELEVANTES:
        for janela in JANELAS:
            features.append(f"{sensor}_media{janela}")
            features.append(f"{sensor}_std{janela}")

    # Garante que todas as colunas existem no DataFrame
    return [f for f in features if f in df.columns]
