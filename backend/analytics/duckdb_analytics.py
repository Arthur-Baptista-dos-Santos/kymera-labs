"""
Camada analítica com DuckDB.
Consolida leituras dos sensores e histórico de predições para consultas analíticas.
"""
from pathlib import Path

import duckdb
import pandas as pd

DIR_DADOS = Path(__file__).parent.parent.parent / "dados"
DB_PATH = DIR_DADOS / "analytics.duckdb"


def _conectar() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH))


def inicializar_banco() -> None:
    """Cria as tabelas analíticas se não existirem."""
    con = _conectar()
    con.execute("""
        CREATE TABLE IF NOT EXISTS leituras_sensores (
            motor_id     INTEGER,
            ciclo        INTEGER,
            timestamp    TIMESTAMP DEFAULT current_timestamp,
            temp_saida_hpc   DOUBLE,
            eficiencia_hpc   DOUBLE,
            velocidade_core  DOUBLE,
            pressao_saida_lpt DOUBLE,
            PRIMARY KEY (motor_id, ciclo)
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS historico_predicoes (
            id           INTEGER PRIMARY KEY,
            motor_id     INTEGER,
            ciclo_atual  INTEGER,
            rul_previsto DOUBLE,
            status       VARCHAR,
            timestamp    TIMESTAMP DEFAULT current_timestamp
        )
    """)
    con.execute("""
        CREATE SEQUENCE IF NOT EXISTS seq_predicoes START 1
    """)
    con.close()


def ingerir_leituras_csv() -> int:
    """Ingere os dados brutos dos CSVs no DuckDB. Retorna total de registros."""
    con = _conectar()
    treino = DIR_DADOS / "raw" / "treino.csv"
    teste = DIR_DADOS / "raw" / "teste.csv"

    total = 0
    for path in [treino, teste]:
        if path.exists():
            n = con.execute(
                f"SELECT COUNT(*) FROM read_csv_auto('{path.as_posix()}')"
            ).fetchone()[0]
            con.execute(f"""
                INSERT OR IGNORE INTO leituras_sensores
                    (motor_id, ciclo, temp_saida_hpc, eficiencia_hpc,
                     velocidade_core, pressao_saida_lpt)
                SELECT motor_id, ciclo, temp_saida_hpc, eficiencia_hpc,
                       velocidade_core, pressao_saida_lpt
                FROM read_csv_auto('{path.as_posix()}')
            """)
            total += n

    con.close()
    return total


def registrar_predicao(motor_id: int, ciclo_atual: int,
                       rul_previsto: float, status: str) -> None:
    """Persiste uma predição no histórico analítico."""
    con = _conectar()
    con.execute("""
        INSERT INTO historico_predicoes (id, motor_id, ciclo_atual, rul_previsto, status)
        VALUES (nextval('seq_predicoes'), ?, ?, ?, ?)
    """, [motor_id, ciclo_atual, rul_previsto, status])
    con.close()


def resumo_frota() -> pd.DataFrame:
    """Retorna um resumo analítico do status atual de todos os motores."""
    con = _conectar()
    df = con.execute("""
        SELECT
            status,
            COUNT(*)              AS total_motores,
            AVG(rul_previsto)     AS rul_medio,
            MIN(rul_previsto)     AS rul_minimo,
            MAX(rul_previsto)     AS rul_maximo
        FROM (
            SELECT DISTINCT ON (motor_id)
                motor_id, rul_previsto, status
            FROM historico_predicoes
            ORDER BY motor_id, timestamp DESC
        )
        GROUP BY status
        ORDER BY rul_medio ASC
    """).df()
    con.close()
    return df


def historico_motor(motor_id: int) -> pd.DataFrame:
    """Retorna o histórico completo de predições de um motor."""
    con = _conectar()
    df = con.execute("""
        SELECT ciclo_atual, rul_previsto, status, timestamp
        FROM historico_predicoes
        WHERE motor_id = ?
        ORDER BY timestamp ASC
    """, [motor_id]).df()
    con.close()
    return df


def tendencia_degradacao() -> pd.DataFrame:
    """Calcula a taxa média de degradação por motor (queda de RUL por ciclo)."""
    con = _conectar()
    df = con.execute("""
        SELECT
            motor_id,
            COUNT(*)                                          AS total_predicoes,
            FIRST(rul_previsto ORDER BY timestamp ASC)        AS rul_inicial,
            LAST(rul_previsto ORDER BY timestamp ASC)         AS rul_atual,
            FIRST(rul_previsto ORDER BY timestamp ASC)
                - LAST(rul_previsto ORDER BY timestamp ASC)   AS degradacao_total
        FROM historico_predicoes
        GROUP BY motor_id
        HAVING COUNT(*) > 1
        ORDER BY degradacao_total DESC
    """).df()
    con.close()
    return df


def estatisticas_sensores() -> pd.DataFrame:
    """Estatísticas descritivas dos sensores por motor."""
    con = _conectar()
    df = con.execute("""
        SELECT
            motor_id,
            COUNT(*)                    AS total_leituras,
            AVG(temp_saida_hpc)         AS temp_media,
            STDDEV(temp_saida_hpc)      AS temp_desvio,
            AVG(eficiencia_hpc)         AS efic_media,
            AVG(velocidade_core)        AS vel_media,
            MIN(ciclo)                  AS ciclo_inicio,
            MAX(ciclo)                  AS ciclo_fim
        FROM leituras_sensores
        GROUP BY motor_id
        ORDER BY motor_id
    """).df()
    con.close()
    return df


if __name__ == "__main__":
    print("Inicializando banco DuckDB...")
    inicializar_banco()
    print("Ingerindo dados dos CSVs...")
    total = ingerir_leituras_csv()
    print(f"{total} registros ingeridos.")
    print("\nEstatísticas dos sensores:")
    print(estatisticas_sensores().to_string(index=False))
