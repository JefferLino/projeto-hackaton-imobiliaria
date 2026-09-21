import { Plus, Loader2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import ConfirmDialog from '../components/ConfirmDialog'
import ImovelForm from '../components/ImovelForm'
import ImovelList from '../components/ImovelList'
import { deletarImovel, listarImoveis } from '../services/imoveis'

export default function ImoveisPage() {
  const [imoveis, setImoveis] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [modo, setModo] = useState('lista') // 'lista' | 'criar' | 'editar'
  const [editando, setEditando] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(null)

  const carregar = useCallback(async () => {
    try {
      const data = await listarImoveis()
      setImoveis(data)
    } catch {
      toast.error('Erro ao carregar imóveis.')
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregar()
  }, [carregar])

  function handleEdit(imovel) {
    setEditando(imovel)
    setModo('editar')
  }

  function handleDelete(id) {
    setConfirmDelete(id)
  }

  async function confirmarDelete() {
    try {
      await deletarImovel(confirmDelete)
      toast.success('Imóvel removido com sucesso.')
      setCarregando(true)
      carregar()
    } catch (err) {
      toast.error(err?.detail ?? 'Erro ao remover imóvel.')
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
        <h1 className="text-xl font-semibold min-w-0">Catálogo de Imóveis</h1>
        {modo === 'lista' && (
          <Button onClick={() => setModo('criar')} className="shrink-0">
            <Plus className="h-4 w-4" />
            Novo Imóvel
          </Button>
        )}
      </div>

      <Separator className="mb-6" />

      {modo !== 'lista' ? (
        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <ImovelForm
            imovel={modo === 'editar' ? editando : null}
            onSuccess={() =>
              handleFormSuccess(modo === 'criar' ? 'Imóvel cadastrado com sucesso.' : 'Imóvel atualizado com sucesso.')
            }
            onCancel={handleCancel}
          />
        </div>
      ) : carregando ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <ImovelList imoveis={imoveis} onEdit={handleEdit} onDelete={handleDelete} />
      )}

      <ConfirmDialog
        open={confirmDelete !== null}
        title="Confirmar exclusão"
        message="Tem certeza que deseja excluir este imóvel? Esta ação não pode ser desfeita."
        onClose={() => setConfirmDelete(null)}
        onConfirm={confirmarDelete}
      />
    </div>
  )
}
