import makeWASocket, {
    useMultiFileAuthState,
    DisconnectReason
} from '@whiskeysockets/baileys'

import { Boom } from '@hapi/boom'
import qrcode from 'qrcode-terminal'
import fs from 'fs/promises'

import {
    PASTA_AUTH
} from '../config/config.js'


let sock = null
let whatsappConectado = false
let iniciandoConexao = false
let configurarSocket = null


export function getSocket() {
    return sock
}


export function isWhatsAppConectado() {
    return whatsappConectado
}


function esperar(ms) {
    return new Promise(
        resolve => setTimeout(resolve, ms)
    )
}


export async function conectarWhatsApp(configurar) {

    if (configurar) {
        configurarSocket = configurar
    }

    if (iniciandoConexao) {

        console.log(
            '[CONEXÃO] Já existe uma tentativa de conexão em andamento.'
        )

        return
    }


    iniciandoConexao = true
    whatsappConectado = false


    try {

        const {
            state,
            saveCreds
        } = await useMultiFileAuthState(
            PASTA_AUTH
        )


        sock = makeWASocket({
            auth: state,
            printQRInTerminal: false
        })


        sock.ev.on(
            'creds.update',
            saveCreds
        )

        // Cada reconexão (inclusive a que ocorre logo após ler o QR) cria um socket novo sem ouvintes.
        configurarSocket?.(sock)


        sock.ev.on(
            'connection.update',
            async (update) => {

                const {
                    connection,
                    lastDisconnect,
                    qr
                } = update


                if (qr) {

                    console.log(
                        '[WHATSAPP] Escaneie o QR Code:'
                    )

                    qrcode.generate(
                        qr,
                        {
                            small: true
                        }
                    )
                }


                if (connection === 'open') {

                    whatsappConectado = true
                    iniciandoConexao = false

                    console.log(
                        '[WHATSAPP] Conectado!'
                    )
                }


                if (connection === 'close') {

                    whatsappConectado = false
                    iniciandoConexao = false


                    const statusCode =
                        new Boom(
                            lastDisconnect?.error
                        )?.output?.statusCode


                    if (
                        statusCode ===
                            DisconnectReason.loggedOut ||
                        statusCode === 401
                    ) {

                        await fs.rm(
                            PASTA_AUTH,
                            {
                                recursive: true,
                                force: true
                            }
                        )

                        await esperar(1000)

                        await conectarWhatsApp()

                        return
                    }


                    await esperar(3000)

                    await conectarWhatsApp()
                }
            }
        )


    } catch (erro) {

        iniciandoConexao = false
        whatsappConectado = false

        console.error(
            '[WHATSAPP] Erro:',
            erro
        )

        await esperar(3000)

        await conectarWhatsApp()
    }

    return sock
}