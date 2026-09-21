const BASE = '/api/leads'

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

export function listarLeads(params = {}) {
  const query = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
  ).toString()
  return request(query ? `${BASE}?${query}` : BASE)
}

export function atualizarLead(conversaId, data) {
  return request(`${BASE}/${conversaId}`, { method: 'PATCH', body: JSON.stringify(data) })
}
