"""
DAG de retraining automatico dos modelos Kymera Labs.
Executa semanalmente: gera novos dados, retreina e valida os modelos.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

ARGS_PADRAO = {
    "owner": "kymera-labs",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}


def gerar_dados(**context):
    """Gera novo batch de dados sinteticos para retraining."""
    import subprocess
    import sys
    resultado = subprocess.run(
        [sys.executable, "dados/gerar_dados.py"],
        capture_output=True,
        text=True,
        cwd="/opt/airflow/kymera-labs",
    )
    if resultado.returncode != 0:
        raise RuntimeError(f"Falha ao gerar dados: {resultado.stderr}")
    print(resultado.stdout)


def treinar_modelos(**context):
    """Retreina XGBoost e Isolation Forest com os novos dados."""
    import subprocess
    import sys
    resultado = subprocess.run(
        [sys.executable, "-m", "backend.ml.treinar"],
        capture_output=True,
        text=True,
        cwd="/opt/airflow/kymera-labs",
    )
    if resultado.returncode != 0:
        raise RuntimeError(f"Falha no treinamento: {resultado.stderr}")
    print(resultado.stdout)


def validar_modelos(**context):
    """Valida que os modelos retreinados atendem ao threshold minimo de qualidade."""
    import pickle
    import pandas as pd
    import numpy as np
    from pathlib import Path
    from sklearn.metrics import mean_absolute_error, r2_score

    DIR = Path("/opt/airflow/kymera-labs")

    with open(DIR / "modelos/modelo_rul.pkl", "rb") as f:
        modelo = pickle.load(f)
    with open(DIR / "modelos/scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open(DIR / "modelos/feature_cols.pkl", "rb") as f:
        feature_cols = pickle.load(f)

    import sys
    sys.path.insert(0, str(DIR))
    from backend.ml.features import construir_features

    df = pd.read_csv(DIR / "dados/raw/teste.csv")
    RUL_MAXIMO = 200

    resultados = []
    for motor_id in df["motor_id"].unique():
        df_motor = df[df["motor_id"] == motor_id].copy()
        max_ciclo = df_motor["ciclo"].max()
        df_motor["rul"] = (max_ciclo - df_motor["ciclo"]).clip(upper=RUL_MAXIMO)
        df_feat = construir_features(df_motor)
        cols = [c for c in feature_cols if c in df_feat.columns]
        X = df_feat[cols].fillna(0).values
        y = df_motor.loc[df_feat.index, "rul"].values
        X_sc = scaler.transform(X)
        y_pred = modelo.predict(X_sc)
        resultados.append({"mae": mean_absolute_error(y, y_pred), "r2": r2_score(y, y_pred)})

    mae_medio = np.mean([r["mae"] for r in resultados])
    r2_medio = np.mean([r["r2"] for r in resultados])

    print(f"MAE medio: {mae_medio:.2f} | R2 medio: {r2_medio:.4f}")

    MAE_THRESHOLD = 25.0
    R2_THRESHOLD = 0.80

    if mae_medio > MAE_THRESHOLD:
        raise ValueError(f"MAE {mae_medio:.2f} acima do threshold {MAE_THRESHOLD}")
    if r2_medio < R2_THRESHOLD:
        raise ValueError(f"R2 {r2_medio:.4f} abaixo do threshold {R2_THRESHOLD}")

    print("Validacao aprovada. Modelos prontos para producao.")


def reindexar_rag(**context):
    """Reindexa a base de conhecimento no ChromaDB."""
    import subprocess
    import sys
    resultado = subprocess.run(
        [sys.executable, "-m", "backend.agente.rag", "--forcar"],
        capture_output=True,
        text=True,
        cwd="/opt/airflow/kymera-labs",
    )
    print(resultado.stdout)


with DAG(
    dag_id="kymera_retraining_semanal",
    description="Retraining semanal dos modelos de manutenção preditiva",
    default_args=ARGS_PADRAO,
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 2 * * 0",
    catchup=False,
    tags=["kymera-labs", "ml", "retraining"],
) as dag:

    t1 = PythonOperator(
        task_id="gerar_dados_sinteticos",
        python_callable=gerar_dados,
    )

    t2 = PythonOperator(
        task_id="treinar_modelos",
        python_callable=treinar_modelos,
    )

    t3 = PythonOperator(
        task_id="validar_modelos",
        python_callable=validar_modelos,
    )

    t4 = PythonOperator(
        task_id="reindexar_rag",
        python_callable=reindexar_rag,
    )

    t1 >> t2 >> t3 >> t4
