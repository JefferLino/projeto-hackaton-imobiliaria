# Agente imobiliário

API FastAPI com IA local via Ollama, histórico SQLite e simulador web de WhatsApp. Python 3.11 ou superior.

A comunicação com o modelo usa a biblioteca oficial Python `ollama`, com `Client.chat`, timeout de 120 segundos e saída estruturada validada com Pydantic. O servidor Ollama continua necessário. O cliente é fechado após cada chamada e o histórico é sempre recuperado do SQLite. `httpx` permanece como dependência para os testes e para tratar erros de transporte propagados pela biblioteca.

## Executar no PowerShell

As operações de SQLite ficam em `database.py`: conexão, criação e migração das tabelas, usuários, conversas, mensagens, interessados e bloqueios por conversa. `llm.py` concentra a configuração do Ollama, os prompts, as chamadas ao modelo e os esquemas de validação das respostas. `app.py` contém os endpoints, validação das requisições e fluxo do agente. Inclua os três arquivos na entrega da API.

A API chama `llm.extract_preferences(current, messages)` para extrair os dados e `llm.generate_reply(current, instruction, messages)` para formular as perguntas. O módulo não acessa o banco, não depende de FastAPI e não guarda conversas em memória entre chamadas. As configurações `OLLAMA_MODEL` e `OLLAMA_URL` continuam iguais. Erros do modelo são lançados como `LLMError`, que a API traduz para HTTP 503.

O caminho do banco continua configurado por `DATABASE_PATH`, com padrão `database/imobiliaria.sqlite3` na raiz do projeto principal. A separação não exige recriar o banco. A inicialização chama `database.init_db()` automaticamente. O processamento usa `begin_response()`, `finish_response()` e `release_response()` para manter as transações curtas, executar a IA fora delas e liberar o bloqueio mesmo em caso de erro.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
ollama pull qwen3:4b
# Se o Ollama não estiver em execução, execute ollama serve em outro terminal.
.\.venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000/docs para o contrato interativo da API. O banco é criado automaticamente na inicialização. A API não serve a interface de testes.

## Interface de testes separada

A pasta `interface-teste/` contém o cliente web opcional e deve ficar fora da entrega da API. O backend permanece em `app.py`, na raiz, e funciona sem essa pasta.

Para testar sem WhatsApp, inicie a API com a origem da interface autorizada:

```powershell
.\interface-teste\iniciar-api.ps1
```

Se a API já estiver em execução, pare-a com Ctrl+C antes de executar esse script. Em outro terminal na raiz do projeto:

```powershell
.\.venv\Scripts\python -m uvicorn receiver:app --app-dir interface-teste --host 127.0.0.1 --port 5500
```

Abra http://127.0.0.1:5500. O endereço da API está em `interface-teste/config.js`. Consulte [as instruções da interface](interface-teste/README.md) para configurar outras portas ou endereços. As mensagens continuam sendo salvas no SQLite pelos endpoints da API.

`CORS_ORIGINS` aceita origens separadas por vírgula e fica desabilitado por padrão. Não é necessário configurá-lo para a integração servidor a servidor do WhatsApp.

## Configuração da API

Configuração opcional via variáveis de ambiente:

```powershell
$env:DATABASE_PATH = 'database/imobiliaria.sqlite3'
$env:OLLAMA_URL = 'http://localhost:11434'
$env:OLLAMA_MODEL = 'qwen3:4b'
$env:API_KEY = 'defina-uma-chave-secreta'
```

Sem API_KEY, o sistema funciona sem autenticação para testes locais. Para disponibilizar a integração, configure a chave e envie o cabeçalho `X-API-Key`, inclusive na interface. O telefone é validado contra a conversa, mas não autentica um usuário: essa responsabilidade pertence à integração confiável do WhatsApp. Use sempre o mesmo formato de telefone (recomendado: código do país + DDD + número, só dígitos).

## Contrato com o WhatsApp

O WhatsApp envia uma única chamada a `POST /api/whatsapp/mensagens`:

```json
{
  "telefone": "5511999999999",
  "texto": "Estou procurando apartamento na zona sul"
}
```

Telefone e texto são obrigatórios. A API cadastra o telefone desconhecido, encontra a conversa ativa mais recente (ou cria uma se não houver), salva a mensagem, recupera o contexto e salva a resposta. Retorna `resposta`, `status`, `conversa_id`, `mensagem_id`, `dados` e indicadores da etapa. O WhatsApp só entrega a resposta ao cliente; não grava diretamente no banco nem envia IDs internos na chamada inicial.

Se a última mensagem da conversa ativa tiver mais de 24 horas (horários UTC), a API apresenta um resumo das preferências persistidas e pergunta se deseja continuar ou iniciar novo atendimento. Sem preferências extraídas, mostra a última solicitação. A decisão fica em `Conversas.AguardandoRetomada`; respostas ambíguas repetem a pergunta. O usuário pode escrever “continuar” ou “novo”, ou a integração pode enviar o campo opcional `opcao_atendimento` com um desses valores após apresentar a escolha. Outras expressões são classificadas pela IA. Se essa classificação falhar, a API salva a mensagem e repete a escolha.

Ao continuar, mantém o contexto. Ao iniciar outro, encerra a conversa anterior, preserva seu histórico e abre uma conversa sem as preferências antigas. Nome e telefone de contato devem ser informados para o novo atendimento. Em bancos legados com várias conversas ativas, seleciona a de maior ID.

Não há identificador externo nem deduplicação de envios: cada chamada aceita cria uma nova mensagem, mesmo com texto idêntico. HTTP 409 indica mensagem anterior pendente ou processamento em andamento. Se a IA falhar depois da gravação, o HTTP 503 retorna `conversa_id` e `mensagem_id`: use esses IDs junto ao telefone em `POST /api/agente/responder` para tentar apenas a resposta novamente. A interface de testes faz isso pelo botão “Tentar novamente”. Se houver falha de rede sem resposta, consulte o histórico antes de reenviar, pois a mensagem pode ter sido salva.

`GET /api/conversas/{id}?telefone=...` permanece disponível para consultar histórico. Os endpoints antigos de criação, gravação e resposta por IDs permanecem por compatibilidade, mas não devem ser usados pela nova integração: o fluxo de retomada por telefone e 24 horas é aplicado no endpoint `/api/whatsapp/mensagens`.

## Coleta e contexto

Obrigatórios: estado, bairro, compra/aluguel, casa/apartamento/comercial e urgência Baixa/Média/Alta. Ao final da coleta, antes de encaminhar ao consultor, são exigidos `nome_contato` e `telefone_contato`. Eles são gravados em `Usuarios.Nome` e `Usuarios.TelefoneContato`. O telefone identificador continua sendo `Usuarios.Telefone` (PK), não é substituído nem copiado automaticamente para o contato. O telefone de contato deve ter DDD e 10 a 15 dígitos. Opcionais: metragem, banheiros, quartos, valor máximo e vagas. Zero é permitido para quantidades.

A cada chamada o agente recupera os últimos 40 registros até a mensagem atual e os dados estruturados persistidos da conversa. É recuperação de contexto por ConversaID (não busca vetorial); nenhuma sessão de usuário fica armazenada na memória do processo. Todo o histórico permanece no SQLite. Detalhes antigos que não sejam preferências podem sair da janela de contexto.

O agente pergunta um ou dois campos obrigatórios por vez. Depois, oferece os opcionais uma vez; o cliente pode responder apenas alguns ou pular. Por último, pede os dados de contato que ainda faltarem. Só então salva o interessado e mantém a conversa ativa com a mensagem: “Suas preferências foram salvas. Um consultor irá entrar em contato. Deseja encerrar a conversa ou alterar algo?”. `Resumo` contém as preferências estruturadas. As colunas necessárias são criadas automaticamente ao reiniciar a API, preservando os dados existentes. Estruturas antigas de chave externa, se presentes em bancos existentes, são preservadas mas não são mais utilizadas nem criadas em bancos novos.

Enquanto `aguardando_confirmacao` for true, o cliente pode alterar os dados e o cadastro do interessado será atualizado. Só uma confirmação explícita de encerramento, após essa pergunta, muda o status para `encerrada`; “sim” isolado não é suficiente. Essa etapa fica persistida em `Conversas.AguardandoConfirmacao`, adicionada automaticamente na inicialização de bancos existentes. Conversas já encerradas pela versão anterior permanecem encerradas; inicie uma nova para testar o novo fluxo.

`Interessados` usa Telefone como PK e guarda os dez campos e ConversaID. Uma nova conversa concluída do mesmo telefone atualiza esse cadastro; os dados anteriores continuam no histórico da conversa. A conclusão e a resposta são gravadas na mesma transação. O corretor não é notificado automaticamente: a tabela é a fila de dados para a futura integração comercial.

SQLite usa WAL, conexões por operação e bloqueio temporário por conversa no banco. A IA roda fora da transação, permitindo atender conversas distintas simultaneamente; a capacidade de geração depende do hardware do Ollama. O bloqueio expira após 300 segundos em caso de queda do processo. Para alto volume ou múltiplas máquinas, planeje migrar para banco servidor e fila de processamento.

## Testes

```powershell
.\.venv\Scripts\python -m pytest -q
```

Testes usam SQLite temporário e IA substituída apenas nos testes, verificando isolamento, persistência, conclusão, repetição, autenticação, falha e concorrência. Para verificar qualidade do modelo, execute também uma conversa real na interface.

Integração de saída estruturada conforme a documentação oficial: https://docs.ollama.com/capabilities/structured-outputs


Caminhos relativos em `DATABASE_PATH` sao resolvidos a partir da raiz do projeto principal (pasta pai de `agente`), nunca do diretorio de execucao. A pasta de destino e criada automaticamente.

Apos a primeira confirmacao de cadastro, novas duvidas e correcoes recebem respostas contextuais da IA, mantendo a conversa aberta. O agente reconhece quando nao tem informacoes suficientes e nao consulta nem compartilha contatos de terceiros. O encerramento continua exigindo confirmacao explicita.


## Lembretes para atendimentos inativos

`POST /api/atendimentos/processar-inativos` aceita `{"limite":50}` (opcional; maximo 500) e usa a mesma autenticacao `X-API-Key`. O SELECT busca conversas ativas com mensagens, cuja ultima mensagem excedeu o prazo. Conversas vazias, encerradas, bloqueadas ou com resposta do agente pendente sao ignoradas.

Configuracao no terminal da API, antes de iniciar:

```powershell
$env:FOLLOWUP_IDLE_HOURS = '24'
$env:FOLLOWUP_INTERVAL_HOURS = '24'
$env:FOLLOWUP_MAX_ATTEMPTS = '3'
```

Os prazos aceitam numeros decimais positivos (ex.: `0.01` para testes em uma base separada). O primeiro lembrete e enviado depois da inatividade configurada. Os seguintes respeitam o intervalo. Apos o terceiro envio aceito, o sistema aguarda mais um intervalo; sem resposta, encerra com `Conversas.Status=encerrada` e `MotivoEncerramento=cancelado_por_inatividade`. O resultado do processamento informa `status=cancelada`. Esse motivo distingue cancelamento de encerramento solicitado pelo cliente, preservando compatibilidade com o CHECK do banco existente. Qualquer nova mensagem do cliente reinicia o ciclo. Uma conversa cancelada nao e selecionada novamente.

`Lembretes` persiste payload, tentativa, erro, identificador de entrega e data de envio. So HTTP 2xx conta como envio aceito; erros nao consomem as tres tentativas. Ha intervalo minimo de 60 segundos para repetir falhas. O mesmo evento e reutilizado apos falha, com `Idempotency-Key`; isso nao altera o contrato de entrada do WhatsApp. Se a API receptora aceitar a mensagem mas a conexao cair, ela deve deduplicar esse evento para evitar entregas repetidas. A resposta do cliente reinicia a contagem pelo ID interno da ultima mensagem recebida, sem memoria de sessao.

`followups.py` orquestra o envio e `reminder_store.py` centraliza o SQL e as reservas transacionais dos lembretes. Inclua ambos na entrega junto de `app.py`, `database.py` e `llm.py`. A rede opera fora da transacao; chamadas concorrentes nao reservam a mesma conversa enquanto houver bloqueio valido.

### Receptor local e monitor

O destino e configurado em `config.py`, na constante `FOLLOWUP_URL`. O valor padrao e: `http://127.0.0.1:5500/api/lembretes`, sem proxy ou redirecionamentos. O transporte para uma API externa real ainda depende da confirmacao do destino e do payload autorizado. Nenhuma mensagem e enviada diretamente ao WhatsApp pelo receptor de testes.

Inicie o receptor em outro terminal (na pasta `agente`):

```powershell
.\.venv\Scripts\python -m uvicorn receiver:app --app-dir interface-teste --host 127.0.0.1 --port 5500
```

Esse comando substitui `python -m http.server`; pare o servidor antigo se estiver usando a porta 5500. O receptor tambem serve o chat em `/`. Abra http://127.0.0.1:5500/lembretes para ver os recebimentos e clicar em **Processar atendimentos inativos**. O log e consultado a cada dois segundos e persiste em `interface-teste/recebimentos.sqlite3`, fora do banco comercial. Eventos repetidos aparecem apenas uma vez.

Payload enviado ao receptor:

```json
{
  "evento_id": "identificador-da-entrega",
  "conversa_id": 15,
  "telefone": "5511999999999",
  "tentativa": 1,
  "tipo": "retomada_atendimento",
  "mensagem": "Seu atendimento anterior esta em aberto. Resumo: ... Deseja continuar o atendimento anterior ou iniciar um novo?"
}
```

O resumo usa somente as preferencias da propria conversa. Se ainda nao houver preferencias, utiliza a ultima solicitacao do cliente. O lembrete aceito e salvo em Mensagens como bot e ativa a escolha de retomada existente.

A verificacao roda quando o endpoint e chamado. Para execucao periodica sem clicar na tela, configure um agendador externo (por exemplo, Agendador de Tarefas do Windows) para fazer POST nesse endpoint a cada 15 minutos. Nao ha tarefa de fundo implicita. O retorno inclui `enviados`, `cancelados`, `falhas` e os resultados por conversa.

Para alterar a API receptora de lembretes, edite `FOLLOWUP_URL` em `config.py` e reinicie a API do agente. Inclua `config.py` na entrega. O padrao continua sendo `http://127.0.0.1:5500/api/lembretes`.
