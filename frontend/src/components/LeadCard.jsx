import { GripVertical, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { resumoPreferencias } from '../lib/leadFormat'
import { ETAPAS } from '../pages/etapas'

const SELECT_CLASSES =
  'flex h-9 w-full rounded-md border border-input bg-background px-2 text-xs ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'

export default function LeadCard({ lead, corretores, onChangeEtapa, onChangeCorretor, onOpenConversa, onDragStart, onDragEnd, dragging }) {
  return (
    <div
      draggable
      onDragStart={e => {
        e.dataTransfer.setData('text/plain', String(lead.conversa_id))
        e.dataTransfer.effectAllowed = 'move'
        onDragStart?.(lead.conversa_id)
      }}
      onDragEnd={() => onDragEnd?.()}
      className={cn(
        'rounded-lg border bg-card p-3 shadow-sm space-y-2 cursor-grab active:cursor-grabbing',
        dragging && 'opacity-40'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="flex items-center gap-1 text-sm font-semibold truncate">
          <GripVertical className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          {lead.nome || lead.telefone}
        </span>
        <span
          className={cn(
            'shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium',
            lead.status === 'ativa'
              ? 'bg-green-100 text-green-800'
              : 'bg-muted text-muted-foreground'
          )}
        >
          {lead.status === 'ativa' ? 'Ativa' : 'Encerrada'}
        </span>
      </div>

      <p className="text-xs text-muted-foreground">{lead.telefone}</p>
      <p className="text-xs text-muted-foreground min-h-8">{resumoPreferencias(lead.dados)}</p>

      <div className="flex gap-2 pt-1">
        <select
          aria-label="Etapa"
          className={SELECT_CLASSES}
          value={lead.etapa}
          onChange={e => onChangeEtapa(lead.conversa_id, e.target.value)}
        >
          {ETAPAS.map(etapa => (
            <option key={etapa.valor} value={etapa.valor}>{etapa.rotulo}</option>
          ))}
        </select>

        <select
          aria-label="Corretor responsável"
          className={SELECT_CLASSES}
          value={lead.corretor_id ?? ''}
          onChange={e => onChangeCorretor(lead.conversa_id, e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">Sem responsável</option>
          {corretores.map(corretor => (
            <option key={corretor.id} value={corretor.id}>{corretor.nome}</option>
          ))}
        </select>
      </div>

      <Button
        variant="outline"
        size="sm"
        className="w-full h-8 text-xs"
        onClick={() => onOpenConversa(lead)}
      >
        <MessageSquare className="h-3.5 w-3.5" />
        Conversa
      </Button>
    </div>
  )
}
