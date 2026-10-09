
export type StatusOrdem =
  | 'ABERTA'
  | 'APROVADA'
  | 'REPROVADA'
  | 'EM_EXECUCAO'
  | 'AGUARDANDO_MATERIAL'
  | 'AGUARDANDO_TERCEIRO'
  | 'AGUARDANDO_VALIDACAO'
  | 'CONCLUIDA'
  | 'ENCERRADA'
  | 'CANCELADA'

export interface OrdemPortal {
  id_ordem_servico: number
  status_ordem_servico: StatusOrdem | string
  tipo_manutencao: string
  prioridade_urgencia: 'SIM' | 'NAO' | string
  descricao_servico: string
  dt_abertura: string
  dt_conclusao?: string | null
  predio_nome?: string
  localizacao_nome?: string
  tecnico?: number | null
  tecnico_nome?: string
  
  vinculo_presenciei?: boolean
}

export interface EventoHistorico {
  id_historico_ordem_servico: number
  data_registro: string
  desc_historico: string
  usuario?: number
  usuario_nome?: string
}

export interface InfoStatus {
  rotulo: string
  descricao: string
  icone: string
  
  classes: string
  
  ponto: string
}

export type FiltroStatusPortal = 'TODOS' | 'EM_ANDAMENTO' | 'AGUARDANDO_VOCE' | 'FINALIZADAS'

export interface ResultadoValidacao {
  aprovada: boolean
  justificativa?: string
}