# ETICE — SAC · Sistema de Acompanhamento de Contratos

Sistema de consulta inteligente e gestão dos contratos de fornecedores de nuvem da ETICE, combinando um agente conversacional ReAct com uma API REST de CRUD.

---

## Visão geral

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend                              │
└────────────┬────────────────────────────┬───────────────────┘
             │ Chat (SSE)                 │ CRUD REST
             ▼                            ▼
┌────────────────────────┐   ┌────────────────────────────────┐
│   Agente ReAct         │   │   API REST (FastAPI)           │
│   LangGraph + Gemini   │   │   /contratos                   │
│   2.5 Flash            │   │   /ordens-servico              │
└────────────┬───────────┘   └──────────────┬─────────────────┘
             │ MCP stdio                     │ SQLAlchemy
             ▼                               ▼
┌────────────────────────┐   ┌────────────────────────────────┐
│   MCP Server (15 tools)│   │   db_writer.py                 │
│   mcp_server/server.py │   │   sac_writer (INSERT/UPDATE/   │
│   sac_reader (SELECT)  │   │   DELETE/SELECT)               │
└────────────┬───────────┘   └──────────────┬─────────────────┘
             └──────────────┬───────────────┘
                            ▼
              ┌─────────────────────────┐
              │  MariaDB :3307          │
              │  etice_contratos        │
              └─────────────────────────┘
```

---

## Pré-requisitos

- Python 3.12+
- MariaDB (porta padrão do projeto: **3307**)
- Chave de API do Google AI Studio (`GOOGLE_API_KEY`)

---

## Instalação

```bash
# 1. Clonar e entrar no projeto
git clone https://github.com/Aquinator/etice_mcp.git
cd etice_mcp

# 2. Criar e ativar o ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com as credenciais reais
```

---

## Configuração do banco

### Usuários

Criar os dois usuários com privilégios mínimos (como root no MariaDB):

```sql
-- Leitura — usado pelo agente MCP
CREATE USER IF NOT EXISTS 'sac_reader'@'%' IDENTIFIED BY '<senha>';
GRANT SELECT ON etice_contratos.* TO 'sac_reader'@'%';

-- Escrita — usado pela API CRUD
CREATE USER IF NOT EXISTS 'sac_writer'@'%' IDENTIFIED BY '<senha>';
GRANT SELECT, INSERT, UPDATE, DELETE ON etice_contratos.* TO 'sac_writer'@'%';

FLUSH PRIVILEGES;
```

### Migrations

Aplicar na ordem (a partir da raiz do projeto):

```bash
mysql -u root -p -P 3307 etice_contratos < db/migrations/001_create_ordem_servico.sql
mysql -u root -p -P 3307 etice_contratos < db/migrations/002_create_ordem_servico_item.sql
mysql -u root -p -P 3307 etice_contratos < db/migrations/003_create_view_saldo_contrato.sql
mysql -u root -p -P 3307 etice_contratos < db/migrations/004_seed_os_reais.sql
mysql -u root -p -P 3307 etice_contratos < db/migrations/005_create_contrato_recurso.sql
mysql -u root -p -P 3307 etice_contratos < db/migrations/006_seed_recursos_contrato.sql
mysql -u root -p -P 3307 etice_contratos < db/migrations/007_add_chave_recurso.sql
```

---

## Execução

```bash
uvicorn api.main:app --reload --port 8000
```

O servidor MCP sobe automaticamente como subprocesso via stdio durante o startup do uvicorn.

Verificar:
```bash
curl http://localhost:8000/health
# {"status":"ok","agente_pronto":true,"total_tools":15,"versao":"1.0.0"}
```

Documentação interativa disponível em:
- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc`

---

## Estrutura do projeto

```
etice_mcp/
├── .env                          # variáveis de ambiente (não versionado)
├── .env.example                  # template
├── requirements.txt
│
├── db/
│   └── migrations/               # scripts SQL em ordem numerada
│
├── logs/
│   ├── etice_client.log          # agente, sessões, API
│   └── etice_server.log          # tool calls, SQL, MCP
│
├── mcp_server/
│   ├── db.py                     # engine SQLAlchemy (sac_reader)
│   └── server.py                 # 15 tools MCP (somente leitura)
│
├── mcp_client/
│   ├── agent.py                  # AppState + agente ReAct LangGraph
│   ├── chat.py
│   └── logging_config.py
│
└── api/
    ├── main.py                   # FastAPI + lifespan + routers
    ├── db_writer.py              # engine SQLAlchemy (sac_writer)
    ├── sessions.py               # SessionRegistry
    ├── dependencies.py
    ├── models/
    │   ├── __init__.py
    │   ├── chat.py               # schemas de sessão e chat
    │   ├── contrato.py           # ContratoOut, CriarContratoInput, EditarContratoInput
    │   └── ordem_servico.py      # OSOut, CriarOSInput, EditarOSInput, OSItemInput
    ├── services/
    │   └── saldo_service.py      # lógica de saldo e criticidade
    └── routers/
        ├── health.py
        ├── sessoes.py
        ├── chat.py               # SSE streaming
        ├── contratos.py          # CRUD /contratos
        └── ordens_servico.py     # CRUD /ordens-servico
```

---

## API — endpoints

### Chat (agente)

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/sessoes` | Cria sessão de chat |
| `GET` | `/sessoes/{id}` | Info da sessão |
| `DELETE` | `/sessoes/{id}` | Encerra sessão |
| `POST` | `/sessoes/{id}/chat` | Envia mensagem (resposta em SSE) |
| `GET` | `/sessoes/{id}/historico` | Histórico de mensagens |

### Eventos SSE

```
event: heartbeat    data: ping                        keep-alive a cada 15s
event: token        data: "<chunk>"                   fragmento de texto do LLM
event: fim          data: [DONE]                      stream encerrado com sucesso
event: sessao_reset data: {"novo_session_id": "...",  histórico corrompido —
                           "mensagem": "..."}         frontend deve trocar session_id
event: erro         data: "<mensagem>"                falha durante o stream
```

O evento `sessao_reset` é emitido quando o histórico da sessão fica corrompido
(ex: erro durante uma tool call). O frontend deve atualizar o `session_id` e
exibir a mensagem ao usuário — sem precisar recarregar a página.

### CRUD — Contratos

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/contratos` | Lista paginada (`?limite=20&offset=0&status_con=ativo`) |
| `GET` | `/contratos/{id}` | Detalhe |
| `GET` | `/contratos/{id}/saldo` | Saldo financeiro e criticidade |
| `POST` | `/contratos` | Criar |
| `PUT` | `/contratos/{id}` | Editar |
| `DELETE` | `/contratos/{id}` | Excluir (409 se houver OS vinculadas) |

### CRUD — Ordens de Serviço

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/ordens-servico` | Lista (`?id_contrato=N&limite=20`) |
| `GET` | `/ordens-servico/{id}` | Detalhe com itens |
| `POST` | `/ordens-servico` | Criar OS com itens (transação atômica) |
| `PUT` | `/ordens-servico/{id}` | Editar cabeçalho |
| `DELETE` | `/ordens-servico/{id}` | Excluir (cascata nos itens) |

---

## Tools do agente (15)

| Tool | O que responde |
|------|----------------|
| `listar_contratos` | Resumo paginado de contratos |
| `listar_gerentes` | Todos os gestores cadastrados |
| `listar_empresas` | Empresas com contagem e valor total |
| `buscar_contrato` | Busca por número, empresa ou termo no objeto |
| `detalhar_contrato` | Todos os campos de um contrato |
| `estatisticas_contratos` | Totais por modalidade |
| `ranking_contratos` | Contratos ordenados por valor |
| `analise_agregada_gerencial` | Ranking de gestores por volume financeiro |
| `analise_vencimentos` | Contratos a vencer em N meses |
| `historico_empresa` | Histórico completo de uma empresa |
| `estatisticas_anuais` | Quantidade e valor por ano de assinatura |
| `estatisticas_vigencia` | Média/min/max de duração dos contratos |
| `consultar_saldo_contrato` | Saldo financeiro em R$ e criticidade |
| `consultar_recursos_contrato` | Saldo em unidade (UST, licença, etc.) com valor unitário |
| `listar_ordens_servico_contrato` | OS de um contrato com itens e valores |

---

## Banco de dados — modelo resumido

```
tb_contrato_con  (tabela central)
    │
    ├── tb_contrato_recurso_cre   (tabela de preços: UST, licenças, etc.)
    │
    ├── tb_ordem_servico_ord      (ordens de serviço)
    │       └── tb_ordem_servico_item_osi  (itens da OS — cascata no DELETE)
    │
    └── vw_saldo_contrato         (view: valor total − consumido nas OS)
```

**Regras de integridade:**
- Excluir contrato com OS vinculadas → bloqueado (`RESTRICT`)
- Excluir OS → itens excluídos automaticamente (`CASCADE`)
- `sac_writer` não tem `DROP`, `ALTER`, `CREATE` — escopo mínimo

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

## Observações de dados históricos

Alguns campos de contratos importados têm formatos não padronizados:
- `dat_prazo_vigencia_meses_con` pode conter texto livre como `'1 ano(s) (12 meses)'`
- `data_fim_vigencia_con` pode estar no formato `DD/MM/AAAA` em vez de ISO 8601

A API serializa esses campos como `string` e deixa a conversão a cargo do frontend.