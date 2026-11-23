import type { OrdemPainel } from '@/types/painelGestor'

export type SituacaoFila = 'PARA_INICIAR' | 'EM_EXECUCAO' | 'PAUSADA' | 'AGUARDANDO_VALIDACAO'

export interface OrdemDaFila {
  ordem: OrdemPainel
  situacao: SituacaoFila
  /** Dias desde a abertura da ordem. */
  diasEmAberto: number
}

export interface ResumoFila {
  paraIniciar: number
  emExecucao: number
  pausadas: number
  aguardandoValidacao: number
  /** Ordens urgentes que ainda dependem do técnico (não inclui aguardando validação). */
  urgentes: number
  total: number
}

export interface TempoPorTipo {
  corretivaMs: number | null
  preventivaMs: number | null
  corretivaTotal: number
  preventivaTotal: number
}