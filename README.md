# Agente SDR Imobiliário com IA

Prova de conceito (POC) de um agente SDR para imobiliárias, desenvolvida para o **Tech Challenge – Fase 5** da POSTECH/FIAP.

O agente atende leads pelo WhatsApp em linguagem natural, identifica a intenção (compra, aluguel ou investimento), coleta os dados de qualificação, sugere imóveis do catálogo e entrega ao corretor um resumo estruturado. Os corretores acompanham os leads em um CRM web com funil (kanban), podem assumir a conversa manualmente e gerenciam o catálogo de imóveis.

## Problema

Leads imobiliários se perdem por demora na resposta, falta de acompanhamento, atendimento manual e dificuldade de identificar quais contatos têm maior potencial. A POC reduz esses gargalos com atendimento conversacional contínuo, follow-up automático e uma visão organizada do funil para o corretor.

## Funcionalidades

| Funcionalidade | Onde |
| --- | --- |
| Atendimento conversacional com LLM local (Ollama `qwen3:4b`) e saída estruturada validada por Pydantic | `agente/llm.py` |
| Qualificação progressiva: estado, bairro, compra/aluguel, tipo de imóvel, urgência + opcionais (metragem, quartos, banheiros, vagas, valor máximo) | `agente/app.py` |
| Perfil investidor: objetivo (renda/valorização), ticket e expectativa de retorno, com direcionamento a especialista | `agente/app.py` |
| Sugestão de até 3 imóveis disponíveis do catálogo, priorizando o bairro de interesse | `agente/catalogo.py` |
| Memória de conversa persistida no SQLite (últimas 40 mensagens + dados estruturados por conversa) | `agente/database.py` |
| Retomada após 24 h de inatividade ("continuar" ou "novo" atendimento) | `agente/database.py` |
| Follow-up automático de leads inativos (até 3 lembretes, depois cancela por inatividade) | `agente/followups.py`, `agente/reminder_store.py` |
| Integração real com WhatsApp via Baileys (recebe mensagens e envia respostas/lembretes) | `baileysWhatsappSendMessage/` |
| CRM web: login JWT, CRUD de corretores e imóveis, pipeline de leads em kanban | `frontend/`, `api/` |
| Corretor assume a conversa: envia mensagem manual pelo CRM, a IA é pausada e o status de entrega é registrado | `agente/app.py` (`/assumir`), `LeadConversationDialog.jsx` |

## Arquitetura

```text
Lead (WhatsApp)
   │
   ▼
baileysWhatsappSendMessage  (Node + Baileys, porta 3000)
   │  POST /api/whatsapp/mensagens                ▲ POST /enviar-mensagem
   ▼                                              │ (lembretes e mensagens manuais)
agente/  (FastAPI + Ollama, porta 8000) ──────────┘
   │         │
   │         └── Ollama qwen3:4b (porta 11434)
   ▼
database/imobiliaria.sqlite3  (SQLite WAL, compartilhado)
   ▲
api/  (FastAPI, porta 8001) — corretores, imóveis, leads, auth JWT
   ▲
frontend/  (React + Vite, porta 5173)
   proxy /api    → localhost:8001
   proxy /agente → localhost:8000/api
```

| Módulo | Stack | Porta | Responsabilidade |
| --- | --- | --- | --- |
| `agente/` | FastAPI, Ollama, SQLite | 8000 | Orquestra o diálogo, extrai preferências, sugere imóveis, follow-up e envio manual |
| `api/` | FastAPI, SQLite, bcrypt, PyJWT | 8001 | CRUD de corretores e imóveis, pipeline de leads, login |
| `frontend/` | React 19, Vite 8, shadcn/ui, Tailwind v3 | 5173 | CRM do corretor |
| `baileysWhatsappSendMessage/` | Node.js, Express 5, Baileys | 3000 | Ponte com o WhatsApp |
| `database/` | SQLite | — | Banco único compartilhado entre `agente/` e `api/` |
| `scripts/seed.py` | Python | — | Popula corretores, imóveis e leads de exemplo |

Os módulos Python não se importam mutuamente: a integração acontece pelo banco compartilhado e por HTTP.

### Tabelas principais

| Tabela | Dono | Conteúdo |
| --- | --- | --- |
| `Usuarios`, `Conversas`, `Mensagens` | `agente/` | Leads (PK = telefone), conversas e histórico |
| `Interessados`, `Investidores` | `agente/` | Perfil qualificado ao final da coleta |
| `Lembretes` | `agente/` | Controle de follow-up |
| `Corretores` | `api/` | Corretores e hash de senha |
| `Imoveis` | `api/` (lida pelo agente) | Catálogo |
| `AtribuicoesConversa` | `api/` | Etapa manual do funil e corretor responsável |

Etapas do funil: `novo`, `qualificando`, `qualificado`, `agendado`, `fechado`, `perdido`. Sem definição manual, a etapa é derivada do estado da conversa.

## Pré-requisitos

- Python 3.11+
- Node.js 20+
- [Ollama](https://ollama.com) com o modelo `qwen3:4b` (`ollama pull qwen3:4b`)
- Um número de WhatsApp para o bot (opcional; dá para testar pela interface de testes do agente)

## Como executar

Cada serviço roda em um terminal próprio. Os comandos abaixo usam PowerShell; o banco é criado automaticamente na primeira inicialização.

**1. API de corretores (porta 8001)**

```powershell
cd api
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app:app --port 8001 --reload
```

**2. Agente SDR (porta 8000)** — requer o Ollama em execução

```powershell
cd agente
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app:app --port 8000 --reload
```

Documentação interativa em http://127.0.0.1:8000/docs.

**3. Frontend (porta 5173)**

```powershell
cd frontend
npm install
npm run dev
```

**4. Bot do WhatsApp (porta 3000, opcional)**

```powershell
cd baileysWhatsappSendMessage
npm install
node bot.js
```

Escaneie o QR code exibido no terminal. A sessão fica em `auth_info/` (ignorada pelo git). Por segurança da POC, o bot só responde ao número definido em `NUMERO_TESTE` (`config/config.js`).

**5. Dados de exemplo (opcional)**

```powershell
api\.venv\Scripts\python scripts\seed.py
```

Cria corretores, imóveis e leads simulados de forma idempotente. As credenciais de login dos corretores de exemplo estão em `scripts/seed.py`.

### Testar o agente sem WhatsApp

A pasta `agente/interface-teste/` tem um simulador web de chat e um monitor de lembretes. Veja [agente/interface-teste/README.md](agente/interface-teste/README.md).

## Variáveis de ambiente

| Variável | Módulo | Padrão | Descrição |
| --- | --- | --- | --- |
| `DATABASE_PATH` | `api/`, `agente/` | `database/imobiliaria.sqlite3` | Caminho do SQLite (relativo à raiz do projeto) |
| `JWT_SECRET` | `api/` | `dev-secret-imobiliaria-2026` | Segredo do JWT |
| `CORS_ORIGINS` | `api/`, `agente/` | `http://localhost:5173` (api) / vazio (agente) | Origens permitidas, separadas por vírgula |
| `API_KEY` | `agente/` | vazio (sem auth) | Exige o header `X-API-Key` |
| `OLLAMA_URL` | `agente/` | `http://localhost:11434` | Endereço do Ollama |
| `OLLAMA_MODEL` | `agente/` | `qwen3:4b` | Modelo usado |
| `FOLLOWUP_IDLE_HOURS` | `agente/` | `24` | Inatividade antes do primeiro lembrete |
| `FOLLOWUP_INTERVAL_HOURS` | `agente/` | igual a `FOLLOWUP_IDLE_HOURS` | Intervalo entre lembretes |
| `FOLLOWUP_MAX_ATTEMPTS` | `agente/` | `3` | Lembretes antes de cancelar por inatividade |
| `AGENTE_API_KEY` | bot | vazio | Valor enviado em `X-API-Key` ao agente |

URLs do bot ficam em `agente/config.py` (`FOLLOWUP_URL`, `WHATSAPP_BOT_URL`) e em `baileysWhatsappSendMessage/config/config.js`.

> O frontend chama o agente sem `X-API-Key`. Para usar o envio manual pelo CRM, deixe `API_KEY` vazio no agente durante o desenvolvimento.

## Follow-up

O processamento de leads inativos é disparado por `POST /api/atendimentos/processar-inativos` (não há tarefa em segundo plano). Para rodar periodicamente, agende uma chamada a esse endpoint (por exemplo, a cada 15 minutos pelo Agendador de Tarefas do Windows). Detalhes em [agente/README.md](agente/README.md).

## Testes

```powershell
cd api;    .\.venv\Scripts\python -m pytest -q
cd agente; .\.venv\Scripts\python -m pytest -q
cd frontend; npm run lint
```

Os testes do agente substituem o LLM por dublês e usam SQLite temporário.

## Diferenciais implementados

- Integração real com WhatsApp (Baileys).
- Memória conversacional persistente em SQLite, sem estado em memória do processo.
- CRM com pipeline kanban e atribuição de corretor.
- Handoff humano: o corretor assume a conversa e a IA é pausada.
- Follow-up automático com idempotência e limite de tentativas.
- LLM local (Ollama), sem envio de dados de leads a provedores externos.

## Roadmap

1. Agendamento de visitas/reuniões integrado a calendário.
2. RAG sobre catálogo, políticas e informações imobiliárias.
3. Autenticação também nos endpoints da API de corretores e chave de API no frontend.
4. Agendador interno de follow-up e fila de processamento.
5. Observabilidade, banco servidor e deploy em cloud.

## Entregáveis do desafio

Repositório, README, arquitetura da solução, demonstração funcional, pitch técnico e explicação da IA utilizada.
