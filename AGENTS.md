# AGENTS.md — Guia para agentes de IA

Este arquivo descreve o projeto para agentes de IA que precisam navegar, modificar ou gerar código neste repositório.

---

## Resumo do Projeto

POC de um agente SDR (_Sales Development Representative_) para imobiliárias, desenvolvido para o **Tech Challenge — Fase 5 da POSTECH/FIAP**. O sistema usa IA generativa local (Ollama) para atender leads via canal de texto, coletar preferências imobiliárias de forma conversacional e qualificá-los para o corretor.

O repositório contém dois módulos independentes:

- **`agente/`** — API backend em Python com FastAPI, SQLite e Ollama. Já implementado e testado.
- **`frontend/`** _(a criar)_ — Interface web em React, separada do backend.

---

## Stack Tecnológica

### Backend (`agente/`)

| Componente | Tecnologia | Versão mínima |
|---|---|---|
| Linguagem | Python | 3.11 |
| Framework web | FastAPI | 0.115 |
| Servidor ASGI | Uvicorn | 0.34 |
| Banco de dados | SQLite (WAL) | embutido no Python |
| ORM / Acesso a dados | sqlite3 nativo | — |
| Validação | Pydantic v2 | 2.10 |
| Cliente HTTP | httpx | 0.28 |
| LLM local | Ollama (`qwen3:4b`) | 0.6.2 |
| Testes | pytest + FastAPI TestClient | 8.x |

### Frontend (`frontend/`) _(a criar)_

| Componente | Tecnologia |
|---|---|
| Linguagem | JavaScript / JSX (TypeScript opcional) |
| Framework | React (versão estável mais recente) |
| Ferramenta de build | Vite ou Create React App |
| Gerenciador de pacotes | npm |

---

## Estrutura de Pastas

```
projeto-hackaton-imobiliaria/
├── agente/                     # Módulo backend (não modificar sem necessidade)
│   ├── app.py                  # Endpoints FastAPI, validação de entrada e fluxo do agente
│   ├── database.py             # Esquema SQLite, migrações e todas as operações de banco
│   ├── llm.py                  # Configuração do Ollama, prompts e validação de respostas
│   ├── requirements.txt        # Dependências Python do backend
│   ├── imobiliaria.sqlite3     # Banco de dados (gerado automaticamente; não versionar)
│   ├── interface-teste/        # Cliente web estático para testes manuais (não é o frontend React)
│   │   ├── index.html
│   │   ├── config.js
│   │   ├── iniciar-api.ps1
│   │   └── README.md
│   └── tests/
│       └── test_api.py         # Testes de integração do backend
├── doc-specs/                  # Documentação e especificações
│   ├── tarefa.md               # História de usuário original (não editar)
│   ├── tarefa.txt              # Versão texto da tarefa (não editar)
│   ├── sdd.txt                 # Log de sessão de especificação (não editar)
│   └── PRD.md                  # Product Requirements Document (gerado)
├── AGENTS.md                   # Este arquivo
├── README.md                   # Visão geral do projeto
└── frontend/                   # (A CRIAR) Projeto React standalone
    ├── src/
    │   └── App.jsx             # Componente raiz com "Hello World"
    ├── public/
    ├── package.json
    └── README.md
```

---

## Padrões e Convenções do Projeto

### Backend

- **Separação de responsabilidades rígida:** `app.py` nunca acessa o banco diretamente nem importa `ollama`. `database.py` não importa `llm.py` nem FastAPI. `llm.py` não acessa banco nem API.
- **Transações curtas:** a IA roda _fora_ das transações SQLite. O padrão é: abrir transação → gravar intent → fechar transação → chamar IA → abrir transação → gravar resultado.
- **Bloqueio por conversa:** cada conversa tem `LockToken` e `LockAte`. Use sempre `BEGIN IMMEDIATE` para operações que precisam de exclusividade.
- **Erros tipados:** `DatabaseError(status_code, detail)` e `LLMError` são os únicos tipos de exceção lançados pelos módulos internos. A API os traduz para HTTP.
- **Sem estado em memória:** nenhuma sessão ou contexto de conversa é mantido em memória entre requisições. Tudo vem do SQLite a cada chamada.
- **Migrations automáticas:** `init_db()` sempre adiciona colunas faltantes com `ALTER TABLE … ADD COLUMN … DEFAULT …` sem recriar tabelas. Preserve esse padrão.
- **Variáveis de ambiente:** `DATABASE_PATH`, `OLLAMA_URL`, `OLLAMA_MODEL`, `API_KEY`, `CORS_ORIGINS`. Sem `API_KEY`, a API funciona sem autenticação.
- **CORS desabilitado por padrão:** middleware só é adicionado se `CORS_ORIGINS` estiver definido e não vazio.
- **Testes:** usam SQLite em diretório temporário (`tmp_path`) e `monkeypatch` para substituir `llm.chat`. Nunca mockar `database`. Os testes devem ser executados com `pytest -q` dentro da pasta `agente/` com o venv ativado.

### Frontend

- Manter o projeto React em uma pasta de nível raiz separada de `agente/` (ex.: `frontend/`).
- Usar a versão estável mais recente do React disponível via npm.
- Não incluir arquivos do backend (`app.py`, `database.py`, etc.) dentro da pasta do frontend.
- Porta padrão do frontend deve diferir de `8000` (porta padrão da API).
- O `README.md` do frontend deve ter pelo menos os comandos `npm install` e `npm start` / `npm run dev`.

---

## Limitações dos Agentes (Do's e Don'ts)

### ✅ Pode fazer

- Criar a pasta `frontend/` na raiz com um projeto React novo.
- Instalar dependências npm dentro de `frontend/`.
- Criar ou editar arquivos dentro de `agente/tests/` para novos cenários de teste.
- Ler qualquer arquivo do repositório para entender o contexto.
- Gerar documentação em `doc-specs/`.
- Modificar `agente/interface-teste/` (ferramenta de teste manual, não é produção).
- Adicionar variáveis de ambiente documentadas no `README.md` do agente.

### ❌ Não deve fazer

- **Não misturar** o código do frontend com o código do backend na mesma pasta.
- **Não modificar** `agente/app.py`, `agente/database.py` ou `agente/llm.py` sem necessidade explícita — esses arquivos são o núcleo estável do backend.
- **Não deletar** `agente/imobiliaria.sqlite3` — contém dados de conversas existentes.
- **Não versionar** arquivos `*.sqlite3`, `*.sqlite3-shm`, `*.sqlite3-wal` (já no `.gitignore`).
- **Não adicionar** estado de conversa em variáveis globais do processo Python — o design é stateless por requisição.
- **Não mockar `database`** nos testes — os testes usam SQLite real em diretório temporário. Isso é intencional para detectar divergências entre mock e banco real.
- **Não usar** `BEGIN` implícito em operações que exigem `BEGIN IMMEDIATE` — locks SQLite são críticos para a consistência do fluxo de agente.
- **Não chamar** endpoints da API diretamente a partir de `llm.py` — o módulo de LLM é isolado por design.
- **Não assumir** que o modelo Ollama (`qwen3:4b`) está disponível nos testes — os testes sempre substituem `llm.chat` via `monkeypatch`.
- **Não configurar** `CORS_ORIGINS` em testes automáticos — pode causar comportamento inesperado no middleware.
- **Não usar** `--no-verify` em commits — os hooks devem ser respeitados.

---

## Comandos Úteis

```powershell
# Iniciar o backend
cd agente
.\.venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 8000

# Rodar os testes do backend
cd agente
.\.venv\Scripts\python -m pytest -q

# Iniciar o backend com CORS liberado para a interface de teste
cd agente
.\interface-teste\iniciar-api.ps1

# Servir a interface de teste estática
cd agente
python -m http.server 5500 --bind 127.0.0.1 --directory interface-teste

# Criar o projeto React (a executar na raiz do repositório)
npm create vite@latest frontend -- --template react
cd frontend && npm install && npm run dev
```

---

## Variáveis de Ambiente do Backend

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_PATH` | `imobiliaria.sqlite3` | Caminho do arquivo SQLite |
| `OLLAMA_URL` | `http://localhost:11434` | URL do servidor Ollama |
| `OLLAMA_MODEL` | `qwen3:4b` | Modelo LLM a usar |
| `API_KEY` | _(vazio)_ | Chave de autenticação; sem valor, sem autenticação |
| `CORS_ORIGINS` | _(vazio)_ | Origens permitidas, separadas por vírgula |
