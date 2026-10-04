const CAMPOS_RESUMO = [
  ['tipo_negocio', 'Negócio'],
  ['tipo_imovel', 'Imóvel'],
  ['bairro', 'Bairro'],
  ['valor_maximo', 'Valor máx.'],
  ['objetivo_investimento', 'Objetivo'],
  ['ticket_investimento', 'Ticket'],
  ['expectativa_retorno', 'Retorno esperado'],
]

export function resumoPreferencias(dados) {
  const partes = CAMPOS_RESUMO
    .filter(([campo]) => dados?.[campo] != null)
    .map(([campo, rotulo]) => `${rotulo}: ${dados[campo]}`)
  return partes.length ? partes.join(' · ') : 'Sem preferências coletadas ainda.'
}
