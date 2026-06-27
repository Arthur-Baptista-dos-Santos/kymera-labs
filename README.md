# `Kymera Labs`

> **Many intelligences. One decision.** *Where AI thinks together.*
>
> Plataforma de manutenção preditiva industrial com arquitetura Agentic RAG. Monitora turbinas industriais em tempo real, prevê falhas antes que aconteçam e responde perguntas técnicas com uma IA especializada chamada KYRA.

---

## `Tecnologias`

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20%2B%20WebSocket-009688)
![XGBoost](https://img.shields.io/badge/XGBoost-Predição%20RUL-orange)
![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-blueviolet)
![Ollama](https://img.shields.io/badge/Ollama-Mistral%207B-purple)
![MLflow](https://img.shields.io/badge/MLflow-Experiment%20Tracking-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-ff4b4b)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![JWT](https://img.shields.io/badge/JWT-Autenticação-black)

---

## `O que faz`

Recebe leituras de 21 sensores de turbinas industriais e as processa em três camadas de inteligência simultâneas. O modelo XGBoost prevê quantos ciclos restam antes da falha (RUL). O Isolation Forest detecta leituras anômalas em tempo real via WebSocket. O agente KYRA roteia perguntas dos operadores entre a base de conhecimento técnico (ChromaDB + RAG) e os modelos de ML, sintetizando respostas em linguagem natural com o Mistral 7B local. Tudo é exposto via API REST autenticada com JWT e visualizado em um dashboard interativo.

---

## `Fluxo do agente KYRA`

```
Pergunta do operador
        |
        v
  [ Roteador KYRA ]
  /      |      \       \
RAG    RUL   Anomalia  Frota
 |      |       |        |
 v      v       v        v
ChromaDB  XGBoost  IsoForest  Todos os motores
        \    |      /     /
         v   v     v    v
        [ Mistral 7B local ]
                |
                v
        Resposta em PT-BR com fonte citada
```

---

## `Arquitetura`

```
kymera-labs/
├── backend/
│   ├── agente/
│   │   ├── rag.py          # Pipeline RAG com ChromaDB + nomic-embed-text
│   │   └── roteador.py     # KYRA: roteamento deterministico + sintese LLM
│   ├── api/
│   │   └── app.py          # FastAPI: REST + WebSocket (porta 8502)
│   ├── ml/
│   │   ├── features.py     # Engenharia de features (71 features por motor)
│   │   ├── preditor.py     # Inferencia: RUL e deteccao de anomalias
│   │   └── treinar.py      # Treinamento XGBoost + Isolation Forest
│   └── seguranca/
│       └── auth.py         # JWT HS256 + bcrypt
├── dados/
│   ├── gerar_dados.py      # Gerador sintetico padrao NASA CMAPSS
│   └── raw/                # CSVs de treino e teste (gitignored)
├── documentos/             # Base de conhecimento para RAG (31 chunks)
│   ├── guia_alertas.md
│   ├── manual_sensores.md
│   └── procedimentos_manutencao.md
├── frontend/
│   └── app.py              # Dashboard Streamlit (porta 8503)
├── modelos/                # Modelos treinados .pkl (gitignored)
├── docker-compose.yml      # PostgreSQL, Redis, ChromaDB, MLflow
├── .env.example
└── requirements.txt
```

---

## `Resultados do modelo`

| Metrica | Valor |
|---|---|
| MAE | 14,89 ciclos |
| RMSE | 19,60 ciclos |
| R² | 0,91 |
| Dataset | 80 motores treino / 20 teste (padrao NASA CMAPSS) |
| Features | 71 (medias e desvios padrao moveis em janelas de 5, 10 e 20 ciclos) |
| Algoritmo de predição | XGBoost (n_estimators=400, max_depth=6, lr=0.05) |
| Detecção de anomalias | Isolation Forest (contamination=0.05) |

---

## `Endpoints da API`

| Método | Rota | Descricao |
|---|---|---|
| `POST` | `/auth/login` | Autenticação e geração de token JWT |
| `GET` | `/motores/{id}/rul` | Previsão de vida útil restante |
| `GET` | `/motores/{id}/anomalia` | Detecção de anomalia nos sensores |
| `GET` | `/frota/status` | Status de todos os motores monitorados |
| `POST` | `/agente/consultar` | Consulta ao agente KYRA |
| `WS` | `/ws/sensores` | Stream de leituras em tempo real |
| `GET` | `/health` | Health check da API |

---

## `Pré-requisitos`

- Python 3.10+
- Docker Desktop
- Ollama com `mistral` e `nomic-embed-text` disponíveis

```bash
ollama pull mistral
ollama pull nomic-embed-text
```

---

## `Como rodar`

```bash
git clone https://github.com/Arthur-Baptista-dos-Santos/kymera-labs.git
cd kymera-labs

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

```bash
# Copiar e configurar variaveis de ambiente
cp .env.example .env

# Subir a infraestrutura (PostgreSQL, Redis, ChromaDB, MLflow)
docker compose up -d
```

```bash
# Gerar dataset sintetico e treinar os modelos
python dados/gerar_dados.py
python -m backend.ml.treinar

# Indexar a base de conhecimento no ChromaDB
python -m backend.agente.rag
```

```bash
# Iniciar a API (porta 8502)
uvicorn backend.api.app:app --host 0.0.0.0 --port 8502 --reload

# Em outro terminal - dashboard (porta 8503)
streamlit run frontend/app.py --server.port 8503
```

Acesse `http://localhost:8503`, faça login com `admin / kymera2026` e explore o dashboard.

Swagger UI disponível em `http://localhost:8502/docs` - MLflow em `http://localhost:5001`.

---

## `Autenticação`

| Usuário | Senha | Perfil |
|---|---|---|
| `admin` | `kymera2026` | Acesso total |
| `operador` | `operador123` | Acesso de leitura |

> Troque as senhas e o `JWT_SECRET_KEY` no `.env` antes de qualquer deploy em produção.

---

## `Conceitos aplicados`

- **`Agentic RAG`**: roteamento deterministico entre RAG, predição ML e detecção de anomalias com sintese via LLM local
- **`XGBoost`**: gradient boosting para regressão do RUL (Remaining Useful Life) com MAE de 14,89 ciclos
- **`Isolation Forest`**: detecção de anomalias não supervisionada para identificar leituras fora do padrão
- **`ChromaDB + RAG`**: base de conhecimento vetorizada com busca semântica para responder perguntas técnicas
- **`FastAPI + JWT`**: API REST com autenticação stateless, rate limiting por IP e WebSocket para dados em tempo real
- **`MLflow`**: rastreamento de experimentos, parâmetros, métricas e artefatos de cada treinamento
- **`Docker Compose`**: infraestrutura completa reprodutível em um comando
- **`Ollama`**: inferência local de LLMs sem custo de API e com privacidade total dos dados industriais
- **`NASA CMAPSS`**: padrão de dataset de degradação de turbofans usado como referência na literatura de manutenção preditiva
