import { Plus, Loader2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
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

  const carregar = useCallback(async () => {
    try {
      const data = await listarCorretores()
      setCorretores(data)
    } catch {
      toast.error('Erro ao carregar corretores.')
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregar()
  }, [carregar])

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
      toast.success('Corretor removido com sucesso.')
      setCarregando(true)
      carregar()
    } catch (err) {
      toast.error(err?.detail ?? 'Erro ao remover corretor.')
    } finally {
      setConfirmDelete(null)
    }
  }

  function handleFormSuccess(msg = 'Operação realizada com sucesso.') {
    toast.success(msg)
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
    <div className="w-full px-6 py-8">
      <div className="flex items-center justify-between gap-4 mb-4">
        <h1 className="text-xl font-semibold min-w-0">Gerenciamento de Corretores</h1>
        {modo === 'lista' && (
          <Button onClick={() => setModo('criar')} className="shrink-0">
            <Plus className="h-4 w-4" />
            Novo Corretor
          </Button>
        )}
      </div>

      <Separator className="mb-6" />

      {modo !== 'lista' ? (
        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <CorretorForm
            corretor={modo === 'editar' ? editando : null}
            onSuccess={() =>
              handleFormSuccess(
                modo === 'criar' ? 'Corretor cadastrado com sucesso.' : 'Corretor atualizado com sucesso.'
              )
            }
            onCancel={handleCancel}
          />
        </div>
      ) : carregando ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
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
    </div>
  )
}
