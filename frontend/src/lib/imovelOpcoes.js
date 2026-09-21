export const TIPOS_NEGOCIO = [
  { valor: 'compra', rotulo: 'Compra' },
  { valor: 'aluguel', rotulo: 'Aluguel' },
]

export const TIPOS_IMOVEL = [
  { valor: 'casa', rotulo: 'Casa' },
  { valor: 'apartamento', rotulo: 'Apartamento' },
  { valor: 'comercial', rotulo: 'Comercial' },
]

export const STATUS_IMOVEL = [
  { valor: 'disponivel', rotulo: 'Disponível' },
  { valor: 'reservado', rotulo: 'Reservado' },
  { valor: 'vendido', rotulo: 'Vendido' },
  { valor: 'alugado', rotulo: 'Alugado' },
]

const ROTULOS = Object.fromEntries(
  [...TIPOS_NEGOCIO, ...TIPOS_IMOVEL, ...STATUS_IMOVEL].map(o => [o.valor, o.rotulo])
)

export function rotulo(valor) {
  return ROTULOS[valor] ?? valor
}
