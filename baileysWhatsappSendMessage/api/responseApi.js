import { URL_API_RESPOSTA, AGENTE_API_KEY } from '../config/config.js'


export async function gerarResposta(
    numero,
    mensagem
) {
    try {

        const resposta = await fetch(
            URL_API_RESPOSTA,
            {
                method: 'POST',

                headers: {
                    'Content-Type': 'application/json',
                'X-API-Key': AGENTE_API_KEY
                },

                body: JSON.stringify({
                    telefone: "+" + numero,
                    texto: mensagem,
                opcao_atendimento: null
                })
            }
        )


        if (resposta.status !== 200) {

            console.error(
                `[API] Erro HTTP. Status: ${resposta.status}`
            )

            return null
        }


        const dados = await resposta.json()


        console.log(
            '[API] Request realizado com sucesso. Status: 200'
        )


        if (
            !dados?.resposta ||
            !String(dados.resposta).trim()
        ) {

            console.log(
                '[API] Request retornou 200, mas a resposta está vazia.'
            )

            return null
        }


        return dados.resposta


    } catch (erro) {

        console.error(
            '[API] Erro ao realizar request:',
            erro
        )

        return null
    }
}