"""Persistência: esquema, histórico, cadastro e transações por conversa.

Não depende da API nem do Ollama. Cada operação abre e fecha sua conexão.
"""
import json
import os
import sqlite3
import time
from contextlib import contextmanager

DB_PATH = os.getenv('DATABASE_PATH', 'imobiliaria.sqlite3')


class DatabaseError(Exception):
    """Conflito ou registro ausente; a API traduz o código para HTTP."""

    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@contextmanager
def db():
    """Abre conexão e confirma a transação, ou desfaz alterações em caso de erro."""
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    """Cria tabelas e aplica migrações compatíveis com bancos existentes."""
    with db() as con:
        con.execute('PRAGMA journal_mode=WAL')
        con.executescript('''
        CREATE TABLE IF NOT EXISTS Usuarios (
          Telefone TEXT PRIMARY KEY, Nome TEXT, Data TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS Conversas (
          ID INTEGER PRIMARY KEY, Telefone TEXT NOT NULL REFERENCES Usuarios(Telefone),
          DataInicio TEXT DEFAULT CURRENT_TIMESTAMP, Status TEXT NOT NULL DEFAULT 'ativa'
          CHECK(Status IN ('ativa','encerrada')), Feedback TEXT, Resumo TEXT,
          Dados TEXT NOT NULL DEFAULT '{}', OpcionaisOferecidos INTEGER NOT NULL DEFAULT 0,
          LockToken TEXT, LockAte REAL NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS Mensagens (
          ID INTEGER PRIMARY KEY, ConversaID INTEGER NOT NULL REFERENCES Conversas(ID),
          Texto TEXT NOT NULL, Horario TEXT DEFAULT CURRENT_TIMESTAMP,
          ResponsavelEnvio TEXT NOT NULL CHECK(ResponsavelEnvio IN ('cliente','bot')),
          EmRespostaA INTEGER UNIQUE REFERENCES Mensagens(ID),
          Resultado TEXT);
        CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON Mensagens(ConversaID, ID);
        CREATE TABLE IF NOT EXISTS Interessados (
          Telefone TEXT PRIMARY KEY REFERENCES Usuarios(Telefone),
          ConversaID INTEGER NOT NULL REFERENCES Conversas(ID),
          Estado TEXT NOT NULL, Bairro TEXT NOT NULL, Metragem REAL,
          Banheiros INTEGER, Quartos INTEGER, ValorMaximo REAL, Vagas INTEGER,
          TipoNegocio TEXT NOT NULL, TipoImovel TEXT NOT NULL, Urgencia TEXT NOT NULL,
          AtualizadoEm TEXT DEFAULT CURRENT_TIMESTAMP);
        ''')
        columns = {r['name'] for r in con.execute('PRAGMA table_info(Conversas)')}
        if 'AguardandoConfirmacao' not in columns:
            con.execute('ALTER TABLE Conversas ADD COLUMN AguardandoConfirmacao INTEGER NOT NULL DEFAULT 0')
        if 'AguardandoRetomada' not in columns:
            con.execute('ALTER TABLE Conversas ADD COLUMN AguardandoRetomada INTEGER NOT NULL DEFAULT 0')
        if 'TelefoneContato' not in {r['name'] for r in con.execute('PRAGMA table_info(Usuarios)')}:
            con.execute('ALTER TABLE Usuarios ADD COLUMN TelefoneContato TEXT')
        con.execute('CREATE INDEX IF NOT EXISTS idx_conversas_telefone ON Conversas(Telefone, Status, ID)')


def conversation(con, cid, phone):
    row = con.execute('SELECT * FROM Conversas WHERE ID=? AND Telefone=?', (cid, phone)).fetchone()
    if not row:
        raise DatabaseError(404, 'Conversa não encontrada para este telefone')
    return row


def create_conversation(phone, name):
    with db() as con:
        con.execute('INSERT INTO Usuarios(Telefone,Nome) VALUES (?,?) ON CONFLICT(Telefone) DO UPDATE SET Nome=CASE WHEN excluded.Nome != \'\' THEN excluded.Nome ELSE Usuarios.Nome END', (phone, name))
        cid = con.execute('INSERT INTO Conversas(Telefone) VALUES (?)', (phone,)).lastrowid
    return {'conversa_id': cid, 'telefone': phone}


def history(cid, phone):
    with db() as con:
        row = conversation(con, cid, phone)
        messages = con.execute('SELECT ID,Texto,Horario,ResponsavelEnvio FROM Mensagens WHERE ConversaID=? ORDER BY ID', (cid,)).fetchall()
        pending = con.execute("SELECT ID FROM Mensagens m WHERE ConversaID=? AND ResponsavelEnvio='cliente' AND NOT EXISTS (SELECT 1 FROM Mensagens r WHERE r.EmRespostaA=m.ID) ORDER BY ID LIMIT 1", (cid,)).fetchone()
    return {'conversa_id': cid, 'status': row['Status'], 'dados': json.loads(row['Dados']), 'mensagens': [dict(m) for m in messages], 'mensagem_pendente_id': pending['ID'] if pending else None}


def save_message(cid, phone, text):
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = conversation(con, cid, phone)
        if row['Status'] != 'ativa':
            raise DatabaseError(409, 'Conversa encerrada. Inicie outra conversa.')
        if row['LockAte'] > time.time():
            raise DatabaseError(409, 'Conversa em processamento; tente novamente')
        mid = con.execute("INSERT INTO Mensagens(ConversaID,Texto,ResponsavelEnvio) VALUES (?,?,'cliente')", (cid, text)).lastrowid
    return {'mensagem_id': mid}


def begin_response(cid, phone, message_id, token):
    """Retorna (conversa, histórico, resposta em cache) e reserva o turno se necessário.

    O histórico vem em ordem decrescente de ID. A conexão é fechada antes da IA.
    Ao adquirir o bloqueio, o chamador deve usar release_response em finally.
    """
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        row = conversation(con, cid, phone)
        cached = con.execute('SELECT Resultado FROM Mensagens WHERE ConversaID=? AND EmRespostaA=?', (cid, message_id)).fetchone()
        if cached:
            return None, [], json.loads(cached['Resultado'])
        pending = con.execute("SELECT ID FROM Mensagens m WHERE ConversaID=? AND ResponsavelEnvio='cliente' AND NOT EXISTS (SELECT 1 FROM Mensagens r WHERE r.EmRespostaA=m.ID) ORDER BY ID LIMIT 1", (cid,)).fetchone()
        if not pending or pending['ID'] != message_id:
            raise DatabaseError(409, 'Responda às mensagens pendentes em ordem; mensagem_id inválida ou fora de ordem')
        if row['Status'] != 'ativa' or row['LockAte'] > time.time():
            raise DatabaseError(409, 'Conversa encerrada ou em processamento')
        con.execute('UPDATE Conversas SET LockToken=?,LockAte=? WHERE ID=?', (token, time.time() + 300, cid))
        records = con.execute('SELECT Texto,ResponsavelEnvio FROM Mensagens WHERE ConversaID=? AND ID<=? ORDER BY ID DESC LIMIT 40', (cid, message_id)).fetchall()
    return dict(row), [dict(record) for record in records], None


def finish_response(cid, phone, message_id, token, current, complete, offered, result):
    """Salva cadastro, estado e resposta atomicamente, validando a reserva do turno."""
    reply = result['resposta']
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        latest = conversation(con, cid, phone)
        if latest['LockToken'] != token or latest['LockAte'] < time.time():
            raise DatabaseError(409, 'Processamento expirou; tente novamente')
        con.execute('UPDATE Usuarios SET Nome=COALESCE(?,Nome),TelefoneContato=COALESCE(?,TelefoneContato) WHERE Telefone=?',
                    (current.get('nome_contato'), current.get('telefone_contato'), phone))
        if complete:
            con.execute('''INSERT INTO Interessados(Telefone,ConversaID,Estado,Bairro,Metragem,Banheiros,Quartos,ValorMaximo,Vagas,TipoNegocio,TipoImovel,Urgencia)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(Telefone) DO UPDATE SET
              ConversaID=excluded.ConversaID,Estado=excluded.Estado,Bairro=excluded.Bairro,Metragem=excluded.Metragem,
              Banheiros=excluded.Banheiros,Quartos=excluded.Quartos,ValorMaximo=excluded.ValorMaximo,Vagas=excluded.Vagas,
              TipoNegocio=excluded.TipoNegocio,TipoImovel=excluded.TipoImovel,Urgencia=excluded.Urgencia,AtualizadoEm=CURRENT_TIMESTAMP''',
              (phone, cid, *[current.get(k) for k in ['estado','bairro','metragem','banheiros','quartos','valor_maximo','vagas','tipo_negocio','tipo_imovel','urgencia']]))
        serialized = json.dumps(current, ensure_ascii=False)
        con.execute('UPDATE Conversas SET Dados=?,Resumo=?,Status=?,OpcionaisOferecidos=?,AguardandoConfirmacao=?,LockToken=NULL,LockAte=0 WHERE ID=?',
                    (serialized, serialized, result['status'], offered, result['aguardando_confirmacao'], cid))
        con.execute("INSERT INTO Mensagens(ConversaID,Texto,ResponsavelEnvio,EmRespostaA,Resultado) VALUES (?,?,'bot',?,?)",
                    (cid, reply, message_id, json.dumps(result, ensure_ascii=False)))


def release_response(cid, token):
    """Libera apenas a reserva do chamador, preservando eventual reserva posterior."""
    with db() as con:
        con.execute('UPDATE Conversas SET LockToken=NULL,LockAte=0 WHERE ID=? AND LockToken=?', (cid, token))


def waiting_resume(phone):
    with db() as con:
        row = con.execute("SELECT AguardandoRetomada FROM Conversas WHERE Telefone=? AND Status='ativa' ORDER BY ID DESC LIMIT 1", (phone,)).fetchone()
        return bool(row and row[0])


def resume_prompt(con, row):
    labels = {'estado':'Estado', 'bairro':'Bairro', 'tipo_negocio':'Negócio', 'tipo_imovel':'Imóvel',
              'urgencia':'Urgência', 'metragem':'Metragem', 'banheiros':'Banheiros', 'quartos':'Quartos',
              'valor_maximo':'Valor máximo', 'vagas':'Vagas'}
    data = json.loads(row['Dados'])
    summary = '; '.join(f'{label}: {data[key]}' for key, label in labels.items() if data.get(key) is not None)
    if not summary:
        last = con.execute("SELECT Texto FROM Mensagens WHERE ConversaID=? AND ResponsavelEnvio='cliente' ORDER BY ID DESC LIMIT 1", (row['ID'],)).fetchone()
        summary = 'Ainda não registramos preferências.' if not last else 'Sua última solicitação: ' + last['Texto'][:400]
    return f'Seu atendimento anterior está em aberto. Resumo: {summary}\nDeseja continuar o atendimento anterior ou iniciar um novo? Responda “continuar” ou “novo”.'


def receive_whatsapp(phone, text, option=None, inferred_option=None):
    """Salva a entrada e resolve a conversa por telefone em uma única transação.

    Cada chamada salva uma nova mensagem, mesmo quando o texto é igual.
    Retorna os IDs internos e a resposta de retomada, quando necessária.
    """
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        con.execute('INSERT INTO Usuarios(Telefone) VALUES (?) ON CONFLICT(Telefone) DO NOTHING', (phone,))
        row = con.execute("SELECT * FROM Conversas WHERE Telefone=? AND Status='ativa' ORDER BY ID DESC LIMIT 1", (phone,)).fetchone()
        prompt = None
        if row:
            if row['LockAte'] > time.time():
                raise DatabaseError(409, 'Atendimento em processamento; repita esta chamada depois')
            pending = con.execute("SELECT ID FROM Mensagens m WHERE ConversaID=? AND ResponsavelEnvio='cliente' AND NOT EXISTS (SELECT 1 FROM Mensagens r WHERE r.EmRespostaA=m.ID) LIMIT 1", (row['ID'],)).fetchone()
            if pending:
                raise DatabaseError(409, f"Há mensagem pendente; chame /api/agente/responder com conversa_id={row['ID']} e mensagem_id={pending['ID']}")
            # Uma conversa criada sem mensagens ainda não é um atendimento anterior.
            # Sem histórico, MAX(Horario) e age são NULL, independentemente de DataInicio.
            age = con.execute("SELECT (julianday('now') - julianday(MAX(Horario))) * 24 FROM Mensagens WHERE ConversaID=?", (row['ID'],)).fetchone()[0]
            if age is None and row['AguardandoRetomada']:
                con.execute('UPDATE Conversas SET AguardandoRetomada=0 WHERE ID=?', (row['ID'],))
                row = dict(row)
                row['AguardandoRetomada'] = 0
            if row['AguardandoRetomada']:
                choice = option or inferred_option
                if choice == 'novo':
                    con.execute("UPDATE Conversas SET Status='encerrada',AguardandoRetomada=0 WHERE ID=?", (row['ID'],))
                    row = None
                elif choice == 'continuar':
                    con.execute('UPDATE Conversas SET AguardandoRetomada=0 WHERE ID=?', (row['ID'],))
                else:
                    prompt = resume_prompt(con, row)
            elif age is not None and age > 24:
                prompt = resume_prompt(con, row)
                con.execute('UPDATE Conversas SET AguardandoRetomada=1 WHERE ID=?', (row['ID'],))
        if row is None:
            cid = con.execute('INSERT INTO Conversas(Telefone) VALUES (?)', (phone,)).lastrowid
        else:
            cid = row['ID']
        mid = con.execute("INSERT INTO Mensagens(ConversaID,Texto,ResponsavelEnvio) VALUES (?,?,'cliente')", (cid, text)).lastrowid
        result = None
        if prompt:
            result = {'conversa_id':cid, 'mensagem_id':mid, 'resposta':prompt, 'status':'ativa',
                      'aguardando_retomada':True, 'aguardando_confirmacao':False, 'dados':json.loads(row['Dados'])}
            con.execute("INSERT INTO Mensagens(ConversaID,Texto,ResponsavelEnvio,EmRespostaA,Resultado) VALUES (?,?,'bot',?,?)", (cid, prompt, mid, json.dumps(result, ensure_ascii=False)))
        return cid, mid, result
