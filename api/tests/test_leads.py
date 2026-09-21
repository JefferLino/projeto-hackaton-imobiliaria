import json

import pytest
from fastapi.testclient import TestClient

import app
import database


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'test.sqlite3'))
    with TestClient(app.app) as c:
        yield c


def seed_conversa(cid, telefone='11987654321', nome='Maria Silva', status='ativa',
                   aguardando_confirmacao=0, dados=None):
    with database.db() as con:
        con.execute('''
            CREATE TABLE IF NOT EXISTS Usuarios (Telefone TEXT PRIMARY KEY, Nome TEXT);
        ''')
        con.execute('''
            CREATE TABLE IF NOT EXISTS Conversas (
              ID INTEGER PRIMARY KEY, Telefone TEXT NOT NULL, Status TEXT NOT NULL DEFAULT 'ativa',
              Resumo TEXT, Dados TEXT NOT NULL DEFAULT '{}', AguardandoConfirmacao INTEGER NOT NULL DEFAULT 0
            );
        ''')
        con.execute('INSERT INTO Usuarios(Telefone,Nome) VALUES (?,?) ON CONFLICT(Telefone) DO NOTHING', (telefone, nome))
        con.execute('''
            INSERT INTO Conversas(ID,Telefone,Status,AguardandoConfirmacao,Dados)
            VALUES (?,?,?,?,?)
        ''', (cid, telefone, status, aguardando_confirmacao, json.dumps(dados or {})))


def criar_corretor(client, nome='Ana Souza', email='ana@example.com'):
    res = client.post('/api/corretores', json={
        'nome': nome, 'email': email, 'telefone': '11987654321', 'senha': 'senha123',
    })
    return res.json()['id']


def test_listar_banco_vazio(client):
    res = client.get('/api/leads')
    assert res.status_code == 200
    assert res.json() == []


def test_etapa_sugerida_novo(client):
    seed_conversa(1)
    res = client.get('/api/leads')
    assert res.status_code == 200
    lead = res.json()[0]
    assert lead['conversa_id'] == 1
    assert lead['etapa'] == 'novo'
    assert lead['corretor_id'] is None


def test_etapa_sugerida_qualificando_com_dados_parciais(client):
    seed_conversa(1, dados={'estado': 'SP'})
    lead = client.get('/api/leads').json()[0]
    assert lead['etapa'] == 'qualificando'


def test_etapa_sugerida_qualificado_aguardando_confirmacao(client):
    seed_conversa(1, aguardando_confirmacao=1, dados={'estado': 'SP'})
    lead = client.get('/api/leads').json()[0]
    assert lead['etapa'] == 'qualificado'


def test_etapa_sugerida_fechado_quando_encerrada(client):
    seed_conversa(1, status='encerrada', dados={'estado': 'SP'})
    lead = client.get('/api/leads').json()[0]
    assert lead['etapa'] == 'fechado'


def test_patch_etapa_manual_sobrescreve_sugestao(client):
    seed_conversa(1)
    res = client.patch('/api/leads/1', json={'etapa': 'agendado'})
    assert res.status_code == 200
    assert res.json()['etapa'] == 'agendado'
    assert client.get('/api/leads').json()[0]['etapa'] == 'agendado'


def test_patch_apenas_corretor_preserva_etapa_manual(client):
    seed_conversa(1)
    cor_id = criar_corretor(client)
    client.patch('/api/leads/1', json={'etapa': 'agendado'})
    res = client.patch('/api/leads/1', json={'corretor_id': cor_id})
    assert res.status_code == 200
    assert res.json()['corretor_id'] == cor_id
    assert res.json()['etapa'] == 'agendado'


def test_patch_apenas_etapa_preserva_corretor(client):
    seed_conversa(1)
    cor_id = criar_corretor(client)
    client.patch('/api/leads/1', json={'corretor_id': cor_id})
    res = client.patch('/api/leads/1', json={'etapa': 'fechado'})
    assert res.status_code == 200
    assert res.json()['etapa'] == 'fechado'
    assert res.json()['corretor_id'] == cor_id


def test_patch_conversa_inexistente(client):
    res = client.patch('/api/leads/999', json={'etapa': 'fechado'})
    assert res.status_code == 404


def test_patch_corretor_inexistente(client):
    seed_conversa(1)
    res = client.patch('/api/leads/1', json={'corretor_id': 999})
    assert res.status_code == 404


def test_patch_etapa_invalida(client):
    seed_conversa(1)
    res = client.patch('/api/leads/1', json={'etapa': 'inventada'})
    assert res.status_code == 422


def test_filtro_por_etapa(client):
    seed_conversa(1)
    seed_conversa(2, telefone='11911112222')
    client.patch('/api/leads/1', json={'etapa': 'fechado'})
    res = client.get('/api/leads', params={'etapa': 'fechado'})
    assert [lead['conversa_id'] for lead in res.json()] == [1]


def test_filtro_por_corretor(client):
    seed_conversa(1)
    seed_conversa(2, telefone='11911112222')
    cor_id = criar_corretor(client)
    client.patch('/api/leads/1', json={'corretor_id': cor_id})
    res = client.get('/api/leads', params={'corretor_id': cor_id})
    assert [lead['conversa_id'] for lead in res.json()] == [1]
