"""
Agente roteador com LangGraph.
Decide automaticamente entre RAG, predição ML ou consulta de sensores
para responder perguntas sobre manutenção preditiva.
"""
import os
import json
import pandas as pd
from pathlib import Path
from typing import Annotated

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from backend.agente.rag import buscar
from backend.ml.preditor import prever_rul, detectar_anomalia

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

DIR_DADOS = Path(__file__).parent.parent.parent / "dados" / "raw"


def _carregar_historico_motor(motor_id: int) -> pd.DataFrame:
    """Carrega o histórico de ciclos de um motor do dataset de teste."""
    caminho = DIR_DADOS / "teste.csv"
    df = pd.read_csv(caminho)
    df_motor = df[df["motor_id"] == motor_id].copy()
    if df_motor.empty:
        caminho = DIR_DADOS / "treino.csv"
        df = pd.read_csv(caminho)
        df_motor = df[df["motor_id"] == motor_id].copy()
    return df_motor


@tool
def consultar_manual(pergunta: str) -> str:
    """
    Busca informações técnicas nos manuais da turbina KY-9000.
    Use quando a pergunta for sobre: o que significa um sensor, faixas normais
    de operação, procedimentos de manutenção, glossário técnico ou interpretação
    de alertas. NÃO use para dados ao vivo ou predições.
    """
    resultados = buscar(pergunta, k=3)
    if not resultados:
        return "Nenhuma informação encontrada nos manuais para essa consulta."
    resposta = ""
    for r in resultados:
        resposta += f"[Fonte: {r['arquivo']}]\n{r['conteudo']}\n\n"
    return resposta.strip()


@tool
def prever_vida_util(motor_id: int) -> str:
    """
    Prediz o RUL (Remaining Useful Life) de um motor específico com base
    no histórico de leituras dos seus sensores.
    Use quando a pergunta for sobre: quantos ciclos restam, quando o motor
    vai falhar, qual o status atual de um motor, se um motor precisa de
    manutenção em breve. Requer o ID numérico do motor.
    """
    df = _carregar_historico_motor(motor_id)
    if df.empty:
        return f"Motor {motor_id} não encontrado no banco de dados."
    resultado = prever_rul(df)
    return (
        f"Motor {resultado['motor_id']} - Ciclo atual: {resultado['ciclo_atual']}\n"
        f"RUL previsto: {resultado['rul_previsto']} ciclos\n"
        f"Status: {resultado['status'].upper()}\n"
        f"Interpretação: "
        + {
            "normal": "Motor operando dentro dos parâmetros esperados.",
            "atencao": "Degradação detectada. Monitorar com frequência maior.",
            "alerta": "Manutenção deve ser agendada em breve.",
            "critico": "PARADA IMEDIATA recomendada. Risco de falha iminente.",
        }[resultado["status"]]
    )


@tool
def verificar_anomalia_sensor(motor_id: int) -> str:
    """
    Verifica se as leituras mais recentes dos sensores de um motor estão
    anômalas em relação ao padrão histórico normal.
    Use quando a pergunta for sobre: sensores fora do padrão, leituras
    suspeitas, comportamento anormal, diagnóstico de anomalia.
    """
    df = _carregar_historico_motor(motor_id)
    if df.empty:
        return f"Motor {motor_id} não encontrado no banco de dados."

    resultado = detectar_anomalia(df)

    if resultado["is_anomalia"]:
        sensores = ", ".join(resultado["sensores_suspeitos"]) or "múltiplos sensores"
        return (
            f"ANOMALIA DETECTADA no motor {motor_id}\n"
            f"Severidade: {resultado['severidade'].upper()}\n"
            f"Score de anomalia: {resultado['score']} (quanto mais negativo, mais anômalo)\n"
            f"Sensores suspeitos: {sensores}\n"
            f"Recomendação: consultar procedimentos de manutenção para os sensores afetados."
        )
    return (
        f"Motor {motor_id}: leituras dentro do padrão normal.\n"
        f"Score: {resultado['score']} (próximo de 0 = normal)"
    )


@tool
def listar_motores_criticos() -> str:
    """
    Lista todos os motores com status crítico ou de alerta no momento.
    Use quando a pergunta for sobre: quais motores precisam de atenção,
    panorama geral da frota, motores em risco, dashboard de status.
    """
    df = pd.read_csv(DIR_DADOS / "teste.csv")
    motor_ids = df["motor_id"].unique()

    criticos = []
    alertas = []

    for motor_id in motor_ids[:20]:
        df_motor = df[df["motor_id"] == motor_id]
        try:
            resultado = prever_rul(df_motor)
            if resultado["status"] == "critico":
                criticos.append((motor_id, resultado["rul_previsto"]))
            elif resultado["status"] == "alerta":
                alertas.append((motor_id, resultado["rul_previsto"]))
        except Exception:
            continue

    resposta = f"Análise de {min(20, len(motor_ids))} motores:\n\n"

    if criticos:
        resposta += f"CRÍTICOS ({len(criticos)} motores):\n"
        for mid, rul in sorted(criticos, key=lambda x: x[1]):
            resposta += f"  - Motor {mid}: {rul} ciclos restantes\n"
    else:
        resposta += "Nenhum motor em estado crítico.\n"

    if alertas:
        resposta += f"\nEM ALERTA ({len(alertas)} motores):\n"
        for mid, rul in sorted(alertas, key=lambda x: x[1]):
            resposta += f"  - Motor {mid}: {rul} ciclos restantes\n"
    else:
        resposta += "Nenhum motor em estado de alerta.\n"

    return resposta


FERRAMENTAS = [
    consultar_manual,
    prever_vida_util,
    verificar_anomalia_sensor,
    listar_motores_criticos,
]

SYSTEM_PROMPT = """Você é KYRA, a assistente de inteligência artificial da Kymera Labs.
Sua especialidade é manutenção preditiva de turbinas industriais KY-9000.

REGRAS ABSOLUTAS:
1. NUNCA invente dados, números ou diagnósticos. Use SEMPRE as ferramentas disponíveis.
2. Para qualquer informação técnica (sensores, faixas, procedimentos): use consultar_manual.
3. Para saber o estado de um motor específico: use prever_vida_util e verificar_anomalia_sensor.
4. Para visão geral da frota: use listar_motores_criticos.
5. Responda SEMPRE em português brasileiro, de forma clara e objetiva.
6. Cite a fonte quando usar informações dos manuais.
7. Quando o status for CRÍTICO, enfatize a urgência da situação.

Você representa o estado da arte em IA aplicada à indústria. Seja preciso, profissional e útil."""


def _rotear(pergunta: str) -> tuple[str, str]:
    """
    Roteamento determinístico por palavras-chave.
    Retorna (nome_rota, contexto_coletado).
    """
    p = pergunta.lower()

    # Extrai motor_id se presente
    motor_id = None
    import re
    m = re.search(r"motor\s+(\d+)", p)
    if m:
        motor_id = int(m.group(1))

    if any(w in p for w in ["crítico", "critico", "alerta", "frota", "panorama", "lista", "todos os motores"]):
        return "frota", listar_motores_criticos.invoke({})

    if motor_id and any(w in p for w in ["anomalia", "anômalo", "suspeito", "sensor", "fora do padrão"]):
        return "anomalia", verificar_anomalia_sensor.invoke({"motor_id": motor_id})

    if motor_id and any(w in p for w in ["rul", "vida útil", "vida util", "ciclos", "falha", "status", "quando vai"]):
        return "rul", prever_vida_util.invoke({"motor_id": motor_id})

    if motor_id:
        rul = prever_vida_util.invoke({"motor_id": motor_id})
        anomalia = verificar_anomalia_sensor.invoke({"motor_id": motor_id})
        return "motor_completo", f"{rul}\n\n{anomalia}"

    # Default: busca no manual
    return "manual", consultar_manual.invoke({"pergunta": pergunta})


def consultar(pergunta: str) -> str:
    """
    Ponto de entrada principal.
    Roteia a pergunta, coleta dados reais e usa o LLM para sintetizar a resposta.
    """
    llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_URL, temperature=0)

    rota, contexto = _rotear(pergunta)

    prompt = f"""{SYSTEM_PROMPT}

DADOS REAIS COLETADOS PELO SISTEMA (use APENAS estes dados, não invente nada):
---
{contexto}
---

Pergunta do usuário: {pergunta}

Responda em português brasileiro de forma clara, objetiva e profissional."""

    resposta = llm.invoke([HumanMessage(content=prompt)])
    return f"[Rota: {rota}]\n{resposta.content}"


if __name__ == "__main__":
    perguntas = [
        "O que significa eficiencia_hpc e qual é a faixa normal?",
        "Qual é o RUL do motor 3?",
        "O motor 5 tem anomalias nos sensores?",
        "Quais motores estão em estado crítico agora?",
    ]
    for p in perguntas:
        print(f"\nPergunta: {p}")
        print(f"Resposta: {consultar(p)}")
        print("-" * 60)
