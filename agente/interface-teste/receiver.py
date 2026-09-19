"""Servidor exclusivo de testes: recebe lembretes e serve a interface."""
import json
import os
import sqlite3
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DB_PATH = os.getenv('RECEIVER_DB_PATH', str(ROOT / 'recebimentos.sqlite3'))
app = FastAPI(title='Receptor local de testes')


def connection():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('CREATE TABLE IF NOT EXISTS Recebimentos (ID INTEGER PRIMARY KEY, EventoID TEXT UNIQUE, Payload TEXT NOT NULL, RecebidoEm TEXT DEFAULT CURRENT_TIMESTAMP)')
    return con


class Reminder(BaseModel):
    evento_id: str = Field(min_length=1,max_length=120)
    conversa_id: int
    telefone: str
    tentativa: int
    tipo: str
    mensagem: str


@app.post('/api/lembretes')
def receive(body: Reminder):
    con = connection()
    try:
        with con:
            con.execute('INSERT INTO Recebimentos(EventoID,Payload) VALUES (?,?) ON CONFLICT(EventoID) DO NOTHING',
                        (body.evento_id, body.model_dump_json()))
        return {'recebido':True,'evento_id':body.evento_id}
    finally:
        con.close()


@app.get('/api/logs')
def logs():
    con = connection()
    try:
        return [{'id':r['ID'],'recebido_em':r['RecebidoEm'],'payload':json.loads(r['Payload'])}
                for r in con.execute('SELECT * FROM Recebimentos ORDER BY ID DESC LIMIT 100')]
    finally:
        con.close()


@app.get('/')
def chat():
    return FileResponse(ROOT/'index.html')


@app.get('/config.js')
def config():
    return FileResponse(ROOT/'config.js', media_type='application/javascript')


@app.get('/lembretes')
def monitor():
    return FileResponse(ROOT/'lembretes.html')
