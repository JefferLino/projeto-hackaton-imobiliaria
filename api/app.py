"""API de CRUD de Corretores — porta 8001.

Camada HTTP pura: validação Pydantic, roteamento, CORS, erros HTTP.
Nunca acessa SQLite diretamente nem importa agente/.
"""
import os
from contextlib import asynccontextmanager
from typing import Literal, Optional

import jwt
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

import database
from services import corretores as svc
from services import imoveis as imoveis_svc
from services import leads as leads_svc

_jwt_secret = os.getenv('JWT_SECRET', 'dev-secret-imobiliaria-2026')


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(title='API Corretores', lifespan=lifespan)

_cors_origins = [o.strip() for o in os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=['*'],
    allow_headers=['*'],
)


# ---------------------------------------------------------------------------
# Modelos Pydantic
# ---------------------------------------------------------------------------

class CorretorCreate(BaseModel):
    nome: str
    email: str
    telefone: str
    senha: str

    @field_validator('nome')
    @classmethod
    def nome_sem_digitos(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 120:
            raise ValueError('Nome deve ter entre 2 e 120 caracteres')
        if any(c.isdigit() for c in v):
            raise ValueError('Nome não pode conter dígitos')
        return v

    @field_validator('email')
    @classmethod
    def email_formato(cls, v: str) -> str:
        import re
        v = v.strip()
        if not re.match(r'^\S+@\S+\.\S+$', v):
            raise ValueError('Email inválido')
        return v

    @field_validator('telefone')
    @classmethod
    def telefone_digitos(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) not in (10, 11):
            raise ValueError('Telefone deve conter somente dígitos (10 ou 11 caracteres)')
        return v

    @field_validator('senha')
    @classmethod
    def senha_minima(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')
        return v


class CorretorUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    senha: Optional[str] = None

    @field_validator('nome')
    @classmethod
    def nome_sem_digitos(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2 or len(v) > 120:
            raise ValueError('Nome deve ter entre 2 e 120 caracteres')
        if any(c.isdigit() for c in v):
            raise ValueError('Nome não pode conter dígitos')
        return v

    @field_validator('email')
    @classmethod
    def email_formato(cls, v):
        if v is None:
            return v
        import re
        v = v.strip()
        if not re.match(r'^\S+@\S+\.\S+$', v):
            raise ValueError('Email inválido')
        return v

    @field_validator('telefone')
    @classmethod
    def telefone_digitos(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v.isdigit() or len(v) not in (10, 11):
            raise ValueError('Telefone deve conter somente dígitos (10 ou 11 caracteres)')
        return v

    @field_validator('senha')
    @classmethod
    def senha_minima(cls, v):
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')
        return v


class CorretorResponse(BaseModel):
    id: int
    nome: str
    email: str
    telefone: str
    criado_em: str


class LeadResponse(BaseModel):
    conversa_id: int
    telefone: str
    nome: str
    status: str
    etapa: Literal[leads_svc.ETAPAS]
    corretor_id: Optional[int]
    corretor_nome: Optional[str]
    resumo: Optional[str]
    dados: dict
    atualizado_em: Optional[str]


class LeadUpdate(BaseModel):
    etapa: Optional[Literal[leads_svc.ETAPAS]] = None
    corretor_id: Optional[int] = None


TIPOS_NEGOCIO = ('compra', 'aluguel')
TIPOS_IMOVEL = ('casa', 'apartamento', 'comercial')
STATUS_IMOVEL = ('disponivel', 'reservado', 'vendido', 'alugado')


class ImovelCreate(BaseModel):
    titulo: str = Field(min_length=2, max_length=200)
    tipo_negocio: Literal[TIPOS_NEGOCIO]
    tipo_imovel: Literal[TIPOS_IMOVEL]
    estado: str = Field(min_length=2, max_length=60)
    bairro: str = Field(min_length=2, max_length=120)
    endereco: Optional[str] = Field(default=None, max_length=200)
    metragem: Optional[float] = Field(default=None, gt=0)
    quartos: Optional[int] = Field(default=None, ge=0)
    banheiros: Optional[int] = Field(default=None, ge=0)
    vagas: Optional[int] = Field(default=None, ge=0)
    valor: float = Field(gt=0)
    status: Literal[STATUS_IMOVEL] = 'disponivel'

    @field_validator('titulo', 'estado', 'bairro')
    @classmethod
    def strip_texto(cls, v: str) -> str:
        return v.strip()


class ImovelUpdate(BaseModel):
    titulo: Optional[str] = Field(default=None, min_length=2, max_length=200)
    tipo_negocio: Optional[Literal[TIPOS_NEGOCIO]] = None
    tipo_imovel: Optional[Literal[TIPOS_IMOVEL]] = None
    estado: Optional[str] = Field(default=None, min_length=2, max_length=60)
    bairro: Optional[str] = Field(default=None, min_length=2, max_length=120)
    endereco: Optional[str] = Field(default=None, max_length=200)
    metragem: Optional[float] = Field(default=None, gt=0)
    quartos: Optional[int] = Field(default=None, ge=0)
    banheiros: Optional[int] = Field(default=None, ge=0)
    vagas: Optional[int] = Field(default=None, ge=0)
    valor: Optional[float] = Field(default=None, gt=0)
    status: Optional[Literal[STATUS_IMOVEL]] = None

    @field_validator('titulo', 'estado', 'bairro')
    @classmethod
    def strip_texto(cls, v):
        return v.strip() if v else v


class ImovelResponse(BaseModel):
    id: int
    titulo: str
    tipo_negocio: str
    tipo_imovel: str
    estado: str
    bairro: str
    endereco: Optional[str]
    metragem: Optional[float]
    quartos: Optional[int]
    banheiros: Optional[int]
    vagas: Optional[int]
    valor: float
    status: str
    criado_em: str
    atualizado_em: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get('/api/corretores', response_model=list[CorretorResponse])
def listar_corretores():
    with database.db() as con:
        return svc.list_corretores(con)


@app.post('/api/corretores', response_model=CorretorResponse, status_code=201)
def criar_corretor(body: CorretorCreate):
    with database.db() as con:
        return svc.create_corretor(con, body.model_dump())


@app.get('/api/corretores/{corretor_id}', response_model=CorretorResponse)
def buscar_corretor(corretor_id: int):
    with database.db() as con:
        return svc.get_corretor(con, corretor_id)


@app.put('/api/corretores/{corretor_id}', response_model=CorretorResponse)
def atualizar_corretor(corretor_id: int, body: CorretorUpdate):
    with database.db() as con:
        return svc.update_corretor(con, corretor_id, body.model_dump(exclude_none=True))


@app.delete('/api/corretores/{corretor_id}', status_code=204)
def deletar_corretor(corretor_id: int):
    with database.db() as con:
        svc.delete_corretor(con, corretor_id)
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    senha: str


class CorretorAuth(BaseModel):
    id: int
    nome: str
    email: str


class LoginResponse(BaseModel):
    token: str
    corretor: CorretorAuth


@app.post('/api/auth/login', response_model=LoginResponse)
def login(body: LoginRequest):
    with database.db() as con:
        row = con.execute(
            'SELECT id, nome, email, senha_hash FROM Corretores WHERE email = ?',
            (body.email,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail='Usuário não encontrado')
    import bcrypt as _bcrypt
    if not _bcrypt.checkpw(body.senha.encode(), row['senha_hash'].encode()):
        raise HTTPException(status_code=401, detail='Senha inválida')
    payload = {'sub': row['id'], 'nome': row['nome'], 'email': row['email']}
    token = jwt.encode(payload, _jwt_secret, algorithm='HS256')
    return {'token': token, 'corretor': {'id': row['id'], 'nome': row['nome'], 'email': row['email']}}


# ---------------------------------------------------------------------------
# Pipeline de Leads
# ---------------------------------------------------------------------------

@app.get('/api/leads', response_model=list[LeadResponse])
def listar_leads(etapa: Optional[str] = None, corretor_id: Optional[int] = None):
    with database.db() as con:
        return leads_svc.list_leads(con, etapa, corretor_id)


@app.patch('/api/leads/{conversa_id}', response_model=LeadResponse)
def atualizar_lead(conversa_id: int, body: LeadUpdate):
    with database.db() as con:
        return leads_svc.update_lead(con, conversa_id, body.etapa, body.corretor_id)


# ---------------------------------------------------------------------------
# Imóveis
# ---------------------------------------------------------------------------

@app.get('/api/imoveis', response_model=list[ImovelResponse])
def listar_imoveis():
    with database.db() as con:
        return imoveis_svc.list_imoveis(con)


@app.post('/api/imoveis', response_model=ImovelResponse, status_code=201)
def criar_imovel(body: ImovelCreate):
    with database.db() as con:
        return imoveis_svc.create_imovel(con, body.model_dump())


@app.get('/api/imoveis/{imovel_id}', response_model=ImovelResponse)
def buscar_imovel(imovel_id: int):
    with database.db() as con:
        return imoveis_svc.get_imovel(con, imovel_id)


@app.put('/api/imoveis/{imovel_id}', response_model=ImovelResponse)
def atualizar_imovel(imovel_id: int, body: ImovelUpdate):
    with database.db() as con:
        return imoveis_svc.update_imovel(con, imovel_id, body.model_dump(exclude_none=True))


@app.delete('/api/imoveis/{imovel_id}', status_code=204)
def deletar_imovel(imovel_id: int):
    with database.db() as con:
        imoveis_svc.delete_imovel(con, imovel_id)
    return Response(status_code=204)
