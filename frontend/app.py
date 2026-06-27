"""
Kymera Labs - Frontend principal.
Many intelligences. One decision.
"""
import streamlit as st

st.set_page_config(
    page_title="Kymera Labs",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS global
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #21262d; }
    .stMetric { background-color: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 16px; }
    .kymera-header { text-align: center; padding: 2rem 0 1rem 0; }
    .kymera-title { font-size: 2.8rem; font-weight: 800; color: #58a6ff; letter-spacing: 4px; }
    .kymera-slogan { font-size: 1rem; color: #8b949e; letter-spacing: 2px; margin-top: 4px; }
    .kymera-hook { font-size: 0.85rem; color #388bfd; margin-top: 2px; }
    .status-normal { color: #3fb950; font-weight: bold; }
    .status-atencao { color: #e3b341; font-weight: bold; }
    .status-alerta { color: #f0883e; font-weight: bold; }
    .status-critico { color: #f85149; font-weight: bold; }
    .divider { border-top: 1px solid #21262d; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


def main():
    # Inicializa estado de sessao
    if "token" not in st.session_state:
        st.session_state.token = None
    if "usuario" not in st.session_state:
        st.session_state.usuario = None

    if not st.session_state.token:
        _pagina_login()
    else:
        _app_principal()


def _pagina_login():
    st.markdown("""
    <div class="kymera-header">
        <div class="kymera-title">⚡ KYMERA LABS</div>
        <div class="kymera-slogan">MANY INTELLIGENCES. ONE DECISION.</div>
        <div class="kymera-hook">Where AI thinks together.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("### Acesso ao Sistema")
        with st.form("login"):
            username = st.text_input("Usuário", placeholder="admin")
            password = st.text_input("Senha", type="password", placeholder="kymera2026")
            entrar = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if entrar:
            import requests
            try:
                r = requests.post(
                    "http://localhost:8502/auth/login",
                    data={"username": username, "password": password},
                    timeout=5,
                )
                if r.status_code == 200:
                    dados = r.json()
                    st.session_state.token = dados["access_token"]
                    st.session_state.usuario = dados["username"]
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
            except Exception:
                st.error("Não foi possível conectar à API. Verifique se o backend está rodando.")

        st.markdown("---")
        st.caption("Demo: admin / kymera2026  |  operador / operador123")


def _headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def _app_principal():
    import requests

    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 1rem 0;">
            <div style="font-size:1.4rem; font-weight:800; color:#58a6ff; letter-spacing:3px;">⚡ KYMERA</div>
            <div style="font-size:0.7rem; color:#8b949e; letter-spacing:1px;">MANY INTELLIGENCES. ONE DECISION.</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        pagina = st.radio(
            "Navegação",
            ["Dashboard", "Motores", "Tempo Real", "KYRA - Agente IA", "MLflow"],
            label_visibility="collapsed",
        )

        st.divider()
        st.caption(f"Conectado como **{st.session_state.usuario}**")
        if st.button("Sair", use_container_width=True):
            st.session_state.token = None
            st.session_state.usuario = None
            st.rerun()

    if pagina == "Dashboard":
        _pagina_dashboard(requests)
    elif pagina == "Motores":
        _pagina_motores(requests)
    elif pagina == "Tempo Real":
        _pagina_tempo_real()
    elif pagina == "KYRA - Agente IA":
        _pagina_kyra(requests)
    elif pagina == "MLflow":
        _pagina_mlflow()


def _pagina_dashboard(requests):
    import plotly.express as px
    import plotly.graph_objects as go

    st.markdown("## Dashboard da Frota")
    st.caption("Visão geral do status de todos os motores monitorados.")

    with st.spinner("Carregando status da frota..."):
        try:
            r = requests.get("http://localhost:8502/frota/status", headers=_headers(), timeout=60)
            if r.status_code != 200:
                st.error(f"Erro {r.status_code}: {r.text[:200]}")
                return
            dados = r.json()
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return

    resumo = dados.get("resumo", {})

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total de Motores", dados.get("total", 0))
    col2.metric("Normal", resumo.get("normal", 0), delta=None)
    col3.metric("Atencao", resumo.get("atencao", 0))
    col4.metric("Alerta", resumo.get("alerta", 0))
    col5.metric("Critico", resumo.get("critico", 0))

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        fig_pizza = px.pie(
            values=list(resumo.values()),
            names=list(resumo.keys()),
            title="Distribuição por Status",
            color=list(resumo.keys()),
            color_discrete_map={
                "normal": "#3fb950",
                "atencao": "#e3b341",
                "alerta": "#f0883e",
                "critico": "#f85149",
            },
        )
        fig_pizza.update_layout(
            paper_bgcolor="#161b22",
            plot_bgcolor="#161b22",
            font_color="#c9d1d9",
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_b:
        criticos = dados.get("critico", [])
        alertas = dados.get("alerta", [])
        urgentes = criticos + alertas

        if urgentes:
            import pandas as pd
            df_urgentes = pd.DataFrame(urgentes).sort_values("rul_previsto")
            df_urgentes.columns = ["Motor ID", "RUL Previsto", "Ciclo Atual"]
            fig_bar = px.bar(
                df_urgentes,
                x="Motor ID",
                y="RUL Previsto",
                title="Motores Urgentes - RUL Restante",
                color="RUL Previsto",
                color_continuous_scale="Reds_r",
            )
            fig_bar.update_layout(
                paper_bgcolor="#161b22",
                plot_bgcolor="#0d1117",
                font_color="#c9d1d9",
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.success("Nenhum motor em estado critico ou de alerta.")

    if criticos:
        st.error(f"ATENCAO: {len(criticos)} motores em estado CRITICO requerem parada imediata.")
        cols = st.columns(min(len(criticos), 5))
        for i, m in enumerate(criticos[:5]):
            cols[i].metric(
                f"Motor {m['motor_id']}",
                f"{m['rul_previsto']} ciclos",
                delta="CRITICO",
                delta_color="inverse",
            )


def _pagina_motores(requests):
    import plotly.express as px
    import pandas as pd

    st.markdown("## Análise de Motor Individual")

    motor_id = st.number_input("ID do Motor", min_value=1, max_value=20, value=1, step=1)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Analisar RUL", use_container_width=True, type="primary"):
            with st.spinner(f"Calculando RUL do motor {motor_id}..."):
                r = requests.get(
                    f"http://localhost:8502/motores/{motor_id}/rul",
                    headers=_headers(),
                    timeout=15,
                )
                if r.status_code == 200:
                    d = r.json()
                    status = d["status"]
                    cores = {"normal": "🟢", "atencao": "🟡", "alerta": "🟠", "critico": "🔴"}
                    st.metric("RUL Previsto", f"{d['rul_previsto']} ciclos")
                    st.metric("Ciclo Atual", d["ciclo_atual"])
                    st.markdown(f"**Status:** {cores.get(status, '')} `{status.upper()}`")
                else:
                    try:
                        st.error(r.json().get("detail", r.text[:200]))
                    except Exception:
                        st.error(f"Erro {r.status_code}: {r.text[:200]}")

    with col2:
        if st.button("Verificar Anomalias", use_container_width=True):
            with st.spinner(f"Verificando sensores do motor {motor_id}..."):
                r = requests.get(
                    f"http://localhost:8502/motores/{motor_id}/anomalia",
                    headers=_headers(),
                    timeout=15,
                )
                if r.status_code == 200:
                    d = r.json()
                    if d["is_anomalia"]:
                        st.warning(f"Anomalia detectada - Severidade: {d['severidade'].upper()}")
                        st.write("**Sensores suspeitos:**")
                        for s in d["sensores_suspeitos"]:
                            st.code(s)
                    else:
                        st.success("Sensores dentro do padrão normal.")
                    st.metric("Score de Anomalia", d["score"])
                else:
                    try:
                        st.error(r.json().get("detail", r.text[:200]))
                    except Exception:
                        st.error(f"Erro {r.status_code}: {r.text[:200]}")


def _pagina_kyra(requests):
    st.markdown("## KYRA - Agente de Inteligencia Industrial")
    st.caption("Many intelligences. One decision. - Pergunte sobre qualquer motor, sensor ou procedimento.")

    if "historico_chat" not in st.session_state:
        st.session_state.historico_chat = []

    for msg in st.session_state.historico_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    pergunta = st.chat_input("Pergunte sobre motores, sensores ou procedimentos...")

    if pergunta:
        st.session_state.historico_chat.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("KYRA processando..."):
                try:
                    r = requests.post(
                        "http://localhost:8502/agente/consultar",
                        json={"pergunta": pergunta},
                        headers=_headers(),
                        timeout=120,
                    )
                    if r.status_code == 200:
                        resposta = r.json()["resposta"]
                    else:
                        resposta = f"Erro {r.status_code}: {r.text}"
                except Exception as e:
                    resposta = f"Erro de conexao: {e}"

                st.markdown(resposta)
                st.session_state.historico_chat.append({"role": "assistant", "content": resposta})

    if st.session_state.historico_chat:
        if st.button("Limpar conversa"):
            st.session_state.historico_chat = []
            st.rerun()

    with st.expander("Exemplos de perguntas"):
        exemplos = [
            "O que significa eficiencia_hpc e qual a faixa normal?",
            "Qual e o RUL do motor 3?",
            "O motor 5 tem anomalias nos sensores?",
            "Quais motores estao em estado critico agora?",
            "Qual procedimento seguir quando o status e ALERTA?",
        ]
        for e in exemplos:
            st.code(e)


def _pagina_tempo_real():
    import asyncio
    import json
    import threading
    import websocket
    import plotly.graph_objects as go
    from collections import deque
    from datetime import datetime

    st.markdown("## Monitoramento em Tempo Real")
    st.caption("Leituras dos sensores transmitidas via WebSocket a cada 2 segundos.")

    if "ws_ativo" not in st.session_state:
        st.session_state.ws_ativo = False
    if "ws_historico" not in st.session_state:
        st.session_state.ws_historico = {}
    if "ws_ultimas" not in st.session_state:
        st.session_state.ws_ultimas = {}

    col_btn1, col_btn2, _ = st.columns([1, 1, 3])

    with col_btn1:
        iniciar = st.button("Iniciar Stream", type="primary", use_container_width=True,
                            disabled=st.session_state.ws_ativo)
    with col_btn2:
        parar = st.button("Parar", use_container_width=True,
                          disabled=not st.session_state.ws_ativo)

    placeholder_status = st.empty()
    placeholder_metricas = st.empty()
    placeholder_grafico = st.empty()
    placeholder_tabela = st.empty()

    if parar:
        st.session_state.ws_ativo = False
        st.session_state.ws_historico = {}
        st.session_state.ws_ultimas = {}
        st.rerun()

    if iniciar:
        st.session_state.ws_ativo = True
        st.session_state.ws_historico = {}
        st.session_state.ws_ultimas = {}

    if st.session_state.ws_ativo:
        placeholder_status.success("Stream ativo - recebendo leituras dos motores...")

        import time
        import urllib.request

        for _ in range(10):
            try:
                ws = websocket.create_connection(
                    "ws://localhost:8502/ws/sensores",
                    timeout=3,
                )
                msg = ws.recv()
                dados = json.loads(msg)
                ws.close()

                motor_id = dados["motor_id"]
                ts = datetime.now().strftime("%H:%M:%S")

                if motor_id not in st.session_state.ws_historico:
                    st.session_state.ws_historico[motor_id] = deque(maxlen=30)

                st.session_state.ws_historico[motor_id].append({
                    "ts": ts,
                    "temp_saida_hpc": dados.get("temp_saida_hpc", 0),
                    "eficiencia_hpc": dados.get("eficiencia_hpc", 0),
                    "velocidade_core": dados.get("velocidade_core", 0),
                })
                st.session_state.ws_ultimas[motor_id] = dados

            except Exception:
                break

            time.sleep(2)

        ultimas = st.session_state.ws_ultimas
        historico = st.session_state.ws_historico

        if ultimas:
            import pandas as pd

            with placeholder_metricas.container():
                st.markdown("**Última leitura por motor:**")
                cols = st.columns(min(len(ultimas), 5))
                for i, (mid, d) in enumerate(sorted(ultimas.items())[:5]):
                    cols[i].metric(
                        f"Motor {mid}",
                        f"Ciclo {d.get('ciclo', '?')}",
                        delta=f"T={d.get('temp_saida_hpc', 0):.0f}K",
                    )

            motor_sel = sorted(historico.keys())[0]
            hist = list(historico[motor_sel])

            if len(hist) > 1:
                df_hist = pd.DataFrame(hist)
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_hist["ts"],
                    y=df_hist["temp_saida_hpc"],
                    mode="lines+markers",
                    name="Temp. saida HPC",
                    line=dict(color="#58a6ff"),
                ))
                fig.add_trace(go.Scatter(
                    x=df_hist["ts"],
                    y=df_hist["velocidade_core"],
                    mode="lines+markers",
                    name="Velocidade core",
                    line=dict(color="#3fb950"),
                    yaxis="y2",
                ))
                fig.update_layout(
                    title=f"Motor {motor_sel} - Sensores em Tempo Real",
                    paper_bgcolor="#161b22",
                    plot_bgcolor="#0d1117",
                    font_color="#c9d1d9",
                    yaxis=dict(title="Temperatura (K)", color="#58a6ff"),
                    yaxis2=dict(title="Velocidade", overlaying="y", side="right",
                                color="#3fb950"),
                    legend=dict(bgcolor="#161b22"),
                )
                placeholder_grafico.plotly_chart(fig, use_container_width=True)

            df_tab = pd.DataFrame([
                {
                    "Motor": mid,
                    "Ciclo": d.get("ciclo", "-"),
                    "Temp. HPC (K)": round(d.get("temp_saida_hpc", 0), 2),
                    "Efic. HPC": round(d.get("eficiencia_hpc", 0), 5),
                    "Vel. Core": round(d.get("velocidade_core", 0), 2),
                    "Pressão LPT": round(d.get("pressao_saida_lpt", 0), 2),
                }
                for mid, d in sorted(ultimas.items())
            ])
            placeholder_tabela.dataframe(df_tab, use_container_width=True, hide_index=True)

        time.sleep(2)
        st.rerun()
    else:
        placeholder_status.info("Clique em 'Iniciar Stream' para começar a receber leituras em tempo real.")


def _pagina_mlflow():
    st.markdown("## MLflow - Rastreamento de Experimentos")
    st.caption("Histórico completo de treinamentos, métricas e parâmetros dos modelos.")
    st.link_button(
        "Abrir MLflow UI",
        "http://localhost:5001",
        use_container_width=True,
        type="primary",
    )
    st.markdown("""
    **Experimento ativo:** `kymera-rul-prediction`

    | Metrica | Valor |
    |---|---|
    | MAE | ~14.89 ciclos |
    | RMSE | ~19.60 ciclos |
    | R2 | ~0.91 |

    **Modelos salvos:**
    - `modelos/modelo_rul.pkl` - XGBoost RUL prediction
    - `modelos/modelo_anomalia.pkl` - Isolation Forest
    - `modelos/scaler.pkl` - StandardScaler
    - `modelos/feature_cols.pkl` - Feature columns
    """)


if __name__ == "__main__":
    main()
