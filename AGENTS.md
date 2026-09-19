# AGENTS.md — Guia de contexto para agentes de IA

Este arquivo descreve o projeto para que agentes (Claude Code, Copilot, etc.) possam trabalhar com contexto suficiente sem precisar redescobrir a estrutura a cada sessão.

---

## Resumo do projeto

POC de um agente SDR (Sales Development Representative) para imobiliárias, desenvolvida para o **Tech Challenge Fase 5 da POSTECH/FIAP**. A solução usa IA generativa local para atender leads via chat, qualificá-los e gerar um resumo estruturado para o corretor humano. O frontend expõe a interface de gestão (CRUD de usuários/corretores, dashboard, histórico de leads).

---

## Stack tecnológica

### Backend (`agente/`)
| Componente | Versão/detalhe |
|------------|---------------|
| Runtime | Python 3.12+ |
| Framework | FastAPI ≥ 0.115 |
| Servidor ASGI | Uvicorn ≥ 0.34 |
| Banco de dados | SQLite (arquivo compartilhado em `database/imobiliaria.sqlite3`) |
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
| UI (atual) | Material UI v6 + Emotion |
| UI (alvo) | shadcn/ui + Tailwind CSS |
| Linter | oxlint |
| Linguagem | JavaScript (JSX) — sem TypeScript |

### Infraestrutura
- Banco compartilhado: `database/imobiliaria.sqlite3` (fora de `agente/`).
- O agente inicializa o schema automaticamente via `database.init_db()`.
- CORS habilitado somente quando `CORS_ORIGINS` env está definida.
- Autenticação por `X-API-Key` header (opcional; habilitada se `API_KEY` env estiver definida).

---

## Estrutura de pastas

```
projeto-hackaton-imobiliaria/
├── agente/                     # Módulo backend (FastAPI + Ollama)
│   ├── app.py                  # Entrypoint FastAPI, rotas e handlers
│   ├── llm.py                  # Chamadas ao Ollama, prompts, modelos Pydantic
│   ├── database.py             # Acesso SQLite, init_db, queries
│   ├── requirements.txt
│   ├── smoke_ollama.py         # Script de smoke test do LLM
│   ├── interface-teste/        # HTML estático de teste manual da API
│   └── tests/
│       └── test_api.py         # Suite pytest de integração
│
├── frontend/                   # Módulo frontend (React + Vite)
│   ├── src/
│   │   ├── App.jsx             # BrowserRouter, rotas principais
│   │   ├── main.jsx            # Ponto de entrada React
│   │   ├── pages/
│   │   │   └── CorretoresPage.jsx   # Página de CRUD de corretores
│   │   ├── components/
│   │   │   ├── CorretorForm.jsx     # Formulário criar/editar
│   │   │   ├── CorretorList.jsx     # Tabela de listagem
│   │   │   └── ConfirmDialog.jsx    # Diálogo de confirmação de exclusão
│   │   └── services/
│   │       └── corretores.js        # Funções fetch para /api/corretores
│   ├── package.json
│   └── index.html
│
├── database/
│   └── imobiliaria.sqlite3     # Arquivo SQLite compartilhado
│
├── doc-specs/
│   ├── PRD.md                  # Product Requirements Document atual
│   └── tarefa.md               # História de usuário em andamento
│
├── README.md
└── AGENTS.md                   # Este arquivo
```

---

## Padrões e convenções

### Geral
- Linguagem do projeto: **português** (nomes de variáveis, comentários, mensagens de UI).
- Commits em português, mensagem imperativa no presente.
- Sem arquivos `.env` commitados; variáveis de ambiente documentadas no README.

### Backend
- Cada módulo tem responsabilidade única: `app.py` (HTTP), `llm.py` (IA), `database.py` (persistência).
- Erros de banco são encapsulados em `DatabaseError`; erros de LLM em `LLMError` — ambos mapeados para respostas HTTP em `app.py`.
- Respostas do agente são **idempotentes** por `mensagem_id`: a mesma chamada retorna o mesmo resultado sem acionar o LLM novamente.
- Bloqueio otimista por `LockToken` na tabela `Conversas` evita respostas duplicadas em concorrência.
- **Nunca** acessar `database.py` diretamente de `llm.py`; o módulo LLM recebe dados como parâmetros.

### Frontend
- Componentes de UI de biblioteca ficam em `src/components/ui/` (padrão shadcn/ui).
- Componentes de domínio ficam em `src/components/`.
- Páginas ficam em `src/pages/`.
- Serviços HTTP (fetch) ficam em `src/services/`.
- Estado gerenciado localmente com `useState`/`useCallback`; sem Redux ou Zustand até necessidade real.
- Validação de formulário feita no próprio componente (sem biblioteca externa como react-hook-form por ora).
- Toda nova tela **deve** usar componentes shadcn/ui — MUI não deve ser adicionado em novas implementações.

### Banco de dados
- O arquivo `database/imobiliaria.sqlite3` é o único banco do projeto. Todos os módulos devem apontar para ele.
- Migrações são feitas via `database.init_db()` com `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` para preservar dados existentes.
- A tabela `Usuarios` armazena tanto leads (vindos do WhatsApp) quanto corretores (criados pelo frontend).

---

## Limitações dos agentes (do's e don'ts)

### Pode fazer (do's)
- Ler qualquer arquivo do repositório para entender o contexto.
- Adicionar componentes shadcn/ui via `npx shadcn@latest add <componente>` dentro de `frontend/`.
- Criar novos arquivos em `src/components/`, `src/pages/`, `src/services/` seguindo a estrutura existente.
- Alterar `agente/app.py`, `agente/database.py` e `agente/llm.py` para adicionar endpoints ou corrigir bugs, desde que os testes existentes continuem passando.
- Rodar `pytest` dentro de `agente/` para validar alterações no backend.
- Rodar `npm run dev` ou `npm run build` dentro de `frontend/` para validar o frontend.
- Atualizar este `AGENTS.md` e `doc-specs/PRD.md` quando o estado do projeto mudar significativamente.

### Não pode fazer (don'ts)
- **Não remover o MUI** (`@mui/material` etc.) antes de confirmar que todos os componentes foram migrados e os testes manuais do CRUD estão aprovados.
- **Não alterar** as regras de validação do formulário de corretor (Nome, Email, Telefone, Senha) sem atualizar o PRD e obter aprovação.
- **Não adicionar** novos modelos de IA, endpoints externos ou dependências pesadas sem discutir com o time — o projeto deve rodar 100% local (sem APIs pagas).
- **Não commitar** o arquivo `database/imobiliaria.sqlite3` com dados reais; o `.gitignore` já o exclui — não reverter esse comportamento.
- **Não modificar** `agente/tests/test_api.py` para fazer testes passarem: corrija o código de produção.
- **Não usar** `git push --force` nem `git reset --hard` sem confirmação explícita do usuário.
- **Não criar** arquivos de documentação extras (`.md`) além dos já definidos em `doc-specs/` e na raiz, a menos que o usuário solicite.
- **Não enviar** dados do banco ou credenciais para serviços externos durante o desenvolvimento.

---

## Endpoints da API (referência rápida)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/whatsapp/mensagens` | Recebe mensagem de lead (WhatsApp) |
| POST | `/api/conversas` | Cria conversa para um telefone |
| GET | `/api/conversas/:cid` | Retorna histórico da conversa |
| POST | `/api/conversas/:cid/mensagens` | Adiciona mensagem a uma conversa |
| POST | `/api/agente/responder` | Aciona o agente LLM para responder |
| GET | `/api/corretores` | Lista corretores |
| POST | `/api/corretores` | Cria corretor |
| GET | `/api/corretores/:id` | Busca corretor por ID |
| PUT | `/api/corretores/:id` | Atualiza corretor |
| DELETE | `/api/corretores/:id` | Remove corretor |

---

## Como executar localmente

### Backend
```bash
cd agente
pip install -r requirements.txt
uvicorn app:app --reload
# Requer Ollama rodando em localhost:11434 com modelo qwen3:4b instalado
```

### Testes do backend
```bash
cd agente
pytest
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Disponível em http://localhost:5173
# O Vite proxeia /api para o backend FastAPI (porta 8000)
```
