import { URL_API_RESPOSTA } from '../config/config.js'


export async function gerarResposta(
    numero,
    mensagem
) {

    const resposta = await fetch(
        URL_API_RESPOSTA,
        {
            method: 'POST',

            headers: {
                'Content-Type': 'application/json'
            },

            body: JSON.stringify({
                telefone: "+" + numero,
                texto: mensagem, 
                opcao_atendimento: ''
            })
        }
    )


    if (!resposta.ok) {

        throw new Error(
            `API respondeu com status ${resposta.status}`
        )
    }


    const dados =
        await resposta.json()


    return dados.resposta
}