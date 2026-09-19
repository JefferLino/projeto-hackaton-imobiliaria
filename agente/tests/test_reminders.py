import importlib.util
from pathlib import Path
import time

import pytest
from fastapi.testclient import TestClient
import app
import database
import followups
import reminder_store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path/'db.sqlite3'))
    monkeypatch.delenv('API_KEY', raising=False)
    for key in ('FOLLOWUP_IDLE_HOURS','FOLLOWUP_INTERVAL_HOURS','FOLLOWUP_MAX_ATTEMPTS'):
        monkeypatch.delenv(key, raising=False)
    with TestClient(app.app) as client:
        yield client


def conversation(hours=25):
    cid = database.create_conversation('5511999999999','Ana')['conversa_id']
    with database.db() as con:
        mid = con.execute("INSERT INTO Mensagens(ConversaID,Texto,ResponsavelEnvio,Horario) VALUES (?,'Quero apartamento','cliente',datetime('now',?))", (cid,f'-{hours} hours')).lastrowid
        con.execute("INSERT INTO Mensagens(ConversaID,Texto,ResponsavelEnvio,EmRespostaA,Horario) VALUES (?,'Qual bairro?','bot',?,datetime('now',?))", (cid,mid,f'-{hours} hours'))
        con.execute('UPDATE Conversas SET Dados=? WHERE ID=?', ('{"tipo_imovel":"apartamento","bairro":"Moema"}',cid))
    return cid


def age():
    with database.db() as con:
        con.execute("UPDATE Mensagens SET Horario=datetime('now','-25 hours')")
        con.execute('UPDATE Lembretes SET EnviadoEm=?,UltimaTentativa=?', (time.time()-90000,time.time()-90000))


def test_three_attempts_then_cancel(client, monkeypatch):
    sent = []
    monkeypatch.setattr(followups,'send',sent.append)
    cid = conversation()
    for attempt in range(1,4):
        result=client.post('/api/atendimentos/processar-inativos',json={}).json()
        assert result['enviados']==1
        assert sent[-1]['tentativa']==attempt
        assert 'Moema' in sent[-1]['mensagem']
        assert followups.process()['enviados']==0
        age()
    result=followups.process()
    assert result['cancelados']==1
    with database.db() as con:
        row=con.execute('SELECT * FROM Conversas WHERE ID=?',(cid,)).fetchone()
        assert row['Status']=='encerrada'
        assert row['MotivoEncerramento']=='cancelado_por_inatividade'
    assert len(sent)==3


def test_recent_empty_closed_and_pending_not_sent(client, monkeypatch):
    sent=[]
    monkeypatch.setattr(followups,'send',sent.append)
    conversation(23)
    database.create_conversation('5521999999999','')
    cid=conversation()
    with database.db() as con:
        con.execute("UPDATE Conversas SET Status='encerrada' WHERE ID=?",(cid,))
    cid=conversation()
    database.save_message(cid,'5511999999999','Voltei')
    assert followups.process()['enviados']==0


def test_failure_retries_same_event_without_counting(client, monkeypatch):
    cid=conversation()
    jobs=[]
    def fail(payload):
        jobs.append(payload)
        raise TimeoutError()
    monkeypatch.setattr(followups,'send',fail)
    assert followups.process()['falhas']==1
    age()
    monkeypatch.setattr(followups,'send',jobs.append)
    assert followups.process()['enviados']==1
    assert jobs[0]==jobs[1]
    assert jobs[-1]['tentativa']==1


def test_customer_reply_resets_attempts(client, monkeypatch):
    sent=[]
    monkeypatch.setattr(followups,'send',sent.append)
    cid=conversation()
    followups.process()
    mid=database.save_message(cid,'5511999999999','continuar')['mensagem_id']
    with database.db() as con:
        con.execute("INSERT INTO Mensagens(ConversaID,Texto,ResponsavelEnvio,EmRespostaA) VALUES (?,'Vamos continuar','bot',?)",(cid,mid))
    age()
    followups.process()
    assert len(sent)==2
    assert sent[-1]['tentativa']==1


def test_claim_is_exclusive_and_configurable(client, monkeypatch):
    cid=conversation(2)
    assert reminder_store.claim(cid,24,24,3) is None
    job=reminder_store.claim(cid,1,1,1)
    assert job
    assert reminder_store.claim(cid,1,1,1) is None
    reminder_store.finish(job,True)
    age()
    monkeypatch.setenv('FOLLOWUP_IDLE_HOURS','1')
    monkeypatch.setenv('FOLLOWUP_MAX_ATTEMPTS','1')
    assert followups.process()['cancelados']==1


def test_receiver_persists_and_deduplicates(client, tmp_path, monkeypatch):
    path=Path(app.__file__).parent/'interface-teste'/'receiver.py'
    spec=importlib.util.spec_from_file_location('test_receiver_module',path)
    receiver=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(receiver)
    monkeypatch.setattr(receiver,'DB_PATH',str(tmp_path/'receiver.sqlite3'))
    with TestClient(receiver.app) as target:
        monkeypatch.setattr(followups,'send',lambda payload: target.post('/api/lembretes',json=payload).raise_for_status())
        conversation()
        assert followups.process()['enviados']==1
        log=target.get('/api/logs').json()
        assert len(log)==1
        target.post('/api/lembretes',json=log[0]['payload'])
        assert len(target.get('/api/logs').json())==1
        assert target.get('/lembretes').status_code==200



def test_transport_uses_configured_receiver(monkeypatch):
    import httpx
    calls=[]
    real_client=httpx.Client
    def handler(request):
        calls.append(request)
        return httpx.Response(200,json={'recebido':True})
    def local_client(**kwargs):
        assert kwargs['trust_env'] is False
        assert kwargs['follow_redirects'] is False
        return real_client(transport=httpx.MockTransport(handler),**kwargs)
    monkeypatch.setattr(followups.httpx,'Client',local_client)
    monkeypatch.setattr(followups.config, 'FOLLOWUP_URL', 'http://127.0.0.1:5510/teste')
    followups.send({'evento_id':'sample'})
    assert str(calls[0].url)=='http://127.0.0.1:5510/teste'
    assert calls[0].headers['Idempotency-Key']=='sample'


def test_auth_and_invalid_config(client, monkeypatch):
    monkeypatch.setenv('API_KEY','secret')
    assert client.post('/api/atendimentos/processar-inativos').status_code==401
    monkeypatch.setenv('FOLLOWUP_MAX_ATTEMPTS','0')
    response=client.post('/api/atendimentos/processar-inativos',headers={'X-API-Key':'secret'})
    assert response.status_code==500
