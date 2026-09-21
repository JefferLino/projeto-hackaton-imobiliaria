import { Pencil, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { rotulo } from '../lib/imovelOpcoes'

const STATUS_CLASSES = {
  disponivel: 'bg-green-100 text-green-800',
  reservado: 'bg-amber-100 text-amber-800',
  vendido: 'bg-muted text-muted-foreground',
  alugado: 'bg-muted text-muted-foreground',
}

function formatarValor(valor) {
  return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export default function ImovelList({ imoveis, onEdit, onDelete }) {
  if (imoveis.length === 0) {
    return (
      <p className="text-center text-muted-foreground py-10">Nenhum imóvel cadastrado.</p>
    )
  }

  return (
    <TooltipProvider>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Título</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Localização</TableHead>
              <TableHead>Valor</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-center">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {imoveis.map(i => (
              <TableRow key={i.id}>
                <TableCell>{i.titulo}</TableCell>
                <TableCell>{rotulo(i.tipo_imovel)} · {rotulo(i.tipo_negocio)}</TableCell>
                <TableCell>{i.bairro}, {i.estado}</TableCell>
                <TableCell>{formatarValor(i.valor)}</TableCell>
                <TableCell>
                  <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium', STATUS_CLASSES[i.status])}>
                    {rotulo(i.status)}
                  </span>
                </TableCell>
                <TableCell className="text-center">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="ghost" size="icon" aria-label="Editar imóvel" onClick={() => onEdit(i)}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Editar</TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="ghost" size="icon" aria-label="Excluir imóvel" className="text-destructive hover:text-destructive" onClick={() => onDelete(i.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Excluir</TooltipContent>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </TooltipProvider>
  )
}
