export type SituacaoAtivoPreventiva = 'ATRASADA' | 'PENDENTE' | 'EM_EXECUCAO'
export type ResultadoItem = 'PENDENTE' | 'CONCLUIDO' | 'NAO_CONCLUIDO'

export interface AtivoPainel {
  id_ativo: number
  codigo_patrimonial: string
  nome: string
  localizacao_nome: string
  id_predio: number
  dt_ultima_preventiva: string | null
  dt_proxima_preventiva: string | null
  dias: number | null
  situacao: SituacaoAtivoPreventiva
  /** CA4: motivo informado quando o ativo voltou como não concluído. */
  motivo_retorno?: string | null
  /** Código único da OS agrupada quando o ativo está em execução. */
  grupo_codigo?: number | null
}

export interface CardPredio {
  id_predio: number
  nome_predio: string
  ativos: AtivoPainel[]
  atrasados: number
  pendentes: number
  emExecucao: number
}

export interface ItemGrupo {
  ativo: number
  resultado: ResultadoItem
  motivo?: string | null
}

export interface GrupoPreventiva {
  id_ordem_servico: number
  predio: number
  tecnico: number | null
  tecnico_nome?: string | null
  status_ordem_servico: string
  itens: ItemGrupo[]
}

export interface DadosGerarOrdem {
  predio: number
  tecnico: number
  ativos: number[]
}

export interface ResultadoItemEnvio {
  ativo: number
  resultado: Exclude<ResultadoItem, 'PENDENTE'>
  motivo?: string
}

export type ErrosGeracao = Partial<Record<'selecao' | 'tecnico', string>>

export type TipoErroGrupo = 'FORA_ESCOPO' | 'MESMO_PREDIO' | 'STATUS_INVALIDO' | 'VALIDACAO' | 'INDISPONIVEL' | 'GENERICO'

export interface ErroGrupo {
  tipo: TipoErroGrupo
  mensagem: string
}