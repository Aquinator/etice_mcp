# ETICE — Agente de Contratos de Nuvem

Sistema de consulta inteligente aos contratos de fornecedores de nuvem da ETICE via agente ReAct (LangGraph + Gemini + MCP).

---

## Arquitetura

```
MariaDB
  ↓ pymysql
mcp_server/   (FastMCP — subprocesso stdio)
  12 tools SQL retornam texto puro
  ↓ protocolo MCP
mcp_client/   (LangGraph ReAct — processo principal)
  LLM recebe resultado das tools e responde em texto
  ↓ invocar_stream() — AsyncGenerator[str]
api/          (FastAPI — HTTP/SSE)
  event: token      → chunk de texto do LLM
  event: heartbeat  → keep-alive a cada 15s
  event: fim        → stream encerrado
  event: sessao_reset → recuperação automática de histórico corrompido
  event: erro       → falha durante o stream
  ↓ proxy /api/* (Next.js)
frontend/     (Next.js 14 — localhost:3000)
  Dashboard de KPIs + Chat com streaming token a token
```

---

## Estrutura

```
etice_mcp/
│
├── .env.example                 # Template de variáveis de ambiente
├── .gitignore
├── requirements.txt             # Dependências Python
├── run_server.py                # Entrypoint para o MCP Inspector
│
├── logs/                        # Criado automaticamente em runtime
│   ├── etice_client.log         # Logs do agente e da API (5 MB × 3 backups)
│   └── etice_server.log         # Logs das tools MCP (5 MB × 3 backups)
│
├── mcp_server/
│   ├── __init__.py
│   └── db.py                    # Pool SQLAlchemy + query()
│
├── mcp_client/
│   ├── __init__.py
│   ├── logging_config.py        # RotatingFileHandler compartilhado
│   ├── agent.py                 # AppState, invocar_stream()
│   └── chat.py                  # REPL de terminal com streaming
│
└── api/
    ├── __init__.py
    ├── main.py                  # FastAPI app + lifespan + CORS
    ├── models.py                # Schemas Pydantic
    ├── sessions.py              # SessionRegistry em memória
    ├── dependencies.py          # Depends() injetáveis
    └── routers/
        ├── __init__.py
        ├── health.py            # GET /health
        ├── sessoes.py           # CRUD de sessões
        └── chat.py              # POST /sessoes/{id}/chat — SSE
```

---

## Tools disponíveis

| Tool | Descrição |
|---|---|
| `listar_contratos` | Lista os N contratos mais recentes (resumo) |
| `listar_gerentes` | Lista todos os gestores cadastrados |
| `listar_empresas` | Lista empresas com quantidade de contratos e valor total |
| `buscar_contrato` | Busca por número, empresa ou trecho do objeto |
| `detalhar_contrato` | Ficha completa de um contrato por ID |
| `ranking_contratos` | Contratos ordenados por valor ou data |
| `estatisticas_contratos` | Agrega valor total e quantidade por modalidade |
| `analise_agregada_gerencial` | Ranking de gestores por volume financeiro |
| `analise_vencimentos` | Contratos vencendo nos próximos N meses |
| `historico_empresa` | Resumo do relacionamento com uma empresa |
| `estatisticas_anuais` | Totais e médias agrupados por ano de assinatura |
| `estatisticas_vigencia` | Média, mínimo e máximo de vigência em meses |

---

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```env
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_DB=nome_do_banco
MARIADB_USER=seu_usuario
MARIADB_PASS=sua_senha

GOOGLE_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.5-flash
```

---

## Setup

```bash
cd etice_mcp
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

### API REST

```bash
uvicorn api.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- Health:     http://localhost:8000/health

### CLI (sem frontend)

```bash
python -m mcp_client.chat
```

---

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Status do agente e tools |
| `POST` | `/sessoes` | Cria sessão de chat |
| `GET` | `/sessoes/{id}` | Metadados da sessão |
| `GET` | `/sessoes/{id}/historico` | Histórico de mensagens |
| `DELETE` | `/sessoes/{id}` | Encerra sessão |
| `POST` | `/sessoes/{id}/chat` | Chat SSE |

### Eventos SSE

```
event: heartbeat    data: ping            keep-alive a cada 15s
event: token        data: "<chunk>"       fragmento de texto do LLM
event: fim          data: [DONE]          stream encerrado com sucesso
event: sessao_reset data: {"novo_session_id": "...", "mensagem": "..."}
event: erro         data: "<mensagem>"    falha durante o stream
```

O evento `sessao_reset` é emitido quando o histórico da sessão fica corrompido
(ex: erro durante uma tool call). O frontend deve atualizar o `session_id` e
exibir a mensagem ao usuário — sem precisar recarregar a página.

---

## Logs

| Arquivo | Conteúdo |
|---|---|
| `logs/etice_client.log` | Inicialização do agente, invocações, sessões, erros da API |
| `logs/etice_server.log` | Tool calls, parâmetros, latências SQL, erros do servidor MCP |

Ambos rodam com `RotatingFileHandler`: 5 MB por arquivo, 3 backups (~15 MB máximo cada).
Para acompanhar em tempo real:

```bash
# PowerShell
Get-Content logs\etice_server.log -Wait

# bash
tail -f logs/etice_server.log
```

---

## A fazer

**Persistência de histórico entre reinicios**
```python
# Em mcp_client/agent.py
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
memory = AsyncSqliteSaver.from_conn_string("checkpoints.db")
```