import { Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { atualizarCorretor, criarCorretor } from '../services/corretores'

const DIGIT_RE = /\d/
const EMAIL_RE = /^\S+@\S+\.\S+$/
const PHONE_RE = /^\d{10,11}$/

function validate(fields, isEdit) {
  const erros = {}
  if (!fields.nome || fields.nome.trim().length < 2) {
    erros.nome = 'Nome deve ter ao menos 2 caracteres'
  } else if (DIGIT_RE.test(fields.nome)) {
    erros.nome = 'Nome não pode conter dígitos'
  }
  if (!fields.email || !EMAIL_RE.test(fields.email.trim())) {
    erros.email = 'Email inválido'
  }
  if (!fields.telefone || !PHONE_RE.test(fields.telefone)) {
    erros.telefone = 'Telefone deve ter 10 ou 11 dígitos (somente números)'
  }
  if (!isEdit && (!fields.senha || fields.senha.length < 8)) {
    erros.senha = 'Senha deve ter no mínimo 8 caracteres'
  }
  if (isEdit && fields.senha && fields.senha.length > 0 && fields.senha.length < 8) {
    erros.senha = 'Senha deve ter no mínimo 8 caracteres'
  }
  return erros
}

export default function CorretorForm({ corretor, onSuccess, onCancel }) {
  const isEdit = Boolean(corretor)
  const [fields, setFields] = useState({
    nome: corretor?.nome ?? '',
    email: corretor?.email ?? '',
    telefone: corretor?.telefone ?? '',
    senha: '',
  })
  const [erros, setErros] = useState({})
  const [showSenha, setShowSenha] = useState(false)
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    const { name, value } = e.target
    setFields(prev => ({ ...prev, [name]: value }))
    setErros(prev => ({ ...prev, [name]: undefined }))
  }

  function handleBlur(e) {
    const { name } = e.target
    const err = validate(fields, isEdit)
    if (err[name]) setErros(prev => ({ ...prev, [name]: err[name] }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const err = validate(fields, isEdit)
    if (Object.keys(err).length) {
      setErros(err)
      return
    }
    setLoading(true)
    try {
      const payload = { nome: fields.nome.trim(), email: fields.email.trim(), telefone: fields.telefone }
      if (!isEdit || fields.senha) payload.senha = fields.senha
      if (isEdit) {
        await atualizarCorretor(corretor.id, payload)
      } else {
        await criarCorretor(payload)
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
      <h2 className="text-lg font-semibold">
        {isEdit ? 'Editar Corretor' : 'Novo Corretor'}
      </h2>

      {erros.form && (
        <p className="text-sm text-destructive">{erros.form}</p>
      )}

      <div className="space-y-1">
        <Label htmlFor="nome">Nome</Label>
        <Input
          id="nome"
          name="nome"
          value={fields.nome}
          onChange={handleChange}
          onBlur={handleBlur}
          aria-invalid={Boolean(erros.nome)}
          required
        />
        {erros.nome
          ? <p className="text-sm text-destructive">{erros.nome}</p>
          : null}
      </div>

      <div className="space-y-1">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          name="email"
          type="email"
          value={fields.email}
          onChange={handleChange}
          onBlur={handleBlur}
          aria-invalid={Boolean(erros.email)}
          required
        />
        {erros.email
          ? <p className="text-sm text-destructive">{erros.email}</p>
          : null}
      </div>

      <div className="space-y-1">
        <Label htmlFor="telefone">Telefone</Label>
        <Input
          id="telefone"
          name="telefone"
          value={fields.telefone}
          onChange={e => {
            const v = e.target.value.replace(/\D/g, '')
            setFields(prev => ({ ...prev, telefone: v }))
            setErros(prev => ({ ...prev, telefone: undefined }))
          }}
          onBlur={handleBlur}
          maxLength={11}
          aria-invalid={Boolean(erros.telefone)}
          required
        />
        {erros.telefone
          ? <p className="text-sm text-destructive">{erros.telefone}</p>
          : <p className="text-xs text-muted-foreground">Somente dígitos, 10 ou 11 caracteres</p>}
      </div>

      <div className="space-y-1">
        <Label htmlFor="senha">
          {isEdit ? 'Nova senha (deixe em branco para manter)' : 'Senha'}
        </Label>
        <div className="relative">
          <Input
            id="senha"
            name="senha"
            type={showSenha ? 'text' : 'password'}
            value={fields.senha}
            onChange={handleChange}
            onBlur={handleBlur}
            aria-invalid={Boolean(erros.senha)}
            required={!isEdit}
            className="pr-10"
          />
          <button
            type="button"
            aria-label={showSenha ? 'Ocultar senha' : 'Mostrar senha'}
            onClick={() => setShowSenha(v => !v)}
            className="absolute inset-y-0 right-0 flex items-center px-3 text-muted-foreground hover:text-foreground"
          >
            {showSenha ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {erros.senha
          ? <p className="text-sm text-destructive">{erros.senha}</p>
          : <p className="text-xs text-muted-foreground">Mínimo 8 caracteres</p>}
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
          Cancelar
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? 'Salvando…' : 'Salvar'}
        </Button>
      </div>
    </form>
  )
}
