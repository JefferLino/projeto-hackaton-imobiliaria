"""Lógica de negócio do CRUD de Corretores.

Recebe conexões abertas pelo app.py. Não importa FastAPI nem database.py
diretamente — apenas sqlite3 para capturar IntegrityError.
"""
import sqlite3

import bcrypt
from fastapi import HTTPException


def _row_to_dict(row) -> dict:
    return {k: row[k] for k in row.keys() if k != 'senha_hash'}


def list_corretores(con) -> list[dict]:
    rows = con.execute(
        'SELECT id, nome, email, telefone, criado_em FROM Corretores ORDER BY id'
    ).fetchall()
    return [dict(r) for r in rows]


def create_corretor(con, data: dict) -> dict:
    senha_hash = bcrypt.hashpw(data['senha'].encode(), bcrypt.gensalt(rounds=12)).decode()
    try:
        cur = con.execute(
            'INSERT INTO Corretores (nome, email, telefone, senha_hash) VALUES (?, ?, ?, ?)',
            (data['nome'], data['email'], data['telefone'], senha_hash),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail='Email já está em uso')
    row = con.execute(
        'SELECT id, nome, email, telefone, criado_em FROM Corretores WHERE id = ?',
        (cur.lastrowid,),
    ).fetchone()
    return dict(row)


def get_corretor(con, corretor_id: int) -> dict:
    row = con.execute(
        'SELECT id, nome, email, telefone, criado_em FROM Corretores WHERE id = ?',
        (corretor_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='Corretor não encontrado')
    return dict(row)


def update_corretor(con, corretor_id: int, data: dict) -> dict:
    existing = con.execute(
        'SELECT id, nome, email, telefone, senha_hash, criado_em FROM Corretores WHERE id = ?',
        (corretor_id,),
    ).fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail='Corretor não encontrado')

    nome = data.get('nome') or existing['nome']
    email = data.get('email') or existing['email']
    telefone = data.get('telefone') or existing['telefone']

    if data.get('senha'):
        senha_hash = bcrypt.hashpw(data['senha'].encode(), bcrypt.gensalt(rounds=12)).decode()
    else:
        senha_hash = existing['senha_hash']

    try:
        con.execute(
            '''UPDATE Corretores
               SET nome=?, email=?, telefone=?, senha_hash=?,
                   atualizado_em=CURRENT_TIMESTAMP
               WHERE id=?''',
            (nome, email, telefone, senha_hash, corretor_id),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail='Email já está em uso')

    row = con.execute(
        'SELECT id, nome, email, telefone, criado_em FROM Corretores WHERE id = ?',
        (corretor_id,),
    ).fetchone()
    return dict(row)


def delete_corretor(con, corretor_id: int) -> None:
    cur = con.execute('DELETE FROM Corretores WHERE id = ?', (corretor_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail='Corretor não encontrado')
