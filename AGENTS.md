# AGENTS.md — Guia de Contexto para Agentes

Leia este arquivo antes de qualquer tarefa neste repositório.  
Ele descreve o projeto, a stack, a estrutura de pastas, padrões obrigatórios e o que não fazer.

---

## 1. Resumo do Projeto

POC de **agente SDR imobiliário** para o Tech Challenge Fase 5 da POSTECH/FIAP.

O sistema atende leads automaticamente via conversação em linguagem natural, qualifica suas intenções (compra, aluguel, investimento), sugere imóveis de uma base simulada e gera resumos para o corretor assumir o atendimento. Corretores gerenciam sua conta via CRUD no frontend.

**Três módulos independentes:**

| Módulo | Descrição | Porta |
|--------|-----------|-------|
| `agente/` | Agente conversacional SDR — FastAPI + Ollama | 8000 |
| `api/` | CRUD de Corretores + Auth JWT — FastAPI | 8001 |
| `frontend/` | Interface web — React + Vite | 5173 |

Os módulos **não se importam mutuamente**. Compartilham apenas o banco SQLite em `database/imobiliaria.sqlite3`.

---

## 2. Stack Tecnológica

### Frontend (`frontend/`)

| Tecnologia | Versão | Papel |
|------------|--------|-------|
| React | 19 | UI |
| Vite | 8 | Build / dev server |
| React Router | v7 | Roteamento SPA |
| shadcn/ui | latest | Componentes de UI (obrigatório) |
| Tailwind CSS | v3 | Estilização utilitária |
| lucide-react | latest | Ícones |
| sonner | latest | Toasts/notificações |
| oxlint | latest | Linting |

- **Sem TypeScript** — arquivos `.jsx` e `.js`.
- **Sem Redux ou Zustand** — estado local com `useState`/`useCallback`.
- **Sem MUI, Ant Design ou outras bibliotecas de UI** além de shadcn/ui.

### API de Corretores (`api/`)

| Tecnologia | Papel |
|------------|-------|
| FastAPI | Framework HTTP |
| SQLite | Banco de dados (WAL mode) |
| Pydantic v2 | Validação e serialização |
| bcrypt | Hash de senha |
| PyJWT | Geração de JWT |

### Agente SDR (`agente/`)

| Tecnologia | Papel |
|------------|-------|
| FastAPI | Framework HTTP |
| SQLite | Banco de dados (compartilhado) |
| Pydantic v2 | Validação |
| Ollama (`qwen3:4b`) | LLM local para conversação |
| httpx | Chamadas HTTP para o Ollama |

---

## 3. Estrutura de Pastas

```
projeto-hackaton-imobiliaria/
├── agente/                     # Agente SDR (porta 8000)
│   ├── app.py                  # Endpoints FastAPI
│   ├── database.py             # Esquema e conexão SQLite
│   ├── llm.py                  # Integração Ollama
│   ├── smoke_ollama.py         # Script de sanidade do Ollama
│   ├── requirements.txt
│   ├── interface-teste/        # HTML estático para teste manual do agente
│   └── tests/
│       └── test_api.py
│
├── api/                        # API de Corretores (porta 8001)
│   ├── app.py                  # Endpoints FastAPI + Auth JWT
│   ├── database.py             # Esquema e conexão SQLite (tabela Corretores)
│   ├── services/
│   │   └── corretores.py       # Lógica de negócio (CRUD)
│   └── tests/
│       └── test_corretores.py
│
├── database/
│   └── imobiliaria.sqlite3     # Banco compartilhado entre api/ e agente/
│
├── frontend/                   # SPA React (porta 5173)
│   ├── index.html
│   ├── vite.config.js          # Proxy /api → localhost:8001
│   ├── src/
│   │   ├── main.jsx            # Ponto de entrada
│   │   ├── App.jsx             # Router raiz
│   │   ├── index.css           # CSS global + variáveis Tailwind/shadcn
│   │   ├── components/
│   │   │   ├── ui/             # Componentes shadcn/ui (Button, Input, etc.)
│   │   │   ├── AppLayout.jsx   # Shell: header + Outlet
│   │   │   ├── ProtectedRoute.jsx
│   │   │   ├── CorretorForm.jsx
│   │   │   ├── CorretorList.jsx
│   │   │   └── ConfirmDialog.jsx
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   └── CorretoresPage.jsx
│   │   └── services/
│   │       ├── auth.js         # login() / logout()
│   │       └── corretores.js   # listarCorretores, criarCorretor, etc.
│   └── node_modules/
│
├── doc-specs/
│   ├── PRD.md                  # Documento de requisitos da feature atual
│   └── tarefa.md               # História de usuário original
│
├── AGENTS.md                   # Este arquivo
└── README.md                   # Visão geral do projeto
```

---

## 4. Endpoints da API

### `api/` — CRUD de Corretores (porta 8001, prefixo `/api`)

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/api/corretores` | Lista todos os corretores |
| `POST` | `/api/corretores` | Cria novo corretor |
| `GET` | `/api/corretores/{id}` | Busca corretor por ID |
| `PUT` | `/api/corretores/{id}` | Atualiza corretor |
| `DELETE` | `/api/corretores/{id}` | Remove corretor |
| `POST` | `/api/auth/login` | Autentica corretor → retorna `{ token, corretor }` |

**Auth:** JWT em `localStorage` (`auth_token`). O frontend usa proxy Vite (`/api` → `http://localhost:8001`); a API não exige o token nos endpoints de corretores (autenticação é tratada no frontend via `ProtectedRoute`).

### `agente/` — Agente SDR (porta 8000, prefixo `/api`)

| Método | Path | Descrição |
|--------|------|-----------|
| `POST` | `/api/whatsapp/mensagens` | Recebe mensagem e retorna resposta do agente |
| `POST` | `/api/conversas` | Cria nova conversa |
| `GET` | `/api/conversas/{cid}` | Histórico de uma conversa |
| `POST` | `/api/conversas/{cid}/mensagens` | Salva mensagem manual |
| `POST` | `/api/agente/responder` | Gera resposta do agente para uma mensagem |

**Auth:** Header `X-API-Key` (variável de ambiente `API_KEY`; opcional em dev).

---

## 5. Padrões e Convenções

### Frontend

- **Componentes shadcn/ui** vão em `src/components/ui/`. Nunca editar os arquivos gerados pelo shadcn diretamente — regenerar se necessário.
- **Componentes de domínio** (layout, páginas, formulários) vão em `src/components/` ou `src/pages/`.
- **Serviços HTTP** vão em `src/services/` — um arquivo por recurso.
- **Estado:** `useState` + `useCallback` apenas. Sem Context API para dados globais simples (usar `localStorage` para auth).
- **Estilização:** classes Tailwind inline; evitar CSS Modules ou `styled-components`.
- **Toasts:** sempre via `sonner` (`toast.success`, `toast.error`).
- **Ícones:** sempre via `lucide-react`.
- **Arquivos:** `.jsx` para componentes React, `.js` para utilitários e serviços.

### API (`api/` e `agente/`)

- **Separação de camadas:** `app.py` só faz HTTP (validação Pydantic, roteamento, erros); `services/*.py` contém lógica de negócio; `database.py` gerencia esquema e conexão.
- **SQLite:** WAL mode, `PRAGMA foreign_keys=ON`, timeout 15 s.
- **Senhas:** bcrypt com `rounds=12`; nunca retornar `senha_hash` nas respostas.
- **JWT:** `PyJWT`; segredo via variável de ambiente `JWT_SECRET` (default: `dev-secret-imobiliaria-2026`).
- **CORS:** configurado via variável `CORS_ORIGINS`; default em `api/` é `http://localhost:5173`.

### Git

- Commits em português, imperativo, sem emoji.
- Mensagem de commit termina com `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` quando gerada por IA.

---

## 6. Variáveis de Ambiente

| Variável | Módulo | Default | Descrição |
|----------|--------|---------|-----------|
| `DATABASE_PATH` | `api/`, `agente/` | `database/imobiliaria.sqlite3` | Caminho absoluto ou relativo ao SQLite |
| `JWT_SECRET` | `api/` | `dev-secret-imobiliaria-2026` | Segredo para assinar JWT |
| `CORS_ORIGINS` | `api/`, `agente/` | `http://localhost:5173` | Origens permitidas pelo CORS |
| `API_KEY` | `agente/` | _(vazio = sem auth)_ | Chave de API para o agente |

---

## 7. Como Executar Localmente

```bash
# 1. Banco de dados — criado automaticamente ao iniciar qualquer serviço

# 2. API de Corretores
cd api
python -m uvicorn app:app --port 8001 --reload

# 3. Agente SDR (requer Ollama com modelo qwen3:4b)
cd agente
python -m uvicorn app:app --port 8000 --reload

# 4. Frontend
cd frontend
npm install
npm run dev
```

---

## 8. Limitações dos Agentes (Do's e Don'ts)

### DO — Pode e deve fazer

- Editar arquivos em `frontend/src/` para adicionar componentes, páginas e serviços.
- Criar novos componentes dentro de `src/components/` ou `src/pages/`.
- Usar componentes shadcn/ui existentes em `src/components/ui/`.
- Editar `api/app.py` e `api/services/corretores.py` para novos endpoints.
- Usar `lucide-react` para ícones e `sonner` para toasts.
- Usar Tailwind CSS para estilos inline nos componentes.
- Ler `doc-specs/PRD.md` para entender o escopo da feature em desenvolvimento.
- Rodar `npm run lint` no frontend antes de reportar conclusão.

### DON'T — Não fazer

- **Não instalar bibliotecas de UI além de shadcn/ui** (sem MUI, Ant Design, Chakra, etc.).
- **Não usar TypeScript** — o projeto é JavaScript puro (`.jsx`/`.js`).
- **Não adicionar Redux, Zustand ou Context API** para estado que cabe em `useState`.
- **Não editar arquivos em `frontend/node_modules/`**.
- **Não modificar o banco SQLite diretamente** — usar as funções em `database.py`.
- **Não criar endpoints novos em `agente/app.py`** sem confirmar com o usuário — o agente usa chave de API e tem escopo definido.
- **Não mover o arquivo `database/imobiliaria.sqlite3`** — o caminho é compartilhado entre `api/` e `agente/`.
- **Não retornar `senha_hash`** em nenhuma resposta de API.
- **Não usar `--no-verify`** em commits nem ignorar falhas de lint.
- **Não criar arquivos de comentário, planejamento ou rascunho no repositório** — usar apenas o contexto da conversa para planejamento.
- **Não assumir que rotas protegidas funcionam sem `ProtectedRoute`** — toda rota que exige login deve ser filha do componente `ProtectedRoute`.
- **Não adicionar CSS Modules ou `styled-components`** — usar apenas classes Tailwind.
