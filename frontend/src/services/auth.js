export async function login(email, senha) {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, senha }),
  })
  const data = await res.json()
  if (!res.ok) throw data
  return data
}

export function logout() {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('auth_user')
}
