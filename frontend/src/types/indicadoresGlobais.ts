export type PeriodoGlobal = '30d' | 'mes_atual' | 'mes_passado' | 'ano' | 'personalizado'

export interface ConsultaIndicadores {
  periodo: PeriodoGlobal
  /** AAAA-MM-DD; só usado quando periodo === 'personalizado'. */
  inicio?: string
  fim?: string
}

export type ChaveIndicador =
  | 'backlog'
  | 'mttr'
  | 'primeiraIntervencao'
  | 'satisfacao'
  | 'reincidencia'
  | 'afetados'

export interface ItemDistribuicao {
  chave: string | number
  rotulo: string
  detalhe?: string | null
  total: number
}

export interface PredioOcorrencias {
  chave: string | number
  nome: string
  totalOcorrencias: number
  /** Cada pessoa vinculada (solicitante + "presenciei", US05) conta uma única vez por ordem. */
  totalAfetados: number
}

export interface IndicadoresGlobais {
  /** Intervalo efetivamente usado pelo backend (CA1: o mesmo para todos os indicadores). */
  intervalo: { inicio: string | null; fim: string | null }
  totalOrdens: number
  backlogAtivo: number
  /** Tempo médio de resolução, em horas. */
  mttrHoras: number | null
  /** Percentual (0-100) de corretivas resolvidas sem retorno ao técnico. */
  resolucaoPrimeiraIntervencao: number | null
  satisfacaoMedia: number | null
  totalAvaliacoes: number
  /** Percentual (0-100). */
  reincidencia: number | null
  totalAfetados: number
  porAtivo: ItemDistribuicao[]
  porLocalizacao: ItemDistribuicao[]
  porPredio: PredioOcorrencias[]
}

export type TipoErroGlobais = 'SEM_PERMISSAO' | 'INDISPONIVEL' | 'PERIODO_INVALIDO' | 'GENERICO'

export interface ErroGlobais {
  tipo: TipoErroGlobais
  mensagem: string
}