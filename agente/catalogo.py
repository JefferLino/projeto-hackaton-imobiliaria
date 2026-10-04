"""Busca imóveis aderentes ao perfil do lead no catálogo simulado.

A tabela Imoveis pertence à API de corretores; aqui ela é apenas lida.
"""
import unicodedata

import database

UFS = {
    'acre': 'ac', 'alagoas': 'al', 'amapa': 'ap', 'amazonas': 'am', 'bahia': 'ba', 'ceara': 'ce',
    'distrito federal': 'df', 'espirito santo': 'es', 'goias': 'go', 'maranhao': 'ma',
    'mato grosso': 'mt', 'mato grosso do sul': 'ms', 'minas gerais': 'mg', 'para': 'pa',
    'paraiba': 'pb', 'parana': 'pr', 'pernambuco': 'pe', 'piaui': 'pi', 'rio de janeiro': 'rj',
    'rio grande do norte': 'rn', 'rio grande do sul': 'rs', 'rondonia': 'ro', 'roraima': 'rr',
    'santa catarina': 'sc', 'sao paulo': 'sp', 'sergipe': 'se', 'tocantins': 'to',
}


def _normalizar(texto):
    sem_acento = unicodedata.normalize('NFKD', str(texto or '')).encode('ascii', 'ignore').decode()
    return ' '.join(sem_acento.lower().split())


def _uf(estado):
    nome = _normalizar(estado)
    return UFS.get(nome, nome)


def sugerir(prefs, limite=3):
    """Retorna imóveis disponíveis do mesmo estado, priorizando o bairro de interesse."""
    if not prefs.get('tipo_negocio') or not prefs.get('estado'):
        return []
    investimento = prefs['tipo_negocio'] == 'investimento'
    filtros = ["status='disponivel'", 'tipo_negocio=?']
    params = ['compra' if investimento else prefs['tipo_negocio']]
    if prefs.get('tipo_imovel'):
        filtros.append('tipo_imovel=?')
        params.append(prefs['tipo_imovel'])
    orcamento = prefs.get('ticket_investimento') if investimento else prefs.get('valor_maximo')
    if orcamento:
        filtros.append('valor<=?')
        params.append(orcamento)
    for campo in ('quartos', 'banheiros', 'vagas', 'metragem'):
        if prefs.get(campo):
            filtros.append(f'COALESCE({campo},0)>=?')
            params.append(prefs[campo])
    with database.db() as con:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='Imoveis'").fetchone():
            return []
        rows = con.execute('SELECT id,titulo,tipo_negocio,tipo_imovel,estado,bairro,metragem,quartos,'
                           f'banheiros,vagas,valor FROM Imoveis WHERE {" AND ".join(filtros)} ORDER BY valor',
                           params).fetchall()
    uf, bairro = _uf(prefs['estado']), _normalizar(prefs.get('bairro'))
    mesmos_estado = [dict(r) for r in rows if _uf(r['estado']) == uf]
    mesmos_estado.sort(key=lambda r: not bairro or _normalizar(r['bairro']) != bairro)
    return mesmos_estado[:limite]


def _moeda(valor):
    return 'R$ ' + f'{valor:,.0f}'.replace(',', '.')


def formatar(imoveis, prefs):
    if not imoveis:
        return ('No momento não encontrei imóveis disponíveis na nossa base com esse perfil, '
                'mas o consultor vai buscar opções para você.')
    investimento = prefs.get('tipo_negocio') == 'investimento'
    linhas = ['Oportunidades da nossa base dentro do seu ticket:' if investimento
              else 'Encontrei estas opções na nossa base que combinam com o que você procura:']
    for i, imovel in enumerate(imoveis, 1):
        detalhes = [_moeda(imovel['valor']) + ('/mês' if imovel['tipo_negocio'] == 'aluguel' else '')]
        if imovel['metragem']:
            detalhes.append(f"{imovel['metragem']:g} m²")
        if imovel['quartos']:
            detalhes.append(f"{imovel['quartos']} quarto{'s' if imovel['quartos'] > 1 else ''}")
        linhas.append(f"{i}. {imovel['titulo']} ({imovel['bairro']}) — {' · '.join(detalhes)}")
    return '\n'.join(linhas)
