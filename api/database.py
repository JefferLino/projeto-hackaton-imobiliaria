"""Persistência: esquema e conexão SQLite para o CRUD de Corretores.

Não depende de FastAPI nem de services/. Compartilha o mesmo arquivo SQLite
do agente, mas só gerencia a tabela Corretores.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_configured_path = Path(os.getenv('DATABASE_PATH') or 'database/imobiliaria.sqlite3').expanduser()
DB_PATH = str(_configured_path if _configured_path.is_absolute() else PROJECT_ROOT / _configured_path)


@contextmanager
def db():
    """Abre conexão WAL, confirma ou desfaz, sempre fecha."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
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
    """Cria as tabelas de Corretores, Atribuições e Imóveis se não existirem. Idempotente."""
    with db() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS Corretores (
          id            INTEGER PRIMARY KEY AUTOINCREMENT,
          nome          TEXT    NOT NULL,
          email         TEXT    NOT NULL UNIQUE,
          telefone      TEXT    NOT NULL,
          senha_hash    TEXT    NOT NULL,
          criado_em     TEXT    DEFAULT CURRENT_TIMESTAMP,
          atualizado_em TEXT    DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS AtribuicoesConversa (
          ConversaID    INTEGER PRIMARY KEY,
          CorretorID    INTEGER REFERENCES Corretores(id),
          Etapa         TEXT CHECK(Etapa IN ('novo','qualificando','qualificado','agendado','fechado','perdido')),
          AtualizadoEm  TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS Imoveis (
          id            INTEGER PRIMARY KEY AUTOINCREMENT,
          titulo        TEXT    NOT NULL,
          tipo_negocio  TEXT    NOT NULL CHECK(tipo_negocio IN ('compra','aluguel')),
          tipo_imovel   TEXT    NOT NULL CHECK(tipo_imovel IN ('casa','apartamento','comercial')),
          estado        TEXT    NOT NULL,
          bairro        TEXT    NOT NULL,
          endereco      TEXT,
          metragem      REAL,
          quartos       INTEGER,
          banheiros     INTEGER,
          vagas         INTEGER,
          valor         REAL    NOT NULL,
          status        TEXT    NOT NULL DEFAULT 'disponivel' CHECK(status IN ('disponivel','reservado','vendido','alugado')),
          criado_em     TEXT    DEFAULT CURRENT_TIMESTAMP,
          atualizado_em TEXT    DEFAULT CURRENT_TIMESTAMP
        );
        ''')
