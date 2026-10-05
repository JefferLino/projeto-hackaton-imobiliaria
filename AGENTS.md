# AGENTS.md — Guia de Contexto para Agentes

Leia este arquivo antes de qualquer tarefa neste repositório.  
Ele descreve o projeto, a stack, a estrutura de pastas, padrões obrigatórios e o que não fazer.

---

## 1. Resumo do Projeto

POC de **agente SDR imobiliário** para o Tech Challenge Fase 5 da POSTECH/FIAP.

O agente atende leads pelo WhatsApp em linguagem natural, qualifica a intenção (compra, aluguel, investimento), sugere imóveis do catálogo e gera resumo estruturado para o corretor. Corretores usam um CRM web (login JWT) para gerenciar corretores e imóveis, acompanhar o funil de leads em kanban e assumir conversas manualmente.

**Módulos:**

| Módulo | Descrição | Porta |
|--------|-----------|-------|
| `agente/` | Agente conversacional SDR — FastAPI + Ollama | 8000 |
| `api/` | Corretores, Imóveis, Leads (pipeline) + Auth JWT — FastAPI | 8001 |
| `frontend/` | CRM web — React + Vite | 5173 |
| `baileysWhatsappSendMessage/` | Bot WhatsApp — Node + Express + Baileys | 3000 |
| `scripts/seed.py` | Seed de dados de dev (corretores, imóveis, leads) | — |

`agente/` e `api/` **não se importam mutuamente**. Compartilham apenas o banco SQLite em `database/imobiliaria.sqlite3`. O bot e o agente se comunicam por HTTP. `scripts/seed.py` carrega os módulos dos dois via `importlib` (ferramenta de dev, não é dependência de nenhum deles).

### Fluxo principal

1. Bot recebe mensagem no WhatsApp → `POST agente /api/whatsapp/mensagens` (`{telefone, texto}`).
2. Agente resolve a conversa ativa pelo telefone, salva a mensagem, extrai preferências via LLM e responde.
3. Coleta: obrigatórios (`estado`, `bairro`, `tipo_negocio`, `tipo_imovel`, `urgencia`) → opcionais oferecidos uma vez (`metragem`, `banheiros`, `quartos`, `valor_maximo`, `vagas`) → contato (`nome_contato`, `telefone_contato`). Investidor: `objetivo_investimento`, `ticket_investimento`, `expectativa_retorno`.
4. Ao completar, grava em `Interessados` ou `Investidores`, anexa até 3 imóveis de `catalogo.sugerir()` e fica em `AguardandoConfirmacao` até o cliente pedir encerramento.
5. Corretor vê o lead no kanban (`/dashboard`), abre a conversa e pode enviar mensagem manual (`/assumir`) → `ModoManual=1`, IA pausada para essa conversa, mensagem enviada ao bot (`/enviar-mensagem`) e `StatusEnvio` registrado.
6. Follow-up: `POST /api/atendimentos/processar-inativos` envia lembretes a conversas inativas e cancela após o máximo de tentativas. Mensagens com mais de 24 h disparam a pergunta "continuar" ou "novo".

---

## 2. Stack Tecnológica

### Frontend (`frontend/`)

| Tecnologia | Versão | Papel |
|------------|--------|-------|
| React | 19 | UI |
| Vite | 8 | Build / dev server |
| React Router | v7 | Roteamento SPA |
| shadcn/ui (Radix) | latest | Componentes de UI (obrigatório) |
| Tailwind CSS | v3 | Estilização utilitária |
| lucide-react | latest | Ícones |
| sonner | latest | Toasts/notificações |
| oxlint | latest | Linting |

- **Sem TypeScript** — arquivos `.jsx` e `.js`.
- **Sem Redux ou Zustand** — estado local com `useState`/`useCallback`.
- **Sem MUI, Ant Design ou outras bibliotecas de UI** além de shadcn/ui.
- Alias `@` → `src/`.

### API (`api/`)

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
| Pydantic v2 | Validação e saída estruturada do LLM |
| `ollama` (lib oficial) + `qwen3:4b` | LLM local |
| httpx | Envio ao bot WhatsApp / lembretes; erros de transporte |

### Bot WhatsApp (`baileysWhatsappSendMessage/`)

| Tecnologia | Papel |
|------------|-------|
| Node.js (ESM) | Runtime |
| Express 5 | API `POST /enviar-mensagem`, `GET /status` |
| @whiskeysockets/baileys | Conexão com o WhatsApp (QR code, sessão em `auth_info/`) |

---

## 3. Estrutura de Pastas

```
projeto-hackaton-imobiliaria/
├── agente/                     # Agente SDR (porta 8000)
│   ├── app.py                  # Endpoints FastAPI e fluxo de qualificação
│   ├── database.py             # Esquema, migrações e transações por conversa
│   ├── llm.py                  # Ollama: prompts, extração e geração de resposta
│   ├── catalogo.py             # Sugestão de imóveis (lê a tabela Imoveis)
│   ├── followups.py            # Orquestra lembretes de inatividade
│   ├── reminder_store.py       # SQL e reservas da tabela Lembretes
│   ├── whatsapp_bot.py         # Cliente HTTP do bot (envio manual)
│   ├── config.py               # FOLLOWUP_URL, WHATSAPP_BOT_URL
│   ├── smoke_ollama.py         # Script de sanidade do Ollama
│   ├── requirements.txt
│   ├── README.md               # Contrato detalhado do agente
│   ├── interface-teste/        # Simulador de chat + monitor de lembretes (porta 5500)
│   └── tests/
│       ├── test_api.py
│       └── test_reminders.py
│
├── api/                        # API do CRM (porta 8001)
│   ├── app.py                  # Endpoints FastAPI + Auth JWT + modelos Pydantic
│   ├── database.py             # Tabelas Corretores, AtribuicoesConversa, Imoveis
│   ├── services/
│   │   ├── corretores.py       # CRUD de corretores
│   │   ├── imoveis.py          # CRUD de imóveis
│   │   └── leads.py            # Pipeline: lê Conversas/Usuarios, grava AtribuicoesConversa
│   └── tests/
│       ├── test_corretores.py
│       ├── test_imoveis.py
│       └── test_leads.py
│
├── baileysWhatsappSendMessage/ # Bot WhatsApp (porta 3000)
│   ├── bot.js                  # Express + inicialização do WhatsApp
│   ├── config/config.js        # Porta, NUMERO_TESTE, URL do agente, API key
│   ├── api/responseApi.js      # Chama o agente
│   ├── whatsapp/               # connection.js, messages.js
│   └── utils/phone.js
│
├── database/
│   └── imobiliaria.sqlite3     # Banco compartilhado (ignorado pelo git)
│
├── frontend/                   # CRM React (porta 5173)
│   ├── vite.config.js          # Proxy /api → :8001, /agente → :8000/api
│   └── src/
│       ├── main.jsx
│       ├── App.jsx             # Rotas: /login, /corretores, /imoveis, /dashboard
│       ├── index.css           # CSS global + variáveis Tailwind/shadcn
│       ├── components/
│       │   ├── ui/             # shadcn/ui: button, dialog, input, label, separator, table, tooltip
│       │   ├── AppLayout.jsx   # Shell: header + Sidebar + Outlet
│       │   ├── Sidebar.jsx
│       │   ├── ProtectedRoute.jsx
│       │   ├── ErrorBoundary.jsx
│       │   ├── ConfirmDialog.jsx
│       │   ├── CorretorForm.jsx / CorretorList.jsx
│       │   ├── ImovelForm.jsx / ImovelList.jsx
│       │   ├── LeadCard.jsx
│       │   └── LeadConversationDialog.jsx  # Histórico + envio manual
│       ├── pages/
│       │   ├── LoginPage.jsx
│       │   ├── CorretoresPage.jsx
│       │   ├── ImoveisPage.jsx
│       │   ├── PipelinePage.jsx  # Kanban de leads (/dashboard)
│       │   └── etapas.js
│       ├── lib/                # utils.js (cn), imovelOpcoes.js, leadFormat.js
│       └── services/           # auth, corretores, imoveis, leads, conversas
│
├── scripts/
│   └── seed.py                 # Seed idempotente de dados de dev
│
├── doc-specs/                  # PRD/specs locais (ignorados pelo git)
├── AGENTS.md                   # Este arquivo
└── README.md                   # Visão geral do projeto
```

---

## 4. Endpoints

### `api/` — CRM (porta 8001)

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/api/corretores` | Lista corretores |
| `POST` | `/api/corretores` | Cria corretor |
| `GET` | `/api/corretores/{id}` | Busca corretor |
| `PUT` | `/api/corretores/{id}` | Atualiza corretor |
| `DELETE` | `/api/corretores/{id}` | Remove corretor |
| `POST` | `/api/auth/login` | Autentica → `{ token, corretor }` |
| `GET` | `/api/leads?etapa=&corretor_id=` | Lista leads (conversas do agente) com etapa e corretor |
| `PATCH` | `/api/leads/{conversa_id}` | Altera `etapa` e/ou `corretor_id` |
| `GET` | `/api/imoveis` | Lista imóveis |
| `POST` | `/api/imoveis` | Cria imóvel |
| `GET` | `/api/imoveis/{id}` | Busca imóvel |
| `PUT` | `/api/imoveis/{id}` | Atualiza imóvel |
| `DELETE` | `/api/imoveis/{id}` | Remove imóvel |

**Auth:** JWT em `localStorage` (`auth_token`, `auth_user`). A API **não** valida o token nos endpoints; a proteção é feita no frontend via `ProtectedRoute`.

### `agente/` — Agente SDR (porta 8000)

| Método | Path | Descrição |
|--------|------|-----------|
| `POST` | `/api/whatsapp/mensagens` | Entrada do WhatsApp: resolve conversa por telefone e responde |
| `POST` | `/api/agente/responder` | Gera (ou repete) a resposta para `conversa_id` + `mensagem_id` |
| `GET` | `/api/conversas/{cid}?telefone=` | Histórico da conversa |
| `POST` | `/api/conversas/{cid}/assumir` | Corretor envia mensagem manual; ativa `ModoManual` e envia via bot |
| `POST` | `/api/conversas` | Cria conversa (legado) |
| `POST` | `/api/conversas/{cid}/mensagens` | Salva mensagem do cliente (legado) |
| `POST` | `/api/atendimentos/processar-inativos` | Processa follow-up de conversas inativas |

**Auth:** header `X-API-Key` quando `API_KEY` está definida. O frontend acessa o agente via proxy `/agente/*` e **não envia** `X-API-Key`.

### Bot (porta 3000)

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/status` | `{ sucesso, whatsapp_conectado }` |
| `POST` | `/enviar-mensagem` | `{ telefone, mensagem }` → `{ sucesso, id }` |

---

## 5. Banco de Dados

| Tabela | Criada por | Observação |
|--------|-----------|------------|
| `Usuarios`, `Conversas`, `Mensagens` | `agente/database.py` | Colunas em PascalCase; migrações via `ALTER TABLE` em `init_db()` |
| `Interessados`, `Investidores` | `agente/database.py` | Upsert por telefone ao concluir a qualificação |
| `Lembretes` | `agente/reminder_store.py` | Follow-up |
| `Corretores`, `Imoveis`, `AtribuicoesConversa` | `api/database.py` | Colunas em snake_case (exceto `AtribuicoesConversa`) |

- `api/` só faz `SELECT` em `Conversas`/`Usuarios`; nunca escreve nas tabelas do agente.
- `agente/` só lê `Imoveis` (em `catalogo.py`).
- Etapas do funil: `novo`, `qualificando`, `qualificado`, `agendado`, `fechado`, `perdido`. Sem override em `AtribuicoesConversa`, `leads._etapa_sugerida()` deriva a etapa do estado da conversa.

---

## 6. Padrões e Convenções

### Frontend

- **Componentes shadcn/ui** vão em `src/components/ui/`. Nunca editar os arquivos gerados diretamente — regenerar se necessário.
- **Componentes de domínio** vão em `src/components/`; páginas em `src/pages/`; helpers em `src/lib/`.
- **Serviços HTTP** vão em `src/services/` — um arquivo por recurso, usando URLs relativas (`/api/...` para o CRM, `/agente/...` para o agente).
- **Estado:** `useState` + `useCallback` apenas. Sem Context API para dados globais simples (usar `localStorage` para auth).
- **Estilização:** classes Tailwind inline; evitar CSS Modules ou `styled-components`.
- **Toasts:** sempre via `sonner` (`toast.success`, `toast.error`).
- **Ícones:** sempre via `lucide-react`.
- **Arquivos:** `.jsx` para componentes React, `.js` para utilitários e serviços.
- Novas páginas autenticadas: adicionar a rota dentro de `<ProtectedRoute>` → `<AppLayout>` em `App.jsx` e o item em `Sidebar.jsx`.

### API (`api/`)

- **Separação de camadas:** `app.py` só faz HTTP (Pydantic, roteamento, erros); `services/*.py` contém lógica de negócio e recebe a conexão aberta; `database.py` gerencia esquema e conexão.
- **SQLite:** WAL mode, `PRAGMA foreign_keys=ON`, timeout 15 s.
- **Senhas:** bcrypt com `rounds=12`; nunca retornar `senha_hash`.
- **JWT:** `PyJWT` HS256; segredo via `JWT_SECRET`.
- **CORS:** `CORS_ORIGINS`; default `http://localhost:5173`.

### Agente (`agente/`)

- `app.py`: endpoints e fluxo; `database.py`: SQL e transações; `llm.py`: tudo que toca o Ollama (não acessa banco); `catalogo.py`, `followups.py`, `reminder_store.py`, `whatsapp_bot.py` com responsabilidade única.
- Transações curtas: `begin_response()` reserva o turno (lock com expiração de 300 s), a IA roda fora da transação, `finish_response()` grava tudo atomicamente e `release_response()` libera em `finally`.
- Sem estado de sessão em memória: o contexto é sempre recuperado do SQLite.
- Erros de banco → `DatabaseError(status_code, detail)`; erros do LLM → `LLMError` (HTTP 503).
- Respostas de etapas críticas (conclusão, encerramento) são texto fixo, não geradas pelo LLM.
- `CORS_ORIGINS` vazio por padrão.

### Git

- Commits em português, imperativo, sem emoji.
- Mensagem de commit termina com `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` quando gerada por IA.

---

## 7. Variáveis de Ambiente

| Variável | Módulo | Default | Descrição |
|----------|--------|---------|-----------|
| `DATABASE_PATH` | `api/`, `agente/` | `database/imobiliaria.sqlite3` | Caminho do SQLite (relativo à raiz do projeto) |
| `JWT_SECRET` | `api/` | `dev-secret-imobiliaria-2026` | Segredo do JWT |
| `CORS_ORIGINS` | `api/`, `agente/` | `http://localhost:5173` (api) / vazio (agente) | Origens permitidas |
| `API_KEY` | `agente/` | _(vazio = sem auth)_ | Chave exigida em `X-API-Key` |
| `OLLAMA_URL` | `agente/` | `http://localhost:11434` | Servidor Ollama |
| `OLLAMA_MODEL` | `agente/` | `qwen3:4b` | Modelo |
| `FOLLOWUP_IDLE_HOURS` | `agente/` | `24` | Inatividade antes do 1º lembrete |
| `FOLLOWUP_INTERVAL_HOURS` | `agente/` | = `FOLLOWUP_IDLE_HOURS` | Intervalo entre lembretes |
| `FOLLOWUP_MAX_ATTEMPTS` | `agente/` | `3` | Máximo de lembretes |
| `AGENTE_API_KEY` | bot | _(vazio)_ | Enviada como `X-API-Key` ao agente |

Constantes em arquivo (não são env vars): `agente/config.py` (`FOLLOWUP_URL`, `WHATSAPP_BOT_URL`) e `baileysWhatsappSendMessage/config/config.js` (`PORTA_API`, `NUMERO_TESTE`, `URL_API_RESPOSTA`).

---

## 8. Como Executar Localmente

```powershell
# API (8001)
cd api; .\.venv\Scripts\python -m uvicorn app:app --port 8001 --reload

# Agente (8000) — requer Ollama com qwen3:4b
cd agente; .\.venv\Scripts\python -m uvicorn app:app --port 8000 --reload

# Frontend (5173) — também disponível via .claude/launch.json ("frontend")
cd frontend; npm install; npm run dev

# Bot WhatsApp (3000) — opcional, pede QR code
cd baileysWhatsappSendMessage; npm install; node bot.js

# Seed (opcional)
api\.venv\Scripts\python scripts\seed.py
```

Testes:

```powershell
cd api; .\.venv\Scripts\python -m pytest -q
cd agente; .\.venv\Scripts\python -m pytest -q
cd frontend; npm run lint
```

---

## 9. Limitações dos Agentes (Do's e Don'ts)

### DO — Pode e deve fazer

- Editar arquivos em `frontend/src/` para adicionar componentes, páginas e serviços.
- Usar componentes shadcn/ui existentes em `src/components/ui/`.
- Editar `api/app.py` e `api/services/*.py` para novos endpoints do CRM.
- Usar `lucide-react` para ícones e `sonner` para toasts.
- Usar Tailwind CSS para estilos inline nos componentes.
- Ler `doc-specs/PRD.md` (quando existir localmente) para entender o escopo da feature em desenvolvimento.
- Rodar `npm run lint` no frontend e `pytest` no módulo Python alterado antes de reportar conclusão.
- Atualizar este arquivo e o `README.md` quando endpoints, tabelas ou módulos mudarem.

### DON'T — Não fazer

- **Não instalar bibliotecas de UI além de shadcn/ui** (sem MUI, Ant Design, Chakra, etc.).
- **Não usar TypeScript** — o projeto é JavaScript puro (`.jsx`/`.js`).
- **Não adicionar Redux, Zustand ou Context API** para estado que cabe em `useState`.
- **Não editar arquivos em `frontend/node_modules/`**.
- **Não modificar o banco SQLite diretamente** — usar as funções em `database.py`/`services`.
- **Não fazer `agente/` importar `api/` (ou vice-versa)** — integrar pelo banco ou por HTTP.
- **Não escrever nas tabelas do agente a partir de `api/`** — usar `AtribuicoesConversa` para dados do CRM sobre leads.
- **Não criar endpoints novos em `agente/app.py`** sem confirmar com o usuário — o agente usa chave de API e tem escopo definido.
- **Não mover o arquivo `database/imobiliaria.sqlite3`** — o caminho é compartilhado entre `api/` e `agente/`.
- **Não retornar `senha_hash`** em nenhuma resposta de API.
- **Não commitar `baileysWhatsappSendMessage/auth_info/`** nem arquivos `.env` — contêm credenciais.
- **Não usar `--no-verify`** em commits nem ignorar falhas de lint.
- **Não criar arquivos de comentário, planejamento ou rascunho no repositório** — usar apenas o contexto da conversa para planejamento.
- **Não assumir que rotas protegidas funcionam sem `ProtectedRoute`** — toda rota que exige login deve ser filha do componente `ProtectedRoute`.
- **Não adicionar CSS Modules ou `styled-components`** — usar apenas classes Tailwind.
