"""Envia mensagens ao bot Baileys para entrega real no WhatsApp."""
import httpx
import config


def enviar(telefone, mensagem):
    with httpx.Client(timeout=10, trust_env=False, follow_redirects=False) as client:
        response = client.post(f'{config.WHATSAPP_BOT_URL}/enviar-mensagem',
                               json={'telefone': telefone, 'mensagem': mensagem})
        response.raise_for_status()
