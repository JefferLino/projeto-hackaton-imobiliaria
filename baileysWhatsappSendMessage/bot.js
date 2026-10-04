import express from 'express'

import {
    PORTA_API
} from './config/config.js'

import {
    conectarWhatsApp,
    getSocket,
    isWhatsAppConectado
} from './whatsapp/connection.js'

import {
    configurarMensagens
} from './whatsapp/messages.js'

import {
    normalizarTelefone
} from './utils/phone.js'


const app = express()

app.use(
    express.json()
)


/*
 * Status
 */

app.get(
    '/status',
    (req, res) => {

        res.json({
            sucesso: true,
            whatsapp_conectado:
                isWhatsAppConectado()
        })
    }
)


/*
 * Enviar mensagem
 */

app.post(
    '/enviar-mensagem',
    async (req, res) => {

        try {

            const {
                telefone,
                mensagem
            } = req.body


            if (!telefone) {

                return res.status(400).json({
                    sucesso: false,
                    erro: 'O campo telefone é obrigatório.'
                })
            }


            if (!mensagem) {

                return res.status(400).json({
                    sucesso: false,
                    erro: 'O campo mensagem é obrigatório.'
                })
            }


            if (!isWhatsAppConectado()) {

                return res.status(503).json({
                    sucesso: false,
                    erro: 'WhatsApp não está conectado.'
                })
            }


            const numero =
                normalizarTelefone(telefone)


            const sock =
                getSocket()


            const contatos =
                await sock.onWhatsApp(numero)


            if (
                !contatos ||
                contatos.length === 0
            ) {

                return res.status(404).json({
                    sucesso: false,
                    erro: 'Número não encontrado no WhatsApp.'
                })
            }


            const contato =
                contatos[0]


            if (!contato.exists) {

                return res.status(404).json({
                    sucesso: false,
                    erro: 'Número não possui WhatsApp.'
                })
            }


            const resultado =
                await sock.sendMessage(
                    contato.jid,
                    {
                        text: mensagem
                    }
                )


            return res.json({
                sucesso: true,
                id: resultado?.key?.id || null
            })


        } catch (erro) {

            console.error(
                '[API] Erro:',
                erro
            )


            return res.status(500).json({
                sucesso: false,
                erro: erro.message
            })
        }
    }
)


/*
 * Inicializa API
 */

app.listen(
    PORTA_API,
    () => {

        console.log(
            `[API] Rodando na porta ${PORTA_API}`
        )
    }
)


/*
 * Inicializa WhatsApp
 */

await conectarWhatsApp(configurarMensagens)