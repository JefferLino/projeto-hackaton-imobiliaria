"""Teste manual real: python smoke_ollama.py (requer Ollama e modelo)."""
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import app
import database


if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as folder:
        database.DB_PATH = str(Path(folder) / 'smoke.sqlite3')
        with TestClient(app.app) as client:
            phone = '5511999999999'
            for number, text in enumerate([
                'Estou procurando apartamento na zona sul.',
                'Quero comprar em SP, no bairro Moema. Urgência alta. Pode pular todos os campos opcionais.',
                'Meu nome é Ana Silva e meu telefone para contato é 11988887777.',
                'Pode encerrar a conversa.',
            ]):
                result = client.post('/api/whatsapp/mensagens', json={
                    'telefone': phone, 'texto': text})
                print(result.status_code, result.text, flush=True)
                assert result.status_code == 200
                if number == 0:
                    assert result.json()['dados'].get('tipo_imovel') == 'apartamento'
                    assert 'bairro' in result.json()['campos_obrigatorios_pendentes']
                elif number == 1:
                    assert result.json()['status'] == 'ativa'
                    assert result.json()['aguardando_confirmacao'] is False
                    assert 'telefone_contato' in result.json()['campos_obrigatorios_pendentes']
                elif number == 2:
                    assert result.json()['aguardando_confirmacao'] is True
                else:
                    assert result.json()['status'] == 'encerrada'
