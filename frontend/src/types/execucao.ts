export type MotivoPausa = 'AGUARDANDO_MATERIAL' | 'AGUARDANDO_TERCEIRO'

export type CausaRaiz =
  | 'DESGASTE_NATURAL'
  | 'MAU_USO'
  | 'FALHA_ELETRICA'
  | 'FALTA_MANUTENCAO'
  | 'DEFEITO_FABRICACAO'
  | 'OUTRA'

export interface Insumo {
  descricao: string
  quantidade: string
}

export interface AtivoOpcao {
  id_ativo?: number | string
  id?: number | string
  codigo_patrimonial: string
  nomeLimpo: string
}

export interface FormularioConclusao {
  tipoEquipamento: '' | 'AR_CONDICIONADO' | 'OUTROS'
  patrimonio: string
  observacao: string
  causaRaiz: CausaRaiz | ''
  causaDetalhe: string
  dataHoraFinal: string
  insumos: Insumo[]
}

export type CampoConclusao =
  | 'equipamento'
  | 'observacao'
  | 'causaRaiz'
  | 'causaDetalhe'
  | 'dataHoraFinal'
  | 'insumos'

export type ErrosConclusao = Partial<Record<CampoConclusao, string>>

export interface FormularioPausa {
  motivo: MotivoPausa | ''
  detalhe: string
}

export type ErrosPausa = Partial<Record<'motivo' | 'detalhe', string>>

export interface DadosPausa {
  motivo: MotivoPausa
  detalhe: string
}

export interface DadosConclusao {
  observacao: string
  causaRaiz?: string
  idAtivo?: number | string
}

export type TipoErroExecucao = 'FORA_ESCOPO' | 'STATUS_INVALIDO' | 'VALIDACAO' | 'GENERICO'

export interface ErroExecucao {
  tipo: TipoErroExecucao
  mensagem: string
  campos: ErrosConclusao
}

export interface RespostaExecucao {
  status_ordem_servico?: string
}

export interface EventoStatus {
  data_registro: string
  status_anterior?: string | null
  status_novo?: string | null
  desc_historico?: string | null
}

export interface PeriodoPausa {
  motivo: MotivoPausa
  inicio: string
  fim: string | null
  duracaoMs: number
}

export interface Apontamento {
  inicio: string | null
  fim: string | null
  pausas: PeriodoPausa[]
  emPausa: boolean
  tempoPausadoMs: number
  tempoTrabalhadoMs: number
}