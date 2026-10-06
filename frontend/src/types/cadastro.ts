/** Envelope padrão das respostas da API (utils/responses.py do backend). */
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

/** Payload enviado ao backend no cadastro (o perfil SOLICITANTE é definido pelo servidor). */
export interface CadastroSolicitantePayload {
  nome: string
  email: string
  senha: string
}

/** Dados devolvidos pela confirmação de e-mail (RA gerado pelo backend após a ativação). */
export interface ConfirmacaoEmailResultado {
  ra?: string
}

export interface ErroApiNormalizado {
  mensagem: string
  campos: ErrosCadastro
  statusHttp?: number
}