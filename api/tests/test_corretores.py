import pytest
from fastapi.testclient import TestClient

import app
import database


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'test.sqlite3'))
    with TestClient(app.app) as c:
        yield c


VALID = {
    'nome': 'Maria Silva',
    'email': 'maria@example.com',
    'telefone': '11987654321',
    'senha': 'senha123',
}


def test_listar_banco_vazio(client):
    res = client.get('/api/corretores')
    assert res.status_code == 200
    assert res.json() == []


def test_cadastro_valido(client):
    res = client.post('/api/corretores', json=VALID)
    assert res.status_code == 201
    data = res.json()
    assert data['nome'] == VALID['nome']
    assert data['email'] == VALID['email']
    assert data['telefone'] == VALID['telefone']
    assert 'id' in data
    assert 'criado_em' in data
    assert 'senha_hash' not in data
    assert 'senha' not in data


def test_email_duplicado(client):
    client.post('/api/corretores', json=VALID)
    res = client.post('/api/corretores', json={**VALID, 'nome': 'Outro Nome'})
    assert res.status_code == 409
    assert 'Email' in res.json()['detail']


def test_nome_com_digito(client):
    res = client.post('/api/corretores', json={**VALID, 'nome': 'Maria123'})
    assert res.status_code == 422


def test_email_invalido(client):
    res = client.post('/api/corretores', json={**VALID, 'email': 'naoemail'})
    assert res.status_code == 422


def test_senha_curta(client):
    res = client.post('/api/corretores', json={**VALID, 'senha': '1234567'})
    assert res.status_code == 422


def test_telefone_invalido(client):
    res = client.post('/api/corretores', json={**VALID, 'telefone': '123'})
    assert res.status_code == 422


def test_buscar_existente(client):
    cid = client.post('/api/corretores', json=VALID).json()['id']
    res = client.get(f'/api/corretores/{cid}')
    assert res.status_code == 200
    assert res.json()['email'] == VALID['email']


def test_buscar_inexistente(client):
    res = client.get('/api/corretores/9999')
    assert res.status_code == 404


def test_atualizar_nome_telefone(client):
    cid = client.post('/api/corretores', json=VALID).json()['id']
    res = client.put(f'/api/corretores/{cid}', json={'nome': 'Novo Nome', 'telefone': '11911112222'})
    assert res.status_code == 200
    assert res.json()['nome'] == 'Novo Nome'
    assert res.json()['telefone'] == '11911112222'


def test_atualizar_senha_gera_hash_novo(client, tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'test2.sqlite3'))
    with TestClient(app.app) as c:
        cid = c.post('/api/corretores', json=VALID).json()['id']
        with database.db() as con:
            hash_antes = con.execute('SELECT senha_hash FROM Corretores WHERE id=?', (cid,)).fetchone()['senha_hash']
        c.put(f'/api/corretores/{cid}', json={'senha': 'novasenha99'})
        with database.db() as con:
            hash_depois = con.execute('SELECT senha_hash FROM Corretores WHERE id=?', (cid,)).fetchone()['senha_hash']
        assert hash_antes != hash_depois


def test_atualizar_sem_senha_preserva_hash(client, tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'test3.sqlite3'))
    with TestClient(app.app) as c:
        cid = c.post('/api/corretores', json=VALID).json()['id']
        with database.db() as con:
            hash_antes = con.execute('SELECT senha_hash FROM Corretores WHERE id=?', (cid,)).fetchone()['senha_hash']
        c.put(f'/api/corretores/{cid}', json={'nome': 'Outro Nome'})
        with database.db() as con:
            hash_depois = con.execute('SELECT senha_hash FROM Corretores WHERE id=?', (cid,)).fetchone()['senha_hash']
        assert hash_antes == hash_depois


def test_deletar_existente(client):
    cid = client.post('/api/corretores', json=VALID).json()['id']
    res = client.delete(f'/api/corretores/{cid}')
    assert res.status_code == 204
    assert client.get(f'/api/corretores/{cid}').status_code == 404


def test_deletar_inexistente(client):
    res = client.delete('/api/corretores/9999')
    assert res.status_code == 404


def test_senha_nunca_retornada(client):
    cid = client.post('/api/corretores', json=VALID).json()['id']
    lista = client.get('/api/corretores').json()
    assert all('senha_hash' not in c and 'senha' not in c for c in lista)
    individual = client.get(f'/api/corretores/{cid}').json()
    assert 'senha_hash' not in individual
    assert 'senha' not in individual


def test_init_db_idempotente(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'idempotente.sqlite3'))
    database.init_db()
    database.init_db()  # segunda chamada não deve falhar


def test_coexistencia_com_tabelas_do_agente(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'shared.sqlite3'))
    # simula tabelas criadas pelo agente
    with database.db() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS Usuarios (Telefone TEXT PRIMARY KEY, Nome TEXT);
        CREATE TABLE IF NOT EXISTS Conversas (ID INTEGER PRIMARY KEY, Telefone TEXT);
        CREATE TABLE IF NOT EXISTS Mensagens (ID INTEGER PRIMARY KEY, ConversaID INTEGER);
        ''')
    database.init_db()
    with database.db() as con:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert 'Corretores' in tables
    assert 'Usuarios' in tables
    assert 'Conversas' in tables
    assert 'Mensagens' in tables
