import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { STATUS_IMOVEL, TIPOS_IMOVEL, TIPOS_NEGOCIO } from '../lib/imovelOpcoes'
import { atualizarImovel, criarImovel } from '../services/imoveis'

const SELECT_CLASSES =
  'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'

function validate(fields) {
  const erros = {}
  if (!fields.titulo || fields.titulo.trim().length < 2) {
    erros.titulo = 'Título deve ter ao menos 2 caracteres'
  }
  if (!fields.estado || fields.estado.trim().length < 2) {
    erros.estado = 'Estado é obrigatório'
  }
  if (!fields.bairro || fields.bairro.trim().length < 2) {
    erros.bairro = 'Bairro é obrigatório'
  }
  if (!fields.valor || Number(fields.valor) <= 0) {
    erros.valor = 'Valor deve ser maior que zero'
  }
  if (fields.metragem && Number(fields.metragem) <= 0) {
    erros.metragem = 'Metragem deve ser maior que zero'
  }
  for (const campo of ['quartos', 'banheiros', 'vagas']) {
    if (fields[campo] && Number(fields[campo]) < 0) {
      erros[campo] = 'Não pode ser negativo'
    }
  }
  return erros
}

function paraNumeroOuNulo(valor) {
  return valor === '' || valor === undefined ? null : Number(valor)
}

export default function ImovelForm({ imovel, onSuccess, onCancel }) {
  const isEdit = Boolean(imovel)
  const [fields, setFields] = useState({
    titulo: imovel?.titulo ?? '',
    tipo_negocio: imovel?.tipo_negocio ?? 'compra',
    tipo_imovel: imovel?.tipo_imovel ?? 'apartamento',
    estado: imovel?.estado ?? '',
    bairro: imovel?.bairro ?? '',
    endereco: imovel?.endereco ?? '',
    metragem: imovel?.metragem ?? '',
    quartos: imovel?.quartos ?? '',
    banheiros: imovel?.banheiros ?? '',
    vagas: imovel?.vagas ?? '',
    valor: imovel?.valor ?? '',
    status: imovel?.status ?? 'disponivel',
  })
  const [erros, setErros] = useState({})
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    const { name, value } = e.target
    setFields(prev => ({ ...prev, [name]: value }))
    setErros(prev => ({ ...prev, [name]: undefined }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const err = validate(fields)
    if (Object.keys(err).length) {
      setErros(err)
      return
    }
    setLoading(true)
    try {
      const payload = {
        titulo: fields.titulo.trim(),
        tipo_negocio: fields.tipo_negocio,
        tipo_imovel: fields.tipo_imovel,
        estado: fields.estado.trim(),
        bairro: fields.bairro.trim(),
        endereco: fields.endereco.trim() || null,
        metragem: paraNumeroOuNulo(fields.metragem),
        quartos: paraNumeroOuNulo(fields.quartos),
        banheiros: paraNumeroOuNulo(fields.banheiros),
        vagas: paraNumeroOuNulo(fields.vagas),
        valor: Number(fields.valor),
        status: fields.status,
      }
      if (isEdit) {
        await atualizarImovel(imovel.id, payload)
      } else {
        await criarImovel(payload)
      }
      onSuccess()
    } catch (err) {
      setErros({ form: err?.detail ?? 'Erro ao salvar. Tente novamente.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <h2 className="text-lg font-semibold">{isEdit ? 'Editar Imóvel' : 'Novo Imóvel'}</h2>

      {erros.form && <p className="text-sm text-destructive">{erros.form}</p>}

      <div className="space-y-1">
        <Label htmlFor="titulo">Título</Label>
        <Input id="titulo" name="titulo" value={fields.titulo} onChange={handleChange} aria-invalid={Boolean(erros.titulo)} required />
        {erros.titulo && <p className="text-sm text-destructive">{erros.titulo}</p>}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label htmlFor="tipo_negocio">Negócio</Label>
          <select id="tipo_negocio" name="tipo_negocio" className={SELECT_CLASSES} value={fields.tipo_negocio} onChange={handleChange}>
            {TIPOS_NEGOCIO.map(o => <option key={o.valor} value={o.valor}>{o.rotulo}</option>)}
          </select>
        </div>
        <div className="space-y-1">
          <Label htmlFor="tipo_imovel">Tipo</Label>
          <select id="tipo_imovel" name="tipo_imovel" className={SELECT_CLASSES} value={fields.tipo_imovel} onChange={handleChange}>
            {TIPOS_IMOVEL.map(o => <option key={o.valor} value={o.valor}>{o.rotulo}</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label htmlFor="estado">Estado</Label>
          <Input id="estado" name="estado" value={fields.estado} onChange={handleChange} aria-invalid={Boolean(erros.estado)} required />
          {erros.estado && <p className="text-sm text-destructive">{erros.estado}</p>}
        </div>
        <div className="space-y-1">
          <Label htmlFor="bairro">Bairro</Label>
          <Input id="bairro" name="bairro" value={fields.bairro} onChange={handleChange} aria-invalid={Boolean(erros.bairro)} required />
          {erros.bairro && <p className="text-sm text-destructive">{erros.bairro}</p>}
        </div>
      </div>

      <div className="space-y-1">
        <Label htmlFor="endereco">Endereço (opcional)</Label>
        <Input id="endereco" name="endereco" value={fields.endereco} onChange={handleChange} />
      </div>

      <div className="grid grid-cols-4 gap-3">
        <div className="space-y-1">
          <Label htmlFor="metragem">Metragem (m²)</Label>
          <Input id="metragem" name="metragem" type="number" min="0" step="0.1" value={fields.metragem} onChange={handleChange} aria-invalid={Boolean(erros.metragem)} />
          {erros.metragem && <p className="text-sm text-destructive">{erros.metragem}</p>}
        </div>
        <div className="space-y-1">
          <Label htmlFor="quartos">Quartos</Label>
          <Input id="quartos" name="quartos" type="number" min="0" value={fields.quartos} onChange={handleChange} aria-invalid={Boolean(erros.quartos)} />
        </div>
        <div className="space-y-1">
          <Label htmlFor="banheiros">Banheiros</Label>
          <Input id="banheiros" name="banheiros" type="number" min="0" value={fields.banheiros} onChange={handleChange} aria-invalid={Boolean(erros.banheiros)} />
        </div>
        <div className="space-y-1">
          <Label htmlFor="vagas">Vagas</Label>
          <Input id="vagas" name="vagas" type="number" min="0" value={fields.vagas} onChange={handleChange} aria-invalid={Boolean(erros.vagas)} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label htmlFor="valor">Valor (R$)</Label>
          <Input id="valor" name="valor" type="number" min="0" step="0.01" value={fields.valor} onChange={handleChange} aria-invalid={Boolean(erros.valor)} required />
          {erros.valor && <p className="text-sm text-destructive">{erros.valor}</p>}
        </div>
        <div className="space-y-1">
          <Label htmlFor="status">Status</Label>
          <select id="status" name="status" className={SELECT_CLASSES} value={fields.status} onChange={handleChange}>
            {STATUS_IMOVEL.map(o => <option key={o.valor} value={o.valor}>{o.rotulo}</option>)}
          </select>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>Cancelar</Button>
        <Button type="submit" disabled={loading}>{loading ? 'Salvando…' : 'Salvar'}</Button>
      </div>
    </form>
  )
}
