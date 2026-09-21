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
    'titulo': 'Apartamento 2 quartos em Moema',
    'tipo_negocio': 'compra',
    'tipo_imovel': 'apartamento',
    'estado': 'SP',
    'bairro': 'Moema',
    'endereco': 'Rua dos Ipês, 123',
    'metragem': 65.5,
    'quartos': 2,
    'banheiros': 1,
    'vagas': 1,
    'valor': 650000,
}


def test_listar_banco_vazio(client):
    res = client.get('/api/imoveis')
    assert res.status_code == 200
    assert res.json() == []


def test_cadastro_valido(client):
    res = client.post('/api/imoveis', json=VALID)
    assert res.status_code == 201
    data = res.json()
    assert data['titulo'] == VALID['titulo']
    assert data['status'] == 'disponivel'
    assert data['quartos'] == 2
    assert 'id' in data
    assert 'criado_em' in data


def test_cadastro_apenas_campos_obrigatorios(client):
    minimo = {'titulo': 'Sala comercial', 'tipo_negocio': 'aluguel', 'tipo_imovel': 'comercial',
              'estado': 'SP', 'bairro': 'Centro', 'valor': 3500}
    res = client.post('/api/imoveis', json=minimo)
    assert res.status_code == 201
    assert res.json()['metragem'] is None
    assert res.json()['quartos'] is None


def test_titulo_curto_invalido(client):
    res = client.post('/api/imoveis', json={**VALID, 'titulo': 'A'})
    assert res.status_code == 422


def test_tipo_negocio_invalido(client):
    res = client.post('/api/imoveis', json={**VALID, 'tipo_negocio': 'permuta'})
    assert res.status_code == 422


def test_tipo_imovel_invalido(client):
    res = client.post('/api/imoveis', json={**VALID, 'tipo_imovel': 'terreno'})
    assert res.status_code == 422


def test_valor_negativo_invalido(client):
    res = client.post('/api/imoveis', json={**VALID, 'valor': -100})
    assert res.status_code == 422


def test_metragem_zero_invalida(client):
    res = client.post('/api/imoveis', json={**VALID, 'metragem': 0})
    assert res.status_code == 422


def test_buscar_existente(client):
    iid = client.post('/api/imoveis', json=VALID).json()['id']
    res = client.get(f'/api/imoveis/{iid}')
    assert res.status_code == 200
    assert res.json()['bairro'] == 'Moema'


def test_buscar_inexistente(client):
    res = client.get('/api/imoveis/9999')
    assert res.status_code == 404


def test_atualizar_status_e_valor(client):
    iid = client.post('/api/imoveis', json=VALID).json()['id']
    res = client.put(f'/api/imoveis/{iid}', json={'status': 'vendido', 'valor': 620000})
    assert res.status_code == 200
    assert res.json()['status'] == 'vendido'
    assert res.json()['valor'] == 620000
    assert res.json()['titulo'] == VALID['titulo']


def test_atualizar_inexistente(client):
    res = client.put('/api/imoveis/9999', json={'status': 'vendido'})
    assert res.status_code == 404


def test_atualizar_status_invalido(client):
    iid = client.post('/api/imoveis', json=VALID).json()['id']
    res = client.put(f'/api/imoveis/{iid}', json={'status': 'demolido'})
    assert res.status_code == 422


def test_deletar_existente(client):
    iid = client.post('/api/imoveis', json=VALID).json()['id']
    res = client.delete(f'/api/imoveis/{iid}')
    assert res.status_code == 204
    assert client.get(f'/api/imoveis/{iid}').status_code == 404


def test_deletar_inexistente(client):
    res = client.delete('/api/imoveis/9999')
    assert res.status_code == 404


def test_listar_varios_ordenado_por_mais_recente(client):
    primeiro = client.post('/api/imoveis', json=VALID).json()['id']
    segundo = client.post('/api/imoveis', json={**VALID, 'titulo': 'Casa em Alphaville'}).json()['id']
    lista = client.get('/api/imoveis').json()
    assert [i['id'] for i in lista] == [segundo, primeiro]


def test_init_db_idempotente(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'idempotente.sqlite3'))
    database.init_db()
    database.init_db()
