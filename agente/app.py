import json
import os
import secrets
from typing import Literal
from contextlib import asynccontextmanager

import database
import followups
import reminder_store
import llm
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

REQUIRED = ['estado', 'bairro', 'tipo_negocio', 'tipo_imovel', 'urgencia']
CONTACT_REQUIRED = ['nome_contato', 'telefone_contato']


@asynccontextmanager
async def lifespan(app):
    database.init_db()
    reminder_store.init_db()
    yield


app = FastAPI(title='Agente imobiliário', lifespan=lifespan)


@app.exception_handler(database.DatabaseError)
async def database_error_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})


@app.exception_handler(llm.LLMError)
async def llm_error_handler(request, exc):
    return JSONResponse(status_code=503, content={'detail': str(exc)})


# Habilite apenas quando um cliente web em outra origem precisar acessar a API.
cors_origins = [origin.strip() for origin in os.getenv('CORS_ORIGINS', '').split(',') if origin.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=['GET', 'POST'],
        allow_headers=['Content-Type', 'X-API-Key'],
    )


def auth(x_api_key: str = Header(default='')):
    key = os.getenv('API_KEY', '')
    if key and not secrets.compare_digest(key, x_api_key):
        raise HTTPException(401, 'Chave de API inválida')


class Identity(BaseModel):
    telefone: str = Field(pattern=r'^\+?[0-9]{10,15}$')


class NewConversation(Identity):
    nome: str = Field(default='', max_length=120)


class NewMessage(Identity):
    texto: str = Field(min_length=1, max_length=4000, pattern=r'\S')


class AgentRequest(Identity):
    conversa_id: int = Field(gt=0)
    mensagem_id: int = Field(gt=0)


class WhatsAppMessage(NewMessage):
    opcao_atendimento: Literal['continuar', 'novo'] | None = None


@app.post('/api/whatsapp/mensagens', dependencies=[Depends(auth)])
def whatsapp_message(body: WhatsAppMessage):
    inferred = None
    if body.opcao_atendimento is None and database.waiting_resume(body.telefone):
        normalized = body.texto.strip().lower().rstrip('.!')
        try:
            inferred = normalized if normalized in ('continuar', 'novo') else llm.resume_choice(body.texto)
        except llm.LLMError:
            # Ainda salva a mensagem e repete a escolha sem decidir pelo cliente.
            inferred = None
    cid, mid, cached = database.receive_whatsapp(body.telefone, body.texto,
                                               body.opcao_atendimento, inferred)
    if cached is not None:
        return cached
    try:
        return respond(AgentRequest(telefone=body.telefone, conversa_id=cid, mensagem_id=mid))
    except llm.LLMError as exc:
        return JSONResponse(status_code=503, content={'detail': str(exc), 'conversa_id': cid, 'mensagem_id': mid})


@app.post('/api/conversas', dependencies=[Depends(auth)])
def create_conversation(body: NewConversation):
    return database.create_conversation(body.telefone, body.nome)


@app.get('/api/conversas/{cid}', dependencies=[Depends(auth)])
def history(cid: int, telefone: str):
    return database.history(cid, telefone)


@app.post('/api/conversas/{cid}/mensagens', dependencies=[Depends(auth)])
def save_message(cid: int, body: NewMessage):
    return database.save_message(cid, body.telefone, body.texto)


@app.post('/api/agente/responder', dependencies=[Depends(auth)])
def respond(body: AgentRequest):
    token = secrets.token_hex(16)
    row, records, cached = database.begin_response(
        body.conversa_id, body.telefone, body.mensagem_id, token)
    if cached is not None:
        return cached
    try:
        selected, size = [], 0
        for record in records:
            if size + len(record['Texto']) > 24000:
                break
            selected.append(record)
            size += len(record['Texto'])
        messages = [{'role': 'user' if m['ResponsavelEnvio'] == 'cliente' else 'assistant', 'content': m['Texto']} for m in reversed(selected)]
        current = json.loads(row['Dados'])
        previous_reply = next((m['content'] for m in reversed(messages[:-1]) if m['role'] == 'assistant'), None)
        resume_text = messages[-1]['content'].strip().lower().strip('.!?, ')
        if previous_reply == llm.FALLBACK_REPLY and resume_text in {
            'sim', 's', 'claro', 'ok', 'vamos', 'continuar', 'prosseguir', 'pode continuar',
            'quero continuar', 'quero prosseguir', 'sim quero continuar', 'sim, quero continuar',
            'sim quero prosseguir', 'sim, quero prosseguir', 'sim, por favor', 'sim por favor',
        }:
            pending_fields = [key for key in REQUIRED + CONTACT_REQUIRED if not current.get(key)]
            labels = {'estado': 'o estado de interesse', 'bairro': 'o bairro de interesse',
                      'tipo_negocio': 'se deseja comprar ou alugar', 'tipo_imovel': 'se procura casa, apartamento ou comercial',
                      'urgencia': 'a urgência (baixa, média ou alta)', 'nome_contato': 'seu nome',
                      'telefone_contato': 'seu telefone para contato com DDD'}
            property_missing = [key for key in REQUIRED if not current.get(key)]
            contact_missing = [key for key in CONTACT_REQUIRED if not current.get(key)]
            offered = bool(row['OpcionaisOferecidos'])
            if property_missing:
                reply = 'Claro, vamos continuar! Para seguir, me informe ' + ' e '.join(labels[key] for key in property_missing[:2]) + '.'
            elif not offered:
                reply = 'Claro, vamos continuar! Deseja informar metragem, quartos, banheiros, vagas ou valor máximo? Esses detalhes são opcionais; pode pular.'
                offered = True
            elif contact_missing:
                reply = 'Claro, vamos continuar! Antes de encaminhar ao consultor, preciso de ' + ' e '.join(labels[key] for key in contact_missing) + '.'
            else:
                reply = 'Claro! Seus dados já estão completos. Você gostaria de alterar alguma informação ou encerrar o atendimento para aguardar o contato do consultor?'
            result = {'conversa_id': body.conversa_id, 'mensagem_id': body.mensagem_id,
                      'resposta': reply, 'status': 'ativa', 'dados': current,
                      'aguardando_confirmacao': bool(row['AguardandoConfirmacao']),
                      'aguardando_retomada': False, 'campos_obrigatorios_pendentes': pending_fields}
            database.finish_response(body.conversa_id, body.telefone, body.mensagem_id,
                                     token, current, False, offered, result)
            return result
        if llm.requests_other_records(messages[-1]['content']):
            result = {
                'conversa_id': body.conversa_id, 'mensagem_id': body.mensagem_id,
                'resposta': llm.PRIVATE_DATA_REPLY, 'status': 'ativa',
                'aguardando_confirmacao': bool(row['AguardandoConfirmacao']),
                'dados': current, 'aguardando_retomada': False,
                'campos_obrigatorios_pendentes': [key for key in REQUIRED + CONTACT_REQUIRED if not current.get(key)],
            }
            database.finish_response(body.conversa_id, body.telefone, body.mensagem_id,
                                     token, current, False, bool(row['OpcionaisOferecidos']), result)
            return result
        extracted = llm.extract_preferences(current, messages)
        if extracted.nao_pode_responder:
            result = {
                'conversa_id': body.conversa_id, 'mensagem_id': body.mensagem_id,
                'resposta': llm.FALLBACK_REPLY, 'status': 'ativa',
                'aguardando_confirmacao': bool(row['AguardandoConfirmacao']),
                'dados': current, 'aguardando_retomada': False,
                'campos_obrigatorios_pendentes': [key for key in REQUIRED + CONTACT_REQUIRED if not current.get(key)],
            }
            database.finish_response(body.conversa_id, body.telefone, body.mensagem_id,
                                     token, current, False, bool(row['OpcionaisOferecidos']), result)
            return result
        updates = extracted.dados.model_dump(exclude_none=True)
        changed = {key: value for key, value in updates.items() if current.get(key) != value}
        current.update(updates)
        missing = [key for key in REQUIRED if not current.get(key)]
        contact_missing = [key for key in CONTACT_REQUIRED if not current.get(key)]
        optional = [key for key in llm.Preferences.model_fields if key not in REQUIRED + CONTACT_REQUIRED and current.get(key) is None]
        preferences_ready = not missing and (not optional or extracted.dispensar_opcionais or bool(row['OpcionaisOferecidos']))
        complete = preferences_ready and not contact_missing
        offered = bool(row['OpcionaisOferecidos']) or not missing
        closing = complete and bool(row['AguardandoConfirmacao']) and extracted.encerrar_conversa
        instruction = ('Confirme brevemente as preferências registradas, sem perguntas e sem dizer que a conversa foi encerrada.' if complete else
                       'Antes de encaminhar ao consultor, peça estes dados obrigatórios: ' + ', '.join(contact_missing) + '. Peça o telefone para contato com DDD; ele é um campo separado do identificador do WhatsApp.' if preferences_ready else
                       'Pergunte somente estes campos obrigatórios ausentes: ' + ', '.join(missing[:2]) if missing else
                       'Pergunte em uma única mensagem quais destas preferências opcionais deseja informar: ' + ', '.join(optional) + '. Explique que pode pular ou informar só algumas.')
        reply = '' if complete else llm.generate_reply(current, instruction, messages)
        if complete:
            # Esta etapa precisa corresponder exatamente ao estado persistido, sem depender da redação da IA.
            reply = ('Conversa encerrada. Um consultor irá entrar em contato em breve. Obrigado!' if closing else
                     'Suas preferências foram salvas. Um consultor irá entrar em contato. Deseja encerrar a conversa ou alterar algo?')
        if complete and row['AguardandoConfirmacao'] and not closing:
            instruction = (
                'O cadastro ja esta completo e a conversa permanece aberta. Responda primeiro a ultima mensagem do cliente. '
                'Se houve correcao, confirme apenas os campos alterados, sem repetir o cadastro inteiro. '
                'Se for uma pergunta, responda com base apenas nos dados deste atendimento. '
                'Se nao souber, diga isso com naturalidade e ofereca ajuda com o proprio atendimento. '
                'Nao repita automaticamente a frase Suas preferencias foram salvas nem a pergunta de encerramento. '
                'Nao diga que a conversa foi encerrada. Campos alterados neste turno: '
                + json.dumps(changed, ensure_ascii=False)
            )
            reply = llm.generate_reply(current, instruction, messages)
        result = {'conversa_id': body.conversa_id, 'mensagem_id': body.mensagem_id, 'resposta': reply,
                  'status': 'encerrada' if closing else 'ativa', 'aguardando_confirmacao': complete and not closing,
                  'dados': current, 'campos_obrigatorios_pendentes': missing + contact_missing, 'aguardando_retomada':False}
        database.finish_response(body.conversa_id, body.telefone, body.mensagem_id,
                                 token, current, complete, offered, result)
        return result
    finally:
        database.release_response(body.conversa_id, token)


class FollowupRequest(BaseModel):
    limite: int = Field(default=50, ge=1, le=500)


@app.post('/api/atendimentos/processar-inativos', dependencies=[Depends(auth)])
def process_inactive(body: FollowupRequest = FollowupRequest()):
    return followups.process(body.limite)
