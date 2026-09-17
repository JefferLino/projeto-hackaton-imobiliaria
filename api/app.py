"""API de CRUD de Corretores — porta 8001.

Camada HTTP pura: validação Pydantic, roteamento, CORS, erros HTTP.
Nunca acessa SQLite diretamente nem importa agente/.
"""
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

import database
from services import corretores as svc


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
