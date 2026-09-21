const BASE = '/api/imoveis'

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

export function listarImoveis() {
  return request(BASE)
}

export function criarImovel(data) {
  return request(BASE, { method: 'POST', body: JSON.stringify(data) })
}

export function buscarImovel(id) {
  return request(`${BASE}/${id}`)
}

export function atualizarImovel(id, data) {
  return request(`${BASE}/${id}`, { method: 'PUT', body: JSON.stringify(data) })
}

export function deletarImovel(id) {
  return request(`${BASE}/${id}`, { method: 'DELETE' })
}
