const BASE = '/agente/conversas'

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json()
  if (!res.ok) throw data
  return data
}

export function buscarHistorico(conversaId, telefone) {
  return request(`${BASE}/${conversaId}?telefone=${encodeURIComponent(telefone)}`)
}

export function enviarMensagemManual(conversaId, telefone, texto) {
  return request(`${BASE}/${conversaId}/assumir`, {
    method: 'POST',
    body: JSON.stringify({ telefone, texto }),
  })
}
