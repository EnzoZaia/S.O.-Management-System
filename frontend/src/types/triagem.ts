export type DecisaoTriagem = 'APROVAR' | 'REPROVAR' | 'CANCELAR'
export type CategoriaManutencao = 'REFRIGERACAO' | 'ELETRICA' | 'GERAIS'
export type PrioridadeApi = 'SIM' | 'NAO'

export interface FormularioTriagem {
  decisao: DecisaoTriagem | null
  categoria: CategoriaManutencao | ''
  prioridade: PrioridadeApi
  justificativa: string
}

export type ErrosTriagem = Partial<Record<'decisao' | 'categoria' | 'prioridade' | 'justificativa', string>>

export interface DadosTriagem {
  decisao: DecisaoTriagem
  categoria?: CategoriaManutencao
  prioridade?: PrioridadeApi
  justificativa?: string
}

export type TipoErroTriagem = 'FORA_ESCOPO' | 'STATUS_INVALIDO' | 'VALIDACAO' | 'GENERICO'

export interface ErroTriagem {
  tipo: TipoErroTriagem
  mensagem: string
  campos: ErrosTriagem
}