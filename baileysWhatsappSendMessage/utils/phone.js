export function normalizarTelefone(telefone) {

    if (!telefone) {
        return null
    }

    const numero =
        String(telefone).replace(/\D/g, '')

    return numero || null
}


export function telefoneParaJid(telefone) {

    const numero =
        normalizarTelefone(telefone)

    if (!numero) {
        return null
    }

    return `${numero}@s.whatsapp.net`
}