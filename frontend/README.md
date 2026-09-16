# Frontend — Agente SDR Imobiliário

Interface React/Vite standalone para o agente SDR imobiliário.

## Instalação

```bash
npm install
```

## Desenvolvimento

```bash
npm run dev
```

Abre em http://localhost:5173

## Configuração

Copie `.env.example` para `.env` e ajuste `VITE_API_URL` se necessário:

```bash
cp .env.example .env
```

| Variável | Padrão | Descrição |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | URL base da API do agente |

## Rotas

| Rota | Descrição |
|---|---|
| `/` | Página principal (Hello World) |
| `/dashboard` | Dashboard do corretor |
