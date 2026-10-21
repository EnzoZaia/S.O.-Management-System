export type ResultadoChecklistItem = 'PENDENTE' | 'EXECUTADO' | 'NAO_EXECUTADO'
export type ResultadoAtivoChecklist = 'PENDENTE' | 'CONCLUIDO' | 'NAO_CONCLUIDO'

export interface ItemChecklist {
  id_item: number
  descricao: string
  resultado: ResultadoChecklistItem
  /** Obrigatório quando o item é marcado como não executado. */
  motivo?: string | null
}

/** O checklist fica associado ao patrimônio do ativo (regra de negócio). */
export interface AtivoChecklist {
  ativo: number
  codigo_patrimonial: string
  nome: string
  tipo_ativo?: string
  resultado: ResultadoAtivoChecklist
  motivo?: string | null
  itens: ItemChecklist[]
}

export interface ChecklistOrdem {
  id_ordem_servico: number
  ativos: AtivoChecklist[]
}

export interface ItemChecklistEnvio {
  item: number
  resultado: Exclude<ResultadoChecklistItem, 'PENDENTE'>
  motivo?: string
}

export interface ErrosChecklistAtivo {
  /** Erro de motivo por item (chave = id_item). */
  itens: Record<number, string>
  /** Motivo do ativo quando ele é registrado como não concluído. */
  motivo?: string
  /** Mensagem geral (ex.: checklist incompleto). */
  geral?: string
}

export type TipoErroChecklist =
  | 'INDISPONIVEL'
  | 'FORA_ESCOPO'
  | 'CHECKLIST_INCOMPLETO'
  | 'STATUS_INVALIDO'
  | 'VALIDACAO'
  | 'GENERICO'

export interface ErroChecklist {
  tipo: TipoErroChecklist
  mensagem: string
}