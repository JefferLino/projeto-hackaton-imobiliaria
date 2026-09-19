"""Persistência de lembretes; não realiza chamadas de rede."""
import json
import time
import uuid
import database


def init_db():
    with database.db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS Lembretes (
            ID TEXT PRIMARY KEY, ConversaID INTEGER NOT NULL REFERENCES Conversas(ID),
            UltimaMensagemClienteID INTEGER NOT NULL REFERENCES Mensagens(ID),
            Tentativa INTEGER NOT NULL, Payload TEXT NOT NULL,
            Status TEXT NOT NULL DEFAULT 'pendente', UltimaTentativa REAL NOT NULL DEFAULT 0,
            EnviadoEm REAL, Erro TEXT,
            UNIQUE(ConversaID, UltimaMensagemClienteID, Tentativa))''')
        if 'MotivoEncerramento' not in {r['name'] for r in con.execute('PRAGMA table_info(Conversas)')}:
            con.execute('ALTER TABLE Conversas ADD COLUMN MotivoEncerramento TEXT')


def candidates(hours, limit):
    with database.db() as con:
        return [r['ID'] for r in con.execute('''SELECT c.ID FROM Conversas c
            JOIN Mensagens m ON m.ConversaID=c.ID WHERE c.Status='ativa' AND c.LockAte<=?
            GROUP BY c.ID HAVING MAX(julianday(m.Horario)) < julianday('now') - ? / 24.0
            ORDER BY MAX(julianday(m.Horario)),c.ID LIMIT ?''', (time.time(),hours,limit))]


def claim(cid, hours, interval, maximum):
    with database.db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = con.execute('SELECT * FROM Conversas WHERE ID=?', (cid,)).fetchone()
        now = time.time()
        if not row or row['Status'] != 'ativa' or row['LockAte'] > now:
            return None
        age = con.execute("SELECT (julianday('now')-MAX(julianday(Horario)))*24 FROM Mensagens WHERE ConversaID=?", (cid,)).fetchone()[0]
        if age is None:
            return None
        last_client = con.execute("SELECT MAX(ID) FROM Mensagens WHERE ConversaID=? AND ResponsavelEnvio='cliente'", (cid,)).fetchone()[0]
        if last_client is None:
            return None
        pending = con.execute("SELECT 1 FROM Mensagens m WHERE ConversaID=? AND ResponsavelEnvio='cliente' AND NOT EXISTS (SELECT 1 FROM Mensagens r WHERE r.EmRespostaA=m.ID)", (cid,)).fetchone()
        if pending:
            return None
        sent = con.execute("SELECT COUNT(*),MAX(EnviadoEm) FROM Lembretes WHERE ConversaID=? AND UltimaMensagemClienteID=? AND Status='enviado'", (cid,last_client)).fetchone()
        if sent[0]:
            if now - sent[1] < interval * 3600:
                return None
        elif age <= hours:
            return None
        if sent[0] >= maximum:
            con.execute("UPDATE Conversas SET Status='encerrada',MotivoEncerramento='cancelado_por_inatividade',AguardandoRetomada=0,AguardandoConfirmacao=0 WHERE ID=?", (cid,))
            return {'conversa_id':cid,'status':'cancelada'}
        attempt = sent[0]+1
        old = con.execute('SELECT * FROM Lembretes WHERE ConversaID=? AND UltimaMensagemClienteID=? AND Tentativa=?', (cid,last_client,attempt)).fetchone()
        if old and now-old['UltimaTentativa'] < 60:
            return None
        token = uuid.uuid4().hex
        if old:
            event_id, payload = old['ID'], json.loads(old['Payload'])
        else:
            event_id = uuid.uuid4().hex
            text = database.resume_prompt(con,row)
            payload = {'evento_id':event_id,'conversa_id':cid,'telefone':row['Telefone'],
                       'tentativa':attempt,'tipo':'retomada_atendimento','mensagem':text}
            con.execute('INSERT INTO Lembretes(ID,ConversaID,UltimaMensagemClienteID,Tentativa,Payload) VALUES (?,?,?,?,?)',
                        (event_id,cid,last_client,attempt,json.dumps(payload,ensure_ascii=False)))
        con.execute('UPDATE Lembretes SET UltimaTentativa=? WHERE ID=?', (now,event_id))
        con.execute('UPDATE Conversas SET LockToken=?,LockAte=? WHERE ID=?', (token,now+60,cid))
        return {'status':'reservado','conversa_id':cid,'token':token,'payload':payload}


def finish(job, success, error=None):
    with database.db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = con.execute('SELECT * FROM Conversas WHERE ID=?', (job['conversa_id'],)).fetchone()
        if row['LockToken'] != job['token']:
            raise database.DatabaseError(409,'Reserva do lembrete expirou; repita o processamento')
        event_id = job['payload']['evento_id']
        if success:
            con.execute("UPDATE Lembretes SET Status='enviado',EnviadoEm=?,Erro=NULL WHERE ID=?", (time.time(),event_id))
            con.execute("INSERT INTO Mensagens(ConversaID,Texto,ResponsavelEnvio) VALUES (?,?,'bot')", (job['conversa_id'],job['payload']['mensagem']))
            con.execute('UPDATE Conversas SET AguardandoRetomada=1 WHERE ID=?', (job['conversa_id'],))
        else:
            con.execute('UPDATE Lembretes SET Erro=? WHERE ID=?', (error,event_id))
        con.execute('UPDATE Conversas SET LockToken=NULL,LockAte=0 WHERE ID=? AND LockToken=?', (job['conversa_id'],job['token']))
