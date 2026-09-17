# AGENTS.md — Guia para agentes de IA

Este arquivo descreve o projeto para agentes de IA que precisam navegar, modificar ou gerar código neste repositório.

---

## Resumo do Projeto

POC de um agente SDR (_Sales Development Representative_) para imobiliárias, desenvolvido para o **Tech Challenge — Fase 5 da POSTECH/FIAP**. O sistema usa IA generativa local (Ollama) para atender leads via canal de texto, coletar preferências imobiliárias de forma conversacional e qualificá-los para o corretor.

O repositório contém dois módulos independentes:

- **`agente/`** — API backend em Python com FastAPI, SQLite e Ollama. Implementado e testado com 14 testes de integração.
- **`frontend/`** — Interface web em React (Vite). Scaffolding criado; próxima entrega é o CRUD de usuários (ver `doc-specs/tarefa.md`).

**História de usuário ativa:** CRUD de usuários no frontend com persistência SQLite em `database/`, separação SOLID de responsabilidades e interface responsiva.

---

## Stack Tecnológica

### Backend (`agente/`)

| Componente | Tecnologia | Versão mínima |
|---|---|---|
| Linguagem | Python | 3.11 |
| Framework web | FastAPI | 0.115 |
| Servidor ASGI | Uvicorn | 0.34 |
| Banco de dados | SQLite (WAL) | embutido no Python |
| Acesso a dados | sqlite3 nativo | — |
| Validação | Pydantic v2 | 2.10 |
| Cliente HTTP | httpx | 0.28 |
| LLM local | Ollama (`qwen3:4b`) | 0.6.2 |
| Testes | pytest + FastAPI TestClient | 8.x |

### Frontend (`frontend/`)

| Componente | Tecnologia | Versão |
|---|---|---|
| Linguagem | JavaScript / JSX | ES2022+ |
| Framework | React | estável mais recente |
| Build tool | Vite | estável mais recente |
| Gerenciador de pacotes | npm | — |
| Linter | oxlint | configurado em `.oxlintrc.json` |

---

## Estrutura de Pastas

```
projeto-hackaton-imobiliaria/
├── agente/                      # Módulo backend (núcleo estável — não modificar sem necessidade)
│   ├── app.py                   # Endpoints FastAPI, validação de entrada e fluxo do agente
│   ├── database.py              # Esquema SQLite, migrações e todas as operações de banco
│   ├── llm.py                   # Configuração do Ollama, prompts e validação de respostas
│   ├── requirements.txt         # Dependências Python do backend
│   ├── imobiliaria.sqlite3      # Banco de dados (gerado automaticamente; não versionar)
│   ├── interface-teste/         # Cliente web estático para testes manuais (não é o frontend React)
│   │   ├── index.html
│   │   ├── config.js
│   │   ├── iniciar-api.ps1
│   │   └── README.md
│   └── tests/
│       └── test_api.py          # 14 testes de integração do backend
├── doc-specs/                   # Documentação e especificações (não editar tarefa.*)
│   ├── tarefa.md                # História de usuário ativa (não editar)
│   ├── tarefa.txt               # Versão texto da tarefa (não editar)
│   └── PRD.md                   # Product Requirements Document (gerado)
├── frontend/                    # Projeto React standalone (Vite)
│   ├── src/
│   │   ├── main.jsx             # Entry point React
│   │   ├── App.jsx              # Componente raiz (a implementar CRUD)
│   │   ├── App.css              # Estilos globais
│   │   └── index.css            # Reset e variáveis CSS
│   ├── public/
│   │   └── favicon.svg
│   ├── index.html               # HTML raiz do Vite
│   ├── vite.config.js           # Configuração Vite + plugin React
│   ├── .oxlintrc.json           # Configuração do linter
│   └── package.json
├── api/                         # (A CRIAR) API Python para o frontend do corretor (porta 8001)
│   ├── app.py                   # Endpoints FastAPI do lado do corretor
│   ├── database.py              # Acesso ao SQLite de usuários/imóveis/leads
│   └── requirements.txt         # Dependências Python da api/
├── database/                    # (A CRIAR) Banco SQLite do CRUD de usuários
│   └── usuarios.sqlite3         # Gerado automaticamente; não versionar
├── AGENTS.md                    # Este arquivo
└── README.md                    # Visão geral do projeto
```

---

## Padrões e Convenções do Projeto

### Backend

- **Separação rígida de responsabilidades:** `app.py` nunca acessa o banco diretamente nem importa `ollama`. `database.py` não importa `llm.py` nem FastAPI. `llm.py` não acessa banco nem a camada HTTP.
- **Stateless por requisição:** nenhuma sessão ou contexto de conversa é mantido em memória entre requisições. Tudo vem do SQLite a cada chamada.
- **Transações curtas:** a IA roda _fora_ das transações SQLite. Padrão: abrir transação → gravar intent → fechar → chamar IA → abrir transação → gravar resultado.
- **Bloqueio por conversa:** cada conversa tem `LockToken` e `LockAte`. Use sempre `BEGIN IMMEDIATE` para operações que exigem exclusividade.
- **Erros tipados:** `DatabaseError(status_code, detail)` e `LLMError` são os únicos tipos de exceção lançados pelos módulos internos. A API os traduz para HTTP.
- **Migrations automáticas:** `init_db()` sempre adiciona colunas faltantes com `ALTER TABLE … ADD COLUMN … DEFAULT …` sem recriar tabelas. Preserve esse padrão.
- **Variáveis de ambiente:** `DATABASE_PATH`, `OLLAMA_URL`, `OLLAMA_MODEL`, `API_KEY`, `CORS_ORIGINS`. Sem `API_KEY`, a API funciona sem autenticação.
- **CORS desabilitado por padrão:** middleware só é adicionado se `CORS_ORIGINS` estiver definido e não vazio.
- **Testes:** usam SQLite em diretório temporário (`tmp_path`) e `monkeypatch` para substituir `llm.chat`. Nunca mockar `database`. Executar com `pytest -q` dentro de `agente/` com o venv ativado.

### Frontend

- Manter o projeto React na pasta `frontend/` na raiz; nunca misturar com `agente/`.
- **CRUD de usuários:** separar em camadas — `services/` (acesso à API), `components/` (UI), `pages/` (composição). Sem lógica de banco diretamente em componentes.
- **Banco do CRUD:** SQLite em `database/` na raiz (fora de `agente/`), servido por uma API Python separada (porta diferente de 8000).
- **Senhas:** armazenar sempre como hash (bcrypt); nunca retornar senha em respostas de API.
- **Validações:** nome sem dígitos, email com formato válido, telefone somente numérico, senha mínima de 8 caracteres. Validar antes do envio e exibir feedback inline.
- Porta padrão do frontend deve diferir de `8000`.
- Componentes de UI: usar biblioteca moderna (shadcn/ui, MUI, Ant Design, ou similar) — não reinventar componentes base.
- Responsivo: funcionar em 375 px (mobile) e 1280 px (desktop).

---

## Limitações dos Agentes (Do's e Don'ts)

### ✅ Pode fazer

- Criar e editar arquivos dentro de `frontend/src/` para implementar o CRUD.
- Criar a pasta `database/` na raiz para o SQLite do CRUD.
- Criar e expandir a pasta `api/` na raiz para serviços do frontend do corretor (CRUD de usuários, futuros endpoints de imóveis e leads), separado de `agente/`.
- Instalar dependências npm dentro de `frontend/`.
- Criar ou editar arquivos dentro de `agente/tests/` para novos cenários de teste.
- Ler qualquer arquivo do repositório para entender o contexto.
- Gerar ou atualizar documentação em `doc-specs/`.
- Modificar `agente/interface-teste/` (ferramenta de teste manual, não é produção).
- Adicionar variáveis de ambiente documentadas no README correspondente.

### ❌ Não deve fazer

- **Não misturar** código do frontend com código do backend na mesma pasta.
- **Não modificar** `agente/app.py`, `agente/database.py` ou `agente/llm.py` sem necessidade explícita — esses arquivos são o núcleo estável do backend.
- **Não deletar** `agente/imobiliaria.sqlite3` — contém dados de conversas existentes.
- **Não versionar** arquivos `*.sqlite3`, `*.sqlite3-shm`, `*.sqlite3-wal` (já no `.gitignore`).
- **Não adicionar** estado de conversa em variáveis globais do processo Python — o design é stateless por requisição.
- **Não mockar `database`** nos testes do backend — os testes usam SQLite real em diretório temporário. Isso é intencional para detectar divergências entre mock e banco real.
- **Não usar** `BEGIN` implícito em operações que exigem `BEGIN IMMEDIATE` — locks SQLite são críticos para a consistência do fluxo do agente.
- **Não chamar** endpoints da API a partir de `llm.py` — o módulo de LLM é isolado por design.
- **Não assumir** que o modelo Ollama (`qwen3:4b`) está disponível nos testes — os testes sempre substituem `llm.chat` via `monkeypatch`.
- **Não configurar** `CORS_ORIGINS` em testes automáticos.
- **Não usar** `--no-verify` em commits — os hooks devem ser respeitados.
- **Não editar** `doc-specs/tarefa.md` ou `doc-specs/tarefa.txt` — são a especificação original imutável.
- **Não armazenar** senhas de usuários em texto plano em nenhuma camada.

---

## Comandos Úteis

```powershell
# Iniciar o backend do agente
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

# Iniciar o frontend (desenvolvimento)
cd frontend
npm run dev

# Instalar dependências do frontend
cd frontend
npm install
```

---

## Variáveis de Ambiente do Backend (agente/)

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_PATH` | `imobiliaria.sqlite3` | Caminho do arquivo SQLite do agente |
| `OLLAMA_URL` | `http://localhost:11434` | URL do servidor Ollama |
| `OLLAMA_MODEL` | `qwen3:4b` | Modelo LLM a usar |
| `API_KEY` | _(vazio)_ | Chave de autenticação; sem valor, sem autenticação |
| `CORS_ORIGINS` | _(vazio)_ | Origens permitidas, separadas por vírgula |

---

## Endpoints da API do Agente

| Método | Caminho | Descrição |
|---|---|---|
| `POST` | `/api/whatsapp/mensagens` | Recebe mensagem do lead (fluxo integrado WhatsApp) |
| `POST` | `/api/conversas` | Cria uma nova conversa |
| `GET` | `/api/conversas/{cid}` | Retorna histórico e dados de uma conversa |
| `POST` | `/api/conversas/{cid}/mensagens` | Salva mensagem sem acionar o agente |
| `POST` | `/api/agente/responder` | Aciona o agente para gerar resposta a uma mensagem |

Todos os endpoints exigem `X-API-Key` se `API_KEY` estiver configurado.

---

## Modelo de Dados — Campos de Qualificação

| Campo | Tipo | Obrigatório | Valores aceitos |
|---|---|---|---|
| `estado` | `str` | Sim | nome ou UF |
| `bairro` | `str` | Sim | texto livre |
| `tipo_negocio` | `Literal` | Sim | `compra`, `aluguel` |
| `tipo_imovel` | `Literal` | Sim | `casa`, `apartamento`, `comercial` |
| `urgencia` | `Literal` | Sim | `Baixa`, `Média`, `Alta` |
| `nome_contato` | `str` | Sim (contato) | texto livre |
| `telefone_contato` | `str` | Sim (contato) | 10–15 dígitos com DDD |
| `metragem` | `float` | Não | > 0 |
| `banheiros` | `int` | Não | ≥ 0 |
| `quartos` | `int` | Não | ≥ 0 |
| `valor_maximo` | `float` | Não | > 0, em reais |
| `vagas` | `int` | Não | ≥ 0 |
