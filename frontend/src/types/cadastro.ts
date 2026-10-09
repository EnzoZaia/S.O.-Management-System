
export interface ApiEnvelope<T> {
  status: 'sucesso' | 'erro'
  mensagem: string
  dados?: T
  erros?: Record<string, string[] | string> | null
}

export type CampoCadastro = 'nome' | 'email' | 'senha' | 'confirmarSenha'

export interface FormularioCadastro {
  nome: string
  email: string
  senha: string
  confirmarSenha: string
}

export type ErrosCadastro = Partial<Record<CampoCadastro, string>>


export interface CadastroSolicitantePayload {
  nome: string
  email: string
  senha: string
}

export interface ConfirmacaoEmailResultado {
  ra?: string
}

export interface ErroApiNormalizado {
  mensagem: string
  campos: ErrosCadastro
  statusHttp?: number
}