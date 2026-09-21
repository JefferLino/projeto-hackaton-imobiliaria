import { Loader2, Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { resumoPreferencias } from '../lib/leadFormat'
import { buscarHistorico, enviarMensagemManual } from '../services/conversas'

const TEXTAREA_CLASSES =
  'flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'

export default function LeadConversationDialog({ lead, open, onClose }) {
  const [carregando, setCarregando] = useState(true)
  const [historico, setHistorico] = useState(null)
  const [texto, setTexto] = useState('')
  const [enviando, setEnviando] = useState(false)
  const chatRef = useRef(null)

  useEffect(() => {
    if (!open || !lead) return
    setCarregando(true)
    setHistorico(null)
    buscarHistorico(lead.conversa_id, lead.telefone)
      .then(setHistorico)
      .catch(() => toast.error('Erro ao carregar a conversa.'))
      .finally(() => setCarregando(false))
  }, [open, lead])

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight })
  }, [historico])

  async function handleEnviar() {
    if (!texto.trim() || !lead) return
    setEnviando(true)
    try {
      await enviarMensagemManual(lead.conversa_id, lead.telefone, texto.trim())
      setTexto('')
      const atualizado = await buscarHistorico(lead.conversa_id, lead.telefone)
      setHistorico(atualizado)
      toast.success('Mensagem enviada.')
    } catch (err) {
      toast.error(err?.detail ?? 'Erro ao enviar mensagem.')
    } finally {
      setEnviando(false)
    }
  }

  const encerrada = historico?.status === 'encerrada'

  return (
    <Dialog open={open} onOpenChange={v => !v && onClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{lead?.nome || lead?.telefone}</DialogTitle>
        </DialogHeader>

        {carregando ? (
          <div className="flex justify-center py-10">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <span>{resumoPreferencias(historico?.dados)}</span>
              {historico?.modo_manual && (
                <span className="rounded-full bg-blue-100 px-2 py-0.5 font-medium text-blue-800">
                  Atendimento manual ativo
                </span>
              )}
            </div>

            <div ref={chatRef} className="h-80 space-y-2 overflow-y-auto rounded-md border bg-muted/20 p-3">
              {historico?.mensagens?.length ? (
                historico.mensagens.map(m => (
                  <div
                    key={m.ID}
                    className={cn('flex', m.ResponsavelEnvio === 'cliente' ? 'justify-start' : 'justify-end')}
                  >
                    <div
                      className={cn(
                        'max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap',
                        m.ResponsavelEnvio === 'cliente'
                          ? 'bg-background border'
                          : 'bg-primary text-primary-foreground'
                      )}
                    >
                      <p className="mb-0.5 text-[10px] opacity-70">
                        {m.ResponsavelEnvio === 'cliente' ? 'Cliente' : 'Atendimento'}
                      </p>
                      {m.Texto}
                    </div>
                  </div>
                ))
              ) : (
                <p className="py-8 text-center text-sm text-muted-foreground">Nenhuma mensagem ainda.</p>
              )}
            </div>

            <div className="flex gap-2">
              <textarea
                className={TEXTAREA_CLASSES}
                rows={2}
                placeholder={encerrada ? 'Conversa encerrada.' : 'Digite sua mensagem…'}
                value={texto}
                onChange={e => setTexto(e.target.value)}
                disabled={encerrada || enviando}
              />
              <Button onClick={handleEnviar} disabled={encerrada || enviando || !texto.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
