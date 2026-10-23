export type PeriodoPainel = '30d' | 'mes_atual' | 'mes_passado' | 'ano'

export interface TecnicoRanking {
  nome: string
  total: number
  concluidas: number
  satisfacao_media?: number | null
  total_avaliacoes?: number
}

export interface PendenciasPainel {
  aguardando_aprovacao: number
  aguardando_material: number
  aguardando_terceiro: number
  aguardando_validacao: number
  sem_tecnico: number
}

export interface SemanaPainel {
  label: string
  valor: number
}

export interface IndicadoresGestor {
  totalOrdens: number
  abertas: number
  concluidas: number
  aguardandoValidacao: number
  /** Texto vindo do backend em dias (ex.: "1.5d"). */
  tempoMedio: string
  statusDetalhados: Record<string, number>
  tipoManutencao: { preventiva: number; corretiva: number }
  rankingTecnicos: TecnicoRanking[]
  satisfacaoMedia: number | null
  totalAvaliacoes: number
  pendencias: PendenciasPainel
  semanas: SemanaPainel[]
}

/** Ordem como devolvida por GET /ordem-servico/ (já filtrada no backend pelo escopo do gestor). */
export interface OrdemPainel {
  id_ordem_servico: number
  status_ordem_servico: string
  tipo_manutencao: string
  prioridade_urgencia: string
  descricao_servico: string
  dt_abertura: string
  dt_conclusao?: string | null
  predio_nome?: string | null
  localizacao_nome?: string | null
  tecnico?: number | null
  tecnico_nome?: string | null
  ativo_nome?: string | null
}

export type CategoriaGargalo = 'SEM_TRIAGEM' | 'SEM_TECNICO' | 'AGUARDANDO_MATERIAL' | 'AGUARDANDO_TERCEIRO'

export interface GargaloOrdem {
  ordem: OrdemPainel
  categoria: CategoriaGargalo
  /** Dias desde a abertura da ordem. */
  diasEmAberto: number
}

export type ResumoGargalos = Record<CategoriaGargalo, number>

export type TipoErroPainel = 'SEM_PERMISSAO' | 'GENERICO'

export interface ErroPainel {
  tipo: TipoErroPainel
  mensagem: string
}