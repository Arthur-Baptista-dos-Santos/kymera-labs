"""
Treinamento dos modelos de ML com MLflow tracking.
- XGBoost: predição de RUL (regressão)
- Isolation Forest: detecção de anomalias em sensores
"""
import os
import pickle
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from backend.ml.features import construir_features, selecionar_features

RAIZ = Path(__file__).parent.parent.parent
DADOS_TREINO = RAIZ / "dados" / "raw" / "treino.csv"
DIR_MODELOS = RAIZ / "modelos"
DIR_MODELOS.mkdir(exist_ok=True)

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
EXPERIMENTO = "kymera-rul-prediction"

# RUL máximo que consideramos - acima disso o motor está saudável
RUL_MAXIMO = 200


def _clipar_rul(df: pd.DataFrame) -> pd.DataFrame:
    """Limita o RUL ao máximo definido (motores muito novos = mesmo risco)."""
    df = df.copy()
    df["rul"] = df["rul"].clip(upper=RUL_MAXIMO)
    return df


def treinar() -> dict:
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENTO)

    print("Carregando dados...")
    df = pd.read_csv(DADOS_TREINO)
    df = _clipar_rul(df)

    print("Construindo features...")
    df = construir_features(df)
    feature_cols = selecionar_features(df)

    X = df[feature_cols].values
    y = df["rul"].values

    X_treino, X_val, y_treino, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler = StandardScaler()
    X_treino_sc = scaler.fit_transform(X_treino)
    X_val_sc = scaler.transform(X_val)

    with mlflow.start_run(run_name="xgboost-rul"):
        params = {
            "n_estimators": 400,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "n_jobs": -1,
        }
        mlflow.log_params(params)
        mlflow.log_param("rul_maximo", RUL_MAXIMO)
        mlflow.log_param("n_features", len(feature_cols))
        mlflow.log_param("n_amostras_treino", len(X_treino))

        print("Treinando XGBoost para predição de RUL...")
        modelo_rul = XGBRegressor(**params)
        modelo_rul.fit(
            X_treino_sc, y_treino,
            eval_set=[(X_val_sc, y_val)],
            verbose=False,
        )

        y_pred = modelo_rul.predict(X_val_sc)
        mae = mean_absolute_error(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        r2 = r2_score(y_val, y_pred)

        mlflow.log_metric("mae", mae)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)

        print(f"  MAE:  {mae:.2f} ciclos")
        print(f"  RMSE: {rmse:.2f} ciclos")
        print(f"  R²:   {r2:.4f}")

        mlflow.log_param("modelo_arquivo", "modelos/modelo_rul.pkl")

    print("\nTreinando Isolation Forest para deteccao de anomalias...")
    modelo_anomalia = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42,
        n_jobs=-1,
    )
    modelo_anomalia.fit(X_treino_sc)

    print("Salvando modelos e scaler...")
    with open(DIR_MODELOS / "modelo_rul.pkl", "wb") as f:
        pickle.dump(modelo_rul, f)
    with open(DIR_MODELOS / "modelo_anomalia.pkl", "wb") as f:
        pickle.dump(modelo_anomalia, f)
    with open(DIR_MODELOS / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(DIR_MODELOS / "feature_cols.pkl", "wb") as f:
        pickle.dump(feature_cols, f)

    metricas = {"mae": mae, "rmse": rmse, "r2": r2}
    print("\nTreinamento concluido!")
    print(f"Modelos salvos em: {DIR_MODELOS}")
    return metricas


if __name__ == "__main__":
    treinar()
