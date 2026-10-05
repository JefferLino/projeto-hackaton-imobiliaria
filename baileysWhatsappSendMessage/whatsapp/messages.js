import {
    NUMERO_TESTE
} from '../config/config.js'

import {
    normalizarTelefone
} from '../utils/phone.js'

import {
    gerarResposta
} from '../api/responseApi.js'


export function configurarMensagens(sock) {

    sock.ev.on(
        'messages.upsert',
        async ({ messages, type }) => {

            if (type !== 'notify') {
                return
            }

            for (const mensagem of messages) {

                try {

                    if (mensagem.key.fromMe) {
                        continue
                    }

                    const remoteJid =
                        mensagem.key.remoteJid

                    if (!remoteJid) {
                        continue
                    }

                    if (remoteJid.endsWith('@g.us')) {
                        console.log(
                            '[IGNORADA] Mensagem de grupo.'
                        )

                        continue
                    }

                    let numeroRemetente = null

                    if (
                        remoteJid.endsWith(
                            '@s.whatsapp.net'
                        )
                    ) {
                        numeroRemetente =
                            normalizarTelefone(
                                remoteJid
                                    .split('@')[0]
                                    .split(':')[0]
                            )
                    }

                    if (
                        remoteJid.endsWith('@lid')
                    ) {

                        if (
                            mensagem.key.participantAlt
                        ) {
                            numeroRemetente =
                                normalizarTelefone(
                                    mensagem.key
                                        .participantAlt
                                        .split('@')[0]
                                        .split(':')[0]
                                )
                        }

                        if (
                            !numeroRemetente &&
                            mensagem.key.remoteJidAlt
                        ) {
                            numeroRemetente =
                                normalizarTelefone(
                                    mensagem.key
                                        .remoteJidAlt
                                        .split('@')[0]
                                        .split(':')[0]
                                )
                        }
                    }

                    console.log(
                        '[REMETENTE]:',
                        numeroRemetente
                    )

                    // Trecho de código comentado para permitir apenas mensagens de um número específico (NUMERO_TESTE). Se quiser habilitar, descomente o bloco abaixo.
                    // if (
                    //     numeroRemetente !== NUMERO_TESTE
                    // ) {
                    //     console.log(
                    //         '[IGNORADA] Número não autorizado.'
                    //     )

                    //     continue
                    // }

                    const texto =
                        mensagem.message?.conversation ||
                        mensagem.message?.extendedTextMessage?.text ||
                        mensagem.message?.imageMessage?.caption ||
                        mensagem.message?.videoMessage?.caption ||
                        ''

                    console.log(
                        '[MENSAGEM RECEBIDA]:',
                        texto
                    )

                    console.log(
                        '[BOT] Enviando mensagem para API...'
                    )

                    const resposta =
                        await gerarResposta(
                            numeroRemetente,
                            texto
                        )

                    console.log(
                        '[API] Resposta recebida:',
                        resposta
                    )

                    if (!resposta ||
                        !String(resposta).trim()) {

                        console.log(
                            '[BOT] API não retornou uma mensagem. Nada será enviado ao cliente.'
                        )

                        continue
                    }


                    await sock.sendMessage(
                        remoteJid,
                        {
                            text: resposta
                        }
                    )

                    console.log(
                        '[BOT] Resposta enviada.'
                    )

                } catch (erro) {

                    console.error(
                        '[MENSAGEM] Erro:',
                        erro
                    )
                }
            }
        }
    )
}