import { Loader2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import LeadCard from '../components/LeadCard'
import LeadConversationDialog from '../components/LeadConversationDialog'
import { listarCorretores } from '../services/corretores'
import { atualizarLead, listarLeads } from '../services/leads'
import { ETAPAS } from './etapas'

export default function PipelinePage() {
  const [leads, setLeads] = useState([])
  const [corretores, setCorretores] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [selectedLead, setSelectedLead] = useState(null)
  const [draggingId, setDraggingId] = useState(null)
  const [dragOverEtapa, setDragOverEtapa] = useState(null)

  const carregar = useCallback(async () => {
    try {
      const [leadsData, corretoresData] = await Promise.all([listarLeads(), listarCorretores()])
      setLeads(leadsData)
      setCorretores(corretoresData)
    } catch {
      toast.error('Erro ao carregar o pipeline.')
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregar()
  }, [carregar])

  async function aplicarAtualizacao(conversaId, data, mensagemErro) {
    try {
      const atualizado = await atualizarLead(conversaId, data)
      setLeads(atual => atual.map(lead => (lead.conversa_id === conversaId ? atualizado : lead)))
    } catch (err) {
      toast.error(err?.detail ?? mensagemErro)
    }
  }

  function handleChangeEtapa(conversaId, etapa) {
    aplicarAtualizacao(conversaId, { etapa }, 'Erro ao mover o lead de etapa.')
  }

  function handleChangeCorretor(conversaId, corretorId) {
    aplicarAtualizacao(conversaId, { corretor_id: corretorId }, 'Erro ao atribuir o corretor.')
  }

  function handleDrop(e, etapa) {
    e.preventDefault()
    setDragOverEtapa(null)
    const conversaId = Number(e.dataTransfer.getData('text/plain'))
    if (!conversaId) return
    const lead = leads.find(l => l.conversa_id === conversaId)
    if (lead && lead.etapa !== etapa) {
      handleChangeEtapa(conversaId, etapa)
    }
  }

  return (
    <div className="w-full px-6 py-8">
      <h1 className="text-xl font-semibold">Pipeline de Leads</h1>
      <p className="text-sm text-muted-foreground mt-1">
        Acompanhe em qual etapa cada conversa está e quem é o corretor responsável.
      </p>

      <Separator className="my-6" />

      {carregando ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-2">
          {ETAPAS.map(etapa => {
            const leadsDaEtapa = leads.filter(lead => lead.etapa === etapa.valor)
            return (
              <div
                key={etapa.valor}
                onDragOver={e => e.preventDefault()}
                onDragEnter={() => setDragOverEtapa(etapa.valor)}
                onDragLeave={() => setDragOverEtapa(atual => (atual === etapa.valor ? null : atual))}
                onDrop={e => handleDrop(e, etapa.valor)}
                className={cn(
                  'w-64 shrink-0 rounded-lg border bg-muted/30 p-2 transition-colors',
                  dragOverEtapa === etapa.valor && 'border-primary bg-primary/5'
                )}
              >
                <p className="px-1 pb-2 text-sm font-semibold">
                  {etapa.rotulo} ({leadsDaEtapa.length})
                </p>
                {leadsDaEtapa.length === 0 ? (
                  <p className="py-6 text-center text-xs text-muted-foreground">
                    Nenhum lead nesta etapa.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {leadsDaEtapa.map(lead => (
                      <LeadCard
                        key={lead.conversa_id}
                        lead={lead}
                        corretores={corretores}
                        onChangeEtapa={handleChangeEtapa}
                        onChangeCorretor={handleChangeCorretor}
                        onOpenConversa={setSelectedLead}
                        onDragStart={setDraggingId}
                        onDragEnd={() => setDraggingId(null)}
                        dragging={draggingId === lead.conversa_id}
                      />
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      <LeadConversationDialog
        lead={selectedLead}
        open={!!selectedLead}
        onClose={() => setSelectedLead(null)}
      />
    </div>
  )
}
