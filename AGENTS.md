# AGENTS.md — Guia de contexto para agentes de IA

Este arquivo descreve o projeto para que agentes (Claude Code, Copilot, etc.) possam trabalhar com contexto suficiente sem precisar redescobrir a estrutura a cada sessão.

---

## Resumo do projeto

POC de um agente SDR (Sales Development Representative) para imobiliárias, desenvolvida para o **Tech Challenge Fase 5 da POSTECH/FIAP**. A solução usa IA generativa local para atender leads via chat, qualificá-los e gerar um resumo estruturado para o corretor humano. O frontend expõe a interface de gestão (CRUD de Corretores, dashboard, histórico de leads).

**Tarefa ativa:** Tela de Login (`doc-specs/tarefa.md` + `doc-specs/PRD.md`) — implementar autenticação por e-mail e senha no frontend, criar o endpoint `POST /api/auth/login` na API de Corretores e proteger todas as rotas com `ProtectedRoute`.

---

## Stack tecnológica

### API de Corretores (`api/`)
| Componente | Versão/detalhe |
|------------|---------------|
| Runtime | Python 3.12+ |
| Framework | FastAPI ≥ 0.115 |
| Servidor ASGI | Uvicorn (porta **8001**) |
| Banco de dados | SQLite compartilhado em `database/imobiliaria.sqlite3` |
| Hash de senha | bcrypt (`bcrypt` lib) |
| Validação | Pydantic v2 |
| Testes | pytest + FastAPI TestClient |

### Agente SDR (`agente/`)
| Componente | Versão/detalhe |
|------------|---------------|
| Runtime | Python 3.12+ |
| Framework | FastAPI ≥ 0.115 |
| Servidor ASGI | Uvicorn (porta **8000**) |
| Banco de dados | SQLite compartilhado em `database/imobiliaria.sqlite3` |
| LLM | Ollama local, modelo padrão `qwen3:4b` (env `OLLAMA_MODEL`) |
| Validação | Pydantic v2 |
| HTTP client | httpx |
| Testes | pytest + FastAPI TestClient |

### Frontend (`frontend/`)
| Componente | Versão/detalhe |
|------------|---------------|
| Runtime | Node 20+ |
| Framework | React 19 |
| Build tool | Vite 8 |
| Roteamento | React Router v7 |
| UI | **shadcn/ui** + Tailwind CSS v3 + Radix UI primitives |
| Notificações | sonner (toast) |
| Ícones | lucide-react |
| Linter | oxlint |
| Linguagem | JavaScript (JSX) — sem TypeScript |
| Proxy dev | `/api` → `http://localhost:8001` (vite.config.js) |

### Infraestrutura
- Banco compartilhado: `database/imobiliaria.sqlite3` (fora de `agente/` e `api/`).
- Cada módulo inicializa seu próprio schema via `database.init_db()` — idempotente.
- CORS da `api/` habilitado para `http://localhost:5173` por padrão; configurável via `CORS_ORIGINS`.
- CORS do `agente/` desabilitado por padrão (habilitado apenas via `CORS_ORIGINS` env).

---

## Estrutura de pastas

```
projeto-hackaton-imobiliaria/
│
├── api/                            # API REST de Corretores (FastAPI, porta 8001)
│   ├── app.py                      # Entrypoint FastAPI, rotas CRUD + auth
│   ├── database.py                 # Conexão SQLite e init_db (tabela Corretores)
│   ├── services/
│   │   └── corretores.py           # Lógica de negócio: list, create, get, update, delete
│   └── tests/
│       └── test_corretores.py      # Suite pytest
│
├── agente/                         # Agente conversacional SDR (FastAPI, porta 8000)
│   ├── app.py                      # Entrypoint FastAPI, rotas de conversa e agente
│   ├── llm.py                      # Chamadas ao Ollama, prompts, modelos Pydantic
│   ├── database.py                 # Acesso SQLite, init_db, queries de conversa
│   ├── requirements.txt
│   ├── smoke_ollama.py             # Script de smoke test do LLM
│   ├── interface-teste/            # HTML estático de teste manual da API do agente
│   └── tests/
│       └── test_api.py             # Suite pytest de integração
│
├── frontend/                       # SPA React + Vite
│   ├── src/
│   │   ├── App.jsx                 # BrowserRouter, rotas principais
│   │   ├── main.jsx                # Ponto de entrada React
│   │   ├── pages/
│   │   │   └── CorretoresPage.jsx  # Página de CRUD de corretores
│   │   ├── components/
│   │   │   ├── ui/                 # Componentes shadcn/ui (button, input, dialog, table…)
│   │   │   ├── CorretorForm.jsx    # Formulário criar/editar corretor
│   │   │   ├── CorretorList.jsx    # Tabela de listagem de corretores
│   │   │   └── ConfirmDialog.jsx   # Diálogo de confirmação de exclusão
│   │   ├── services/
│   │   │   └── corretores.js       # Funções fetch para /api/corretores
│   │   └── lib/
│   │       └── utils.js            # cn() (clsx + tailwind-merge)
│   ├── vite.config.js              # Proxy /api → localhost:8001
│   ├── package.json
│   └── index.html
│
├── database/
│   └── imobiliaria.sqlite3         # Arquivo SQLite compartilhado (ignorado pelo git)
│
├── doc-specs/
│   ├── PRD.md                      # Product Requirements Document (feature atual)
│   ├── tarefa.md                   # História de usuário em andamento
│   └── tarefa.txt                  # Cópia da história (referência)
│
├── README.md
└── AGENTS.md                       # Este arquivo
```

---

## Padrões e convenções

### Geral
- Linguagem do projeto: **português** (variáveis, comentários, mensagens de UI, commits).
- Commits em português, mensagem imperativa no presente.
- Sem arquivos `.env` commitados; variáveis de ambiente documentadas no README.

### Backend (ambos os módulos)
- Responsabilidade única por arquivo: `app.py` (HTTP), `llm.py` (IA), `database.py` (persistência), `services/` (lógica de negócio).
- Erros de banco são encapsulados e mapeados para respostas HTTP; nunca vaze stack trace para o cliente.
- `database.py` nunca importa FastAPI. `services/` nunca importa `database.py` diretamente — recebe conexões abertas pelo `app.py`.
- Respostas do agente são **idempotentes** por `mensagem_id`.
- **Nunca** acessar `agente/database.py` de `llm.py`; o módulo LLM recebe dados como parâmetros.

### Frontend
- Componentes de UI de biblioteca ficam em `src/components/ui/` (padrão shadcn/ui).
- Componentes de domínio ficam em `src/components/`.
- Páginas ficam em `src/pages/`.
- Serviços HTTP (fetch) ficam em `src/services/`.
- Estado gerenciado localmente com `useState`/`useCallback`; sem Redux ou Zustand.
- Validação de formulário feita no próprio componente; sem `react-hook-form` por ora.
- Toda nova tela **deve** usar componentes shadcn/ui. MUI **não deve** ser adicionado.
- Aliases: `@/` mapeia para `src/` (configurado no `vite.config.js`).

### Banco de dados
- `database/imobiliaria.sqlite3` é o único banco do projeto; todos os módulos apontam para ele.
- Migrações via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` para preservar dados existentes.
- A tabela `Corretores` (módulo `api/`) armazena os usuários gestores com `senha_hash` bcrypt.
- A tabela `Usuarios` (módulo `agente/`) armazena leads (telefone + nome); sem senha.

---

## Endpoints da API — referência rápida

### API de Corretores (`api/`, porta 8001)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET    | `/api/corretores` | Lista todos os corretores |
| POST   | `/api/corretores` | Cria corretor (nome, email, telefone, senha) |
| GET    | `/api/corretores/:id` | Busca corretor por ID |
| PUT    | `/api/corretores/:id` | Atualiza corretor (campos opcionais) |
| DELETE | `/api/corretores/:id` | Remove corretor (204 No Content) |
| POST   | `/api/auth/login` | **A implementar** — autentica por e-mail + senha |

### Agente SDR (`agente/`, porta 8000)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST   | `/api/whatsapp/mensagens` | Recebe mensagem de lead (WhatsApp) |
| POST   | `/api/conversas` | Cria conversa para um telefone |
| GET    | `/api/conversas/:cid` | Retorna histórico da conversa |
| POST   | `/api/conversas/:cid/mensagens` | Adiciona mensagem a uma conversa |
| POST   | `/api/agente/responder` | Aciona o agente LLM para responder |

---

## Limitações dos agentes (do's e don'ts)

### Pode fazer ✅
- Ler qualquer arquivo do repositório para entender o contexto.
- Adicionar componentes shadcn/ui via `npx shadcn@latest add <componente>` dentro de `frontend/`.
- Criar novos arquivos em `src/components/`, `src/pages/`, `src/services/` seguindo a estrutura existente.
- Alterar `api/app.py`, `api/database.py` e `api/services/corretores.py` para adicionar endpoints, desde que os testes existentes continuem passando.
- Alterar `agente/app.py`, `agente/database.py` e `agente/llm.py` para adicionar endpoints ou corrigir bugs, desde que os testes existentes continuem passando.
- Rodar `pytest` dentro de `api/` ou `agente/` para validar alterações no backend.
- Rodar `npm run dev` ou `npm run build` dentro de `frontend/` para validar o frontend.
- Atualizar `AGENTS.md` e `doc-specs/PRD.md` quando o estado do projeto mudar significativamente.

### Não pode fazer ❌
- **Não alterar** as regras de validação dos formulários (Nome, Email, Telefone, Senha) sem atualizar o PRD e obter aprovação.
- **Não adicionar** novos modelos de IA, endpoints externos ou dependências pagas — o projeto deve rodar 100% local.
- **Não commitar** `database/imobiliaria.sqlite3` com dados reais — o `.gitignore` já o exclui, não reverter isso.
- **Não modificar** arquivos de teste (`test_*.py`) para fazer testes passarem — corrija o código de produção.
- **Não usar** `git push --force` nem `git reset --hard` sem confirmação explícita do usuário.
- **Não criar** arquivos de documentação extras (`.md`) além dos já definidos em `doc-specs/` e na raiz, a menos que o usuário solicite.
- **Não enviar** dados do banco ou credenciais para serviços externos.
- **Não adicionar** MUI (`@mui/material`) ou qualquer outra biblioteca de UI em novas telas — shadcn/ui é o padrão obrigatório.
- **Não misturar** responsabilidades entre `agente/` e `api/` — são módulos independentes que apenas compartilham o arquivo SQLite.

---

## Como executar localmente

### API de Corretores (porta 8001)
```powershell
cd api
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 8001 --reload
```

### Agente SDR (porta 8000)
```powershell
cd agente
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
ollama pull qwen3:4b
# Se o Ollama não estiver em execução: ollama serve (em outro terminal)
.\.venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
# Disponível em http://localhost:5173
# O Vite proxeia /api para http://localhost:8001 (API de Corretores)
```

### Testes
```powershell
# API de Corretores
cd api; .\.venv\Scripts\python -m pytest -q

# Agente SDR
cd agente; .\.venv\Scripts\python -m pytest -q
```
