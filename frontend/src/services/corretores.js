const BASE = '/api/corretores'

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (res.status === 204) return null
  const data = await res.json()
  if (!res.ok) throw data
  return data
}

export function listarCorretores() {
  return request(BASE)
}

export function criarCorretor(data) {
  return request(BASE, { method: 'POST', body: JSON.stringify(data) })
}

export function buscarCorretor(id) {
  return request(`${BASE}/${id}`)
}

export function atualizarCorretor(id, data) {
  return request(`${BASE}/${id}`, { method: 'PUT', body: JSON.stringify(data) })
}

export function deletarCorretor(id) {
  return request(`${BASE}/${id}`, { method: 'DELETE' })
}
