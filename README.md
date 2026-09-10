# Agente SDR Imobiliario com IA

Prova de conceito (POC) de um agente SDR para imobiliarias. O produto usa inteligencia artificial generativa para atender leads, entender suas necessidades, qualifica-los e apoiar o corretor na proxima melhor acao.

Este projeto foi concebido para o **Tech Challenge - Fase 5** da POSTECH/FIAP.

## Problema

Leads imobiliarios frequentemente se perdem por demora na resposta, falta de acompanhamento, atendimento manual e dificuldade de identificar quais contatos tem maior potencial de conversao. O objetivo desta POC e reduzir esses gargalos com um atendimento conversacional continuo e orientado a dados.

## Objetivos

- Atender leads automaticamente, com linguagem natural e humanizada.
- Identificar a intencao: compra, aluguel ou investimento.
- Coletar dados para qualificacao, como regiao, faixa de preco, numero de quartos, urgencia e perfil do cliente.
- Consultar uma base simulada de imoveis para sugerir opcoes aderentes.
- Manter o contexto entre interacoes e executar follow-up quando o lead parar de responder.
- Agendar reunioes ou visitas para leads qualificados.
- Gerar um resumo estruturado para que o corretor assuma o atendimento com contexto.
- Disponibilizar um dashboard minimo para acompanhamento dos leads.

## Fluxo da solucao

```text
Lead
  -> Canal de atendimento
  -> Agente conversacional
  -> Classificacao de intencao e qualificacao
  -> Consulta a base simulada de imoveis
  -> Proxima acao: sugestao, follow-up, agendamento ou encaminhamento
  -> Resumo e dashboard para o corretor
```

## Cenarios atendidos

### Compra

Ao receber uma mensagem como "Estou procurando apartamento na zona sul", o agente deve identificar a intencao de compra e coletar, de forma progressiva:

- faixa de preco;
- quantidade de quartos;
- regiao de interesse;
- prazo ou urgencia de compra.

Com a qualificacao suficiente, o agente sugere a proxima etapa e oferece uma reuniao ou visita.

### Investimento

Para uma mensagem como "Quero investir em imoveis para renda", o agente identifica o perfil investidor e pergunta pelo ticket disponivel e pela expectativa de retorno. Em seguida, direciona o lead para um especialista.

### Follow-up

Se o lead interromper a conversa, o agente deve retomar o contato preservando o contexto ja coletado e convidando-o a continuar o atendimento.

## Requisitos funcionais

- Atendimento conversacional natural e humanizado.
- Continuidade e memoria de conversa.
- Qualificacao de leads.
- Agendamento de reunioes ou visitas.
- Resumo inteligente para corretores.
- Dashboard minimo de acompanhamento.

## Diferenciais previstos

A POC pode evoluir com os seguintes diferenciais:

- RAG para consulta de catalogo, politicas e informacoes imobiliarias;
- integracao com WhatsApp;
- memoria conversacional persistente;
- arquitetura multiagente;
- Voice AI;
- integracao com CRM;
- observabilidade, seguranca e deploy em cloud.

## Arquitetura proposta

| Camada | Responsabilidade |
| --- | --- |
| Interface/canais | Receber e enviar mensagens ao lead. |
| Orquestrador de IA | Gerenciar o dialogo, contexto, regras e proxima acao. |
| Servico de qualificacao | Estruturar dados do lead e calcular seu nivel de qualificacao. |
| Catalogo de imoveis | Fornecer a base simulada para busca e recomendacao. |
| Agenda e follow-up | Criar agendamentos e disparar retomadas de contato. |
| Dashboard | Exibir funil, status dos leads e resumos para corretores. |
| Persistencia | Armazenar leads, conversas, preferencias e eventos. |

## Dados de qualificacao

| Campo | Exemplos |
| --- | --- |
| Intencao | Compra, aluguel ou investimento |
| Regiao | Zona sul, bairro ou cidade |
| Orcamento/ticket | Faixa de preco disponivel |
| Preferencias | Tipo de imovel, quartos, vagas e caracteristicas desejadas |
| Urgencia | Imediata, curto prazo ou sem prazo definido |
| Perfil investidor | Objetivo de renda e expectativa de retorno |
| Proxima acao | Visita, reuniao, especialista ou follow-up |

## Criterios de sucesso

A solucao deve demonstrar:

- arquitetura organizada, componentizada e com potencial de escala;
- respostas contextualizadas, uteis e humanizadas;
- interface clara e facil de usar;
- ao menos um diferencial tecnico relevante para o negocio.

## Entregaveis do desafio

- Repositorio do projeto.
- README.
- Arquitetura da solucao.
- Demonstracao funcional.
- Pitch tecnico.
- Explicacao da IA utilizada.

## Como executar

> A implementacao ainda nao foi adicionada a este repositorio. Quando a stack for definida, inclua aqui os pre-requisitos, as variaveis de ambiente e os comandos de instalacao e execucao.

## Roadmap sugerido

1. Criar a interface de chat e a base simulada de imoveis.
2. Implementar a qualificacao e o resumo estruturado do lead.
3. Integrar o modelo de IA e a memoria conversacional.
4. Adicionar agendamento, follow-up e dashboard.
5. Evoluir com RAG, integracao com CRM/WhatsApp e observabilidade.

## Licenca

Definir conforme a estrategia de distribuicao do projeto.
