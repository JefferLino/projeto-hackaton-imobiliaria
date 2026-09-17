import Visibility from '@mui/icons-material/Visibility'
import VisibilityOff from '@mui/icons-material/VisibilityOff'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import InputAdornment from '@mui/material/InputAdornment'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { useState } from 'react'

import { criarCorretor, atualizarCorretor } from '../services/corretores'

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
    <Box component="form" onSubmit={handleSubmit} noValidate>
      <Typography variant="h6" mb={2}>
        {isEdit ? 'Editar Corretor' : 'Novo Corretor'}
      </Typography>
      <Stack spacing={2}>
        {erros.form && (
          <Typography color="error" variant="body2">
            {erros.form}
          </Typography>
        )}
        <TextField
          label="Nome"
          name="nome"
          value={fields.nome}
          onChange={handleChange}
          onBlur={handleBlur}
          error={Boolean(erros.nome)}
          helperText={erros.nome}
          required
          fullWidth
        />
        <TextField
          label="Email"
          name="email"
          type="email"
          value={fields.email}
          onChange={handleChange}
          onBlur={handleBlur}
          error={Boolean(erros.email)}
          helperText={erros.email}
          required
          fullWidth
        />
        <TextField
          label="Telefone"
          name="telefone"
          value={fields.telefone}
          onChange={e => {
            const v = e.target.value.replace(/\D/g, '')
            setFields(prev => ({ ...prev, telefone: v }))
            setErros(prev => ({ ...prev, telefone: undefined }))
          }}
          onBlur={handleBlur}
          error={Boolean(erros.telefone)}
          helperText={erros.telefone ?? 'Somente dígitos, 10 ou 11 caracteres'}
          required
          fullWidth
          inputProps={{ maxLength: 11 }}
        />
        <TextField
          label={isEdit ? 'Nova senha (deixe em branco para manter)' : 'Senha'}
          name="senha"
          type={showSenha ? 'text' : 'password'}
          value={fields.senha}
          onChange={handleChange}
          onBlur={handleBlur}
          error={Boolean(erros.senha)}
          helperText={erros.senha ?? 'Mínimo 8 caracteres'}
          required={!isEdit}
          fullWidth
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowSenha(v => !v)} edge="end">
                  {showSenha ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        <Stack direction="row" spacing={1} justifyContent="flex-end">
          <Button onClick={onCancel} disabled={loading}>
            Cancelar
          </Button>
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Salvando…' : 'Salvar'}
          </Button>
        </Stack>
      </Stack>
    </Box>
  )
}
