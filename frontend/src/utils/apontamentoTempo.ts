import type { Apontamento, EventoStatus, MotivoPausa, PeriodoPausa } from '@/types/execucao'

const STATUS_PAUSA: string[] = ['AGUARDANDO_MATERIAL', 'AGUARDANDO_TERCEIRO']
const STATUS_FIM: string[] = ['AGUARDANDO_VALIDACAO', 'CONCLUIDA', 'ENCERRADA']

export const ROTULO_MOTIVO_PAUSA: Record<string, string> = {
  AGUARDANDO_MATERIAL: 'Falta de material',
  AGUARDANDO_TERCEIRO: 'Aguardando terceiro',
}

/** Reconstrói início, pausas e tempo trabalhado a partir do histórico de mudanças de status da OS. */
export function calcularApontamento(eventos: EventoStatus[], agora: number): Apontamento {
  const ordenados = eventos
    .filter((e) => !!e.status_novo)
    .sort((a, b) => Date.parse(a.data_registro) - Date.parse(b.data_registro))

  let inicio: string | null = null
  let fim: string | null = null
  const pausas: PeriodoPausa[] = []
  const estado = { aberta: null as PeriodoPausa | null }

  const fechar = (ate: string) => {
    const p = estado.aberta
    if (!p) return
    p.fim = ate
    p.duracaoMs = Math.max(0, Date.parse(ate) - Date.parse(p.inicio))
    estado.aberta = null
  }

  for (const ev of ordenados) {
    const novo = String(ev.status_novo)
    if (novo === 'EM_EXECUCAO') {
      if (!inicio) inicio = ev.data_registro
      fim = null
      fechar(ev.data_registro)
    } else if (STATUS_PAUSA.includes(novo)) {
      if (!estado.aberta) {
        const p: PeriodoPausa = { motivo: novo as MotivoPausa, inicio: ev.data_registro, fim: null, duracaoMs: 0 }
        pausas.push(p)
        estado.aberta = p
      }
    } else if (STATUS_FIM.includes(novo) && inicio) {
      fechar(ev.data_registro)
      fim = ev.data_registro
    }
  }

  const pausasCalculadas = pausas.map((p) =>
    p.fim ? p : { ...p, duracaoMs: Math.max(0, agora - Date.parse(p.inicio)) },
  )
  const tempoPausadoMs = pausasCalculadas.reduce((soma, p) => soma + p.duracaoMs, 0)
  const limite = fim ? Date.parse(fim) : agora
  const tempoTrabalhadoMs = inicio ? Math.max(0, limite - Date.parse(inicio) - tempoPausadoMs) : 0

  return {
    inicio,
    fim,
    pausas: pausasCalculadas,
    emPausa: estado.aberta !== null,
    tempoPausadoMs,
    tempoTrabalhadoMs,
  }
}

export function formatarDuracao(ms: number): string {
  const minutos = Math.floor(ms / 60000)
  if (ms <= 0) return '0 min'
  if (minutos < 1) return '< 1 min'
  const dias = Math.floor(minutos / 1440)
  const horas = Math.floor((minutos % 1440) / 60)
  const resto = minutos % 60
  const partes: string[] = []
  if (dias) partes.push(`${dias}d`)
  if (horas) partes.push(`${horas}h`)
  if (resto) partes.push(`${resto}min`)
  return partes.join(' ')
}