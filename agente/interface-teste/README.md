# Interface de testes (não incluir na entrega da API)

Cliente web independente que simula o WhatsApp. Esta pasta pode ser copiada ou removida sem afetar a API. Não há dependências de FastAPI ou Ollama no servidor da interface.

## Executar

Na raiz do projeto, inicie a API em um terminal, liberando a origem da interface:

```powershell
.\interface-teste\iniciar-api.ps1
```

Em outro terminal, também na raiz:

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory interface-teste
```

Abra http://127.0.0.1:5500. Se já estiver dentro desta pasta, omita `--directory interface-teste`.

Se a API já estiver rodando, pare-a com Ctrl+C no terminal dela antes de executar o script. Ele autoriza as origens `http://127.0.0.1:5500` e `http://localhost:5500` somente no processo de teste. Alterar CORS_ORIGINS em outro terminal não modifica uma API já iniciada.

Para outra API, altere `API_BASE_URL` em `config.js`. Para outra origem da interface (protocolo, host ou porta), ajuste `CORS_ORIGINS` na API e reinicie-a. `localhost` e `127.0.0.1` são origens diferentes. Não abra o HTML diretamente com `file://`.

Se a API exigir `API_KEY`, preencha o campo de chave na página. A interface envia apenas telefone e texto a `/api/whatsapp/mensagens`. A API salva tudo no SQLite e escolhe o atendimento automaticamente. A tela consulta o histórico usando o ID retornado. Não é necessário criar uma conversa manualmente. Após 24 horas de inatividade, responda “continuar” ou “novo” à pergunta de retomada. Nome e telefone para contato serão pedidos na própria conversa antes do encaminhamento. Em caso de falha da IA após salvar a mensagem, o botão de tentativa usa os IDs internos retornados para gerar a resposta sem repetir a gravação.

## Entrega

Esta pasta inteira é opcional e deve ficar fora do pacote de produção. A API não importa nem serve seus arquivos. A integração do WhatsApp não precisa de CORS; deixe `CORS_ORIGINS` sem configuração quando não houver cliente de navegador.
