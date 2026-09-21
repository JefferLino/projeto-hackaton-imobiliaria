"""Lógica de negócio do CRUD de Imóveis.

Recebe conexões abertas pelo app.py. Não importa FastAPI nem database.py
diretamente — mesmo padrão de services/corretores.py.
"""
from fastapi import HTTPException

CAMPOS = ['titulo', 'tipo_negocio', 'tipo_imovel', 'estado', 'bairro', 'endereco',
          'metragem', 'quartos', 'banheiros', 'vagas', 'valor', 'status']


def _row_to_dict(row) -> dict:
    return {k: row[k] for k in row.keys()}


def list_imoveis(con) -> list[dict]:
    rows = con.execute('SELECT * FROM Imoveis ORDER BY id DESC').fetchall()
    return [_row_to_dict(r) for r in rows]


def create_imovel(con, data: dict) -> dict:
    campos = [c for c in CAMPOS if c in data]
    cur = con.execute(
        f'INSERT INTO Imoveis ({", ".join(campos)}) VALUES ({", ".join("?" for _ in campos)})',
        [data[c] for c in campos],
    )
    return _row_to_dict(con.execute('SELECT * FROM Imoveis WHERE id = ?', (cur.lastrowid,)).fetchone())


def get_imovel(con, imovel_id: int) -> dict:
    row = con.execute('SELECT * FROM Imoveis WHERE id = ?', (imovel_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='Imóvel não encontrado')
    return _row_to_dict(row)


def update_imovel(con, imovel_id: int, data: dict) -> dict:
    existing = con.execute('SELECT id FROM Imoveis WHERE id = ?', (imovel_id,)).fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail='Imóvel não encontrado')

    campos = [c for c in CAMPOS if c in data]
    if campos:
        assignments = ', '.join(f'{c}=?' for c in campos)
        con.execute(
            f'UPDATE Imoveis SET {assignments}, atualizado_em=CURRENT_TIMESTAMP WHERE id=?',
            [data[c] for c in campos] + [imovel_id],
        )
    return _row_to_dict(con.execute('SELECT * FROM Imoveis WHERE id = ?', (imovel_id,)).fetchone())


def delete_imovel(con, imovel_id: int) -> None:
    cur = con.execute('DELETE FROM Imoveis WHERE id = ?', (imovel_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail='Imóvel não encontrado')
