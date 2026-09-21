"""Lógica de negócio do pipeline de leads (conversas do agente).

Recebe conexões abertas pelo app.py. Só faz SELECT nas tabelas do agente
(Usuarios, Conversas) — nunca escreve nelas. A atribuição de corretor e a
etapa manual do funil ficam isoladas em AtribuicoesConversa.
"""
import json

from fastapi import HTTPException

ETAPAS = ('novo', 'qualificando', 'qualificado', 'agendado', 'fechado', 'perdido')


def _etapa_sugerida(row) -> str:
    """Deriva a etapa a partir do estado do agente quando não há override manual."""
    if row['Status'] == 'encerrada':
        return 'fechado'
    if row['AguardandoConfirmacao']:
        return 'qualificado'
    if json.loads(row['Dados'] or '{}'):
        return 'qualificando'
    return 'novo'


def _to_dict(row) -> dict:
    etapa = row['EtapaManual'] or _etapa_sugerida(row)
    return {
        'conversa_id': row['conversa_id'],
        'telefone': row['Telefone'],
        'nome': row['Nome'],
        'status': row['Status'],
        'etapa': etapa,
        'corretor_id': row['CorretorID'],
        'corretor_nome': row['CorretorNome'],
        'resumo': row['Resumo'],
        'dados': json.loads(row['Dados'] or '{}'),
        'atualizado_em': row['AtualizadoEm'],
    }


def _tabela_conversas_existe(con) -> bool:
    """Conversas pertence ao esquema do agente e pode não existir se ele nunca rodou ainda."""
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='Conversas'"
    ).fetchone() is not None


def list_leads(con, etapa: str | None = None, corretor_id: int | None = None) -> list[dict]:
    if not _tabela_conversas_existe(con):
        return []
    rows = con.execute('''
        SELECT c.ID as conversa_id, c.Telefone, u.Nome, c.Status, c.AguardandoConfirmacao,
               c.Dados, c.Resumo, a.Etapa as EtapaManual, a.CorretorID, a.AtualizadoEm, cor.nome as CorretorNome
        FROM Conversas c
        JOIN Usuarios u ON u.Telefone = c.Telefone
        LEFT JOIN AtribuicoesConversa a ON a.ConversaID = c.ID
        LEFT JOIN Corretores cor ON cor.id = a.CorretorID
        ORDER BY c.ID DESC
    ''').fetchall()
    leads = [_to_dict(r) for r in rows]
    if etapa is not None:
        leads = [lead for lead in leads if lead['etapa'] == etapa]
    if corretor_id is not None:
        leads = [lead for lead in leads if lead['corretor_id'] == corretor_id]
    return leads


def update_lead(con, conversa_id: int, etapa: str | None = None, corretor_id: int | None = None) -> dict:
    if not _tabela_conversas_existe(con) or not con.execute(
        'SELECT 1 FROM Conversas WHERE ID=?', (conversa_id,)
    ).fetchone():
        raise HTTPException(status_code=404, detail='Conversa não encontrada')
    if corretor_id is not None and not con.execute('SELECT 1 FROM Corretores WHERE id=?', (corretor_id,)).fetchone():
        raise HTTPException(status_code=404, detail='Corretor não encontrado')

    con.execute('''
        INSERT INTO AtribuicoesConversa (ConversaID, CorretorID, Etapa) VALUES (?, ?, ?)
        ON CONFLICT(ConversaID) DO UPDATE SET
          CorretorID   = COALESCE(excluded.CorretorID, AtribuicoesConversa.CorretorID),
          Etapa        = COALESCE(excluded.Etapa, AtribuicoesConversa.Etapa),
          AtualizadoEm = CURRENT_TIMESTAMP
    ''', (conversa_id, corretor_id, etapa))

    row = con.execute('''
        SELECT c.ID as conversa_id, c.Telefone, u.Nome, c.Status, c.AguardandoConfirmacao,
               c.Dados, c.Resumo, a.Etapa as EtapaManual, a.CorretorID, a.AtualizadoEm, cor.nome as CorretorNome
        FROM Conversas c
        JOIN Usuarios u ON u.Telefone = c.Telefone
        LEFT JOIN AtribuicoesConversa a ON a.ConversaID = c.ID
        LEFT JOIN Corretores cor ON cor.id = a.CorretorID
        WHERE c.ID = ?
    ''', (conversa_id,)).fetchone()
    return _to_dict(row)
