"""
Gerador de dados sintéticos inspirado no dataset NASA CMAPSS.
Produz leituras realistas de 21 sensores de turbinas industriais
com degradação progressiva e falha simulada.
"""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
N_MOTORES_TREINO = 80
N_MOTORES_TESTE = 20
CICLOS_MIN = 120
CICLOS_MAX = 350

# Nomes dos 21 sensores (baseados no CMAPSS real)
SENSORES = [
    "temp_entrada_fan",       # s1  - temperatura total na entrada do fan
    "temp_saida_lpc",         # s2  - temperatura total na saida do LPC
    "temp_saida_hpc",         # s3  - temperatura total na saida do HPC
    "temp_saida_lpt",         # s4  - temperatura total na saida do LPT
    "pressao_entrada_fan",    # s5  - pressao total na entrada do fan
    "pressao_saida_lpc",      # s6  - pressao total na saida do LPC
    "pressao_saida_hpc",      # s7  - pressao total na saida do HPC
    "pressao_saida_hpt",      # s8  - pressao total fisica na saida do HPT
    "pressao_saida_lpt",      # s9  - pressao total fisica na saida do LPT
    "velocidade_fan",         # s10 - velocidade de rotacao do fan
    "velocidade_core",        # s11 - velocidade de rotacao do nucleo
    "razao_pressao_fan",      # s12 - razao de pressao do fan estático
    "razao_combustivel",      # s13 - razao combustivel-ar do nucleo
    "razao_pressao_corr_fan", # s14 - razao de pressao corrigida do fan
    "eficiencia_fan",         # s15 - eficiencia aerodinamica corrigida do fan
    "eficiencia_hpc",         # s16 - eficiencia aerodinamica corrigida do HPC
    "eficiencia_lpt",         # s17 - eficiencia aerodinamica corrigida do LPT
    "bleed_entalpico",        # s18 - nivel de sangria entalpica
    "demanda_coolant_hpt",    # s19 - demanda de resfriamento HPT coolant bleed
    "demanda_coolant_lpt",    # s20 - demanda de resfriamento LPT coolant bleed
    "pressao_saida_fan",      # s21 - pressao total na saida do fan
]

# Valores base e amplitude de ruido para cada sensor
SENSOR_CONFIG = [
    (518.67, 0.5),    # s1
    (642.68, 0.5),    # s2
    (1590.0, 5.0),    # s3
    (1408.0, 8.0),    # s4
    (14.62,  0.1),    # s5
    (21.61,  0.1),    # s6
    (554.0,  3.0),    # s7
    (2388.0, 8.0),    # s8
    (9065.0, 20.0),   # s9
    (1.30,   0.01),   # s10
    (47.47,  0.2),    # s11
    (521.66, 1.0),    # s12
    (2388.0, 5.0),    # s13
    (8138.0, 20.0),   # s14
    (8.4195, 0.05),   # s15
    (0.03,   0.002),  # s16
    (392.0,  2.0),    # s17
    (2388.0, 8.0),    # s18
    (100.0,  0.5),    # s19
    (38.95,  0.2),    # s20
    (23.42,  0.1),    # s21
]

# Direcao e intensidade da degradacao por sensor (positivo=sobe, negativo=desce)
DEGRADACAO = [
    0.0,    # s1  - nao degrada visivelmente
    0.0,    # s2
    2.0,    # s3  - temperatura sobe com degradacao
    1.5,    # s4
    0.0,    # s5
    0.0,    # s6
   -0.5,    # s7  - pressao cai levemente
    0.0,    # s8
   -5.0,    # s9  - pressao cai na saida
    0.0,    # s10
   -0.05,   # s11 - velocidade cai
    0.0,    # s12
    0.0,    # s13
   -5.0,    # s14
   -0.002,  # s15 - eficiencia cai
   -0.001,  # s16
   -0.3,    # s17
    0.0,    # s18
    0.0,    # s19
    0.0,    # s20
    0.0,    # s21
]


def _gerar_motor(motor_id: int, n_ciclos: int, rng: np.random.Generator) -> pd.DataFrame:
    """Gera os ciclos de um motor com degradacao progressiva."""
    ciclos = np.arange(1, n_ciclos + 1)
    degradacao_norm = ciclos / n_ciclos  # 0 no inicio, 1 na falha

    linhas = []
    for i, ciclo in enumerate(ciclos):
        d = degradacao_norm[i]
        linha = {
            "motor_id": motor_id,
            "ciclo": ciclo,
            "config1": rng.normal(0.0, 0.002),
            "config2": rng.normal(0.0, 0.003),
            "config3": rng.choice([100.0]),
        }
        for j, (nome, (base, ruido), deg) in enumerate(
            zip(SENSORES, SENSOR_CONFIG, DEGRADACAO)
        ):
            # valor = base + efeito_degradacao + ruido_gaussiano
            valor = base + deg * d + rng.normal(0, ruido)
            linha[nome] = round(valor, 4)

        linhas.append(linha)

    return pd.DataFrame(linhas)


def gerar_dataset(
    n_motores: int,
    seed_offset: int,
    incluir_rul: bool = True,
) -> pd.DataFrame:
    """Gera dataset completo com N motores."""
    rng = np.random.default_rng(SEED + seed_offset)
    frames = []

    for i in range(1, n_motores + 1):
        n_ciclos = int(rng.integers(CICLOS_MIN, CICLOS_MAX))
        df_motor = _gerar_motor(i, n_ciclos, rng)
        if incluir_rul:
            df_motor["rul"] = n_ciclos - df_motor["ciclo"]
        frames.append(df_motor)

    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    saida = Path(__file__).parent / "raw"
    saida.mkdir(exist_ok=True)

    print("Gerando dados de treino...")
    df_treino = gerar_dataset(N_MOTORES_TREINO, seed_offset=0, incluir_rul=True)
    df_treino.to_csv(saida / "treino.csv", index=False)
    print(f"  {len(df_treino):,} registros | {df_treino['motor_id'].nunique()} motores")

    print("Gerando dados de teste...")
    df_teste = gerar_dataset(N_MOTORES_TESTE, seed_offset=100, incluir_rul=True)
    df_teste.to_csv(saida / "teste.csv", index=False)
    print(f"  {len(df_teste):,} registros | {df_teste['motor_id'].nunique()} motores")

    print("\nAmostra dos dados de treino:")
    print(df_treino.head(3).to_string())
    print(f"\nColunas: {list(df_treino.columns)}")
    print("\nDataset gerado com sucesso em dados/raw/")
