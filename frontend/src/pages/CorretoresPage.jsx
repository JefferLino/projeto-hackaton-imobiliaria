import AddIcon from '@mui/icons-material/Add'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Container from '@mui/material/Container'
import Divider from '@mui/material/Divider'
import Paper from '@mui/material/Paper'
import Snackbar from '@mui/material/Snackbar'
import Typography from '@mui/material/Typography'
import { useCallback, useEffect, useState } from 'react'

import ConfirmDialog from '../components/ConfirmDialog'
import CorretorForm from '../components/CorretorForm'
import CorretorList from '../components/CorretorList'
import { deletarCorretor, listarCorretores } from '../services/corretores'

export default function CorretoresPage() {
  const [corretores, setCorretores] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [modo, setModo] = useState('lista') // 'lista' | 'criar' | 'editar'
  const [editando, setEditando] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [toast, setToast] = useState({ open: false, msg: '', severity: 'success' })

  const carregar = useCallback(async () => {
    try {
      const data = await listarCorretores()
      setCorretores(data)
    } catch {
      mostrarToast('Erro ao carregar corretores.', 'error')
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregar()
  }, [carregar])

  function mostrarToast(msg, severity = 'success') {
    setToast({ open: true, msg, severity })
  }

  function handleEdit(corretor) {
    setEditando(corretor)
    setModo('editar')
  }

  function handleDelete(id) {
    setConfirmDelete(id)
  }

  async function confirmarDelete() {
    try {
      await deletarCorretor(confirmDelete)
      mostrarToast('Corretor removido com sucesso.')
      setCarregando(true)
      carregar()
    } catch (err) {
      mostrarToast(err?.detail ?? 'Erro ao remover corretor.', 'error')
    } finally {
      setConfirmDelete(null)
    }
  }

  function handleFormSuccess(msg = 'Operação realizada com sucesso.') {
    mostrarToast(msg)
    setModo('lista')
    setEditando(null)
    setCarregando(true)
    carregar()
  }

  function handleCancel() {
    setModo('lista')
    setEditando(null)
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={600}>
          Gerenciamento de Corretores
        </Typography>
        {modo === 'lista' && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setModo('criar')}
          >
            Novo Corretor
          </Button>
        )}
      </Box>

      <Divider sx={{ mb: 3 }} />

      {modo !== 'lista' ? (
        <Paper sx={{ p: 3 }}>
          <CorretorForm
            corretor={modo === 'editar' ? editando : null}
            onSuccess={() =>
              handleFormSuccess(
                modo === 'criar' ? 'Corretor cadastrado com sucesso.' : 'Corretor atualizado com sucesso.'
              )
            }
            onCancel={handleCancel}
          />
        </Paper>
      ) : carregando ? (
        <Box display="flex" justifyContent="center" py={6}>
          <CircularProgress />
        </Box>
      ) : (
        <CorretorList
          corretores={corretores}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}

      <ConfirmDialog
        open={confirmDelete !== null}
        title="Confirmar exclusão"
        message="Tem certeza que deseja excluir este corretor? Esta ação não pode ser desfeita."
        onClose={() => setConfirmDelete(null)}
        onConfirm={confirmarDelete}
      />

      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast(t => ({ ...t, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={toast.severity} variant="filled" onClose={() => setToast(t => ({ ...t, open: false }))}>
          {toast.msg}
        </Alert>
      </Snackbar>
    </Container>
  )
}
