"""Configuracao do agente. Reinicie a API apos alterar este arquivo."""

# API receptora dos lembretes de retomada.
FOLLOWUP_URL = 'http://localhost:3000/enviar-mensagem'

# Bot Baileys responsavel pelo envio real de mensagens no WhatsApp.
WHATSAPP_BOT_URL = 'http://127.0.0.1:3000'
