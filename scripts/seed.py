"""Seed de dados para testes manuais locais.

Cria corretores e leads (conversas simuladas) no banco compartilhado
(database/imobiliaria.sqlite3), sem depender do Ollama nem do WhatsApp.
Idempotente: pode rodar várias vezes sem duplicar dados.

Não faz parte de agente/ nem de api/ — é só uma ferramenta de dev que
reaproveita as funções públicas dos dois módulos (eles continuam sem se
importar mutuamente entre si).

Uso (precisa do venv de api/, que tem fastapi e bcrypt):
    api/.venv/bin/python scripts/seed.py
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


agente_db = _load('agente_db', ROOT / 'agente' / 'database.py')
api_db = _load('api_db', ROOT / 'api' / 'database.py')
corretores_svc = _load('corretores_svc', ROOT / 'api' / 'services' / 'corretores.py')
leads_svc = _load('leads_svc', ROOT / 'api' / 'services' / 'leads.py')
imoveis_svc = _load('imoveis_svc', ROOT / 'api' / 'services' / 'imoveis.py')

CORRETORES = [
    {'nome': 'Ana Souza', 'email': 'ana@imobiliaria.com', 'telefone': '11987654321', 'senha': 'senha1234'},
    {'nome': 'Bruno Lima', 'email': 'bruno@imobiliaria.com', 'telefone': '11911112222', 'senha': 'senha1234'},
]

LEADS = [
    {'telefone': '11999990001', 'nome': 'Carla Mendes', 'mensagem': 'Estou procurando apartamento na zona sul, 2 quartos.'},
    {'telefone': '11999990002', 'nome': 'Diego Alves', 'mensagem': 'Quero investir em imóveis para renda.'},
    {'telefone': '11999990003', 'nome': 'Fernanda Rocha', 'mensagem': 'Procuro casa para alugar com 3 quartos.'},
]

IMOVEIS = [
    {'titulo': 'Apartamento 2 quartos em Moema', 'tipo_negocio': 'compra', 'tipo_imovel': 'apartamento',
     'estado': 'SP', 'bairro': 'Moema', 'metragem': 65, 'quartos': 2, 'banheiros': 1, 'vagas': 1, 'valor': 650000},
    {'titulo': 'Casa 3 quartos em Alphaville', 'tipo_negocio': 'aluguel', 'tipo_imovel': 'casa',
     'estado': 'SP', 'bairro': 'Alphaville', 'metragem': 180, 'quartos': 3, 'banheiros': 3, 'vagas': 2, 'valor': 6500},
    {'titulo': 'Sala comercial no Centro', 'tipo_negocio': 'aluguel', 'tipo_imovel': 'comercial',
     'estado': 'SP', 'bairro': 'Centro', 'metragem': 40, 'valor': 3200},
]


def seed_corretores():
    ids = {}
    with api_db.db() as con:
        for c in CORRETORES:
            existing = con.execute('SELECT id FROM Corretores WHERE email=?', (c['email'],)).fetchone()
            if existing:
                print(f"  já existe: {c['email']}")
                ids[c['email']] = existing['id']
                continue
            criado = corretores_svc.create_corretor(con, c)
            print(f"  criado: {c['email']} (senha: {c['senha']})")
            ids[c['email']] = criado['id']
    return ids


def seed_leads():
    conversa_ids = {}
    for lead in LEADS:
        with agente_db.db() as con:
            existing = con.execute('SELECT ID FROM Conversas WHERE Telefone=?', (lead['telefone'],)).fetchone()
        if existing:
            print(f"  já existe: {lead['nome']} ({lead['telefone']})")
            conversa_ids[lead['telefone']] = existing['ID']
            continue
        criada = agente_db.create_conversation(lead['telefone'], lead['nome'])
        agente_db.save_message(criada['conversa_id'], lead['telefone'], lead['mensagem'])
        print(f"  criado: {lead['nome']} ({lead['telefone']})")
        conversa_ids[lead['telefone']] = criada['conversa_id']
    return conversa_ids


def seed_atribuicoes(corretor_ids, conversa_ids):
    ana_id = corretor_ids.get('ana@imobiliaria.com')
    with api_db.db() as con:
        cid = conversa_ids.get('11999990001')
        if cid:
            leads_svc.update_lead(con, cid, etapa='qualificando', corretor_id=ana_id)
            print('  Carla Mendes -> qualificando, atribuída à Ana Souza')
        cid = conversa_ids.get('11999990002')
        if cid:
            leads_svc.update_lead(con, cid, etapa='agendado', corretor_id=ana_id)
            print('  Diego Alves -> agendado, atribuído à Ana Souza')
    print('  Fernanda Rocha fica em "novo", sem responsável (estado inicial)')


def seed_imoveis():
    with api_db.db() as con:
        existentes = {r['titulo'] for r in con.execute('SELECT titulo FROM Imoveis').fetchall()}
        for imovel in IMOVEIS:
            if imovel['titulo'] in existentes:
                print(f"  já existe: {imovel['titulo']}")
                continue
            imoveis_svc.create_imovel(con, imovel)
            print(f"  criado: {imovel['titulo']}")


def main():
    print('Inicializando esquemas...')
    agente_db.init_db()
    api_db.init_db()

    print('\nCorretores:')
    corretor_ids = seed_corretores()

    print('\nLeads (conversas simuladas):')
    conversa_ids = seed_leads()

    print('\nAtribuições de exemplo no pipeline:')
    seed_atribuicoes(corretor_ids, conversa_ids)

    print('\nImóveis:')
    seed_imoveis()

    print(f'\nPronto! Banco em: {api_db.DB_PATH}')
    print('Login de teste -> email: ana@imobiliaria.com | senha: senha1234')


if __name__ == '__main__':
    main()
