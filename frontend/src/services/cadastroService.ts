import axios from 'axios'
import api from '@/services/api'
import type {
  ApiEnvelope,
  CadastroSolicitantePayload,
  CampoCadastro,
  ConfirmacaoEmailResultado,
  ErroApiNormalizado,
} from '@/types/cadastro'

const CAMPOS_BACKEND: Record<string, CampoCadastro> = { nome: 'nome', email: 'email', senha: 'senha' }

/** Converte erros do Axios/DRF no formato usado pelas telas (mensagem geral + erros por campo). */
export function normalizarErroApi(error: unknown, mensagemPadrao: string): ErroApiNormalizado {
  if (!axios.isAxiosError(error)) return { mensagem: mensagemPadrao, campos: {} }
  if (!error.response) {
    return { mensagem: 'Não foi possível conectar ao servidor. Tente novamente.', campos: {} }
  }

  const corpo = error.response.data as Partial<ApiEnvelope<unknown>> & { erro?: string; detail?: string }
  const campos: ErroApiNormalizado['campos'] = {}

  if (corpo?.erros && typeof corpo.erros === 'object') {
    for (const [chave, valor] of Object.entries(corpo.erros)) {
      const campo = CAMPOS_BACKEND[chave]
      if (campo) campos[campo] = Array.isArray(valor) ? (valor[0] ?? '') : String(valor)
    }
  }

  return {
    mensagem: corpo?.mensagem || corpo?.erro || corpo?.detail || mensagemPadrao,
    campos,
    statusHttp: error.response.status,
  }
}

/** CA1/CA3: cria a conta pendente. O backend define o perfil SOLICITANTE e envia o e-mail. */
export async function cadastrarSolicitante(payload: CadastroSolicitantePayload) {
  const { data } = await api.post<ApiEnvelope<unknown>>('/usuario/', payload)
  return data
}

/** CA2/CA4: valida o token do link. A resposta traz o RA gerado quando a conta é ativada. */
export async function confirmarEmail(token: string): Promise<ConfirmacaoEmailResultado> {
  const { data } = await api.get<ApiEnvelope<ConfirmacaoEmailResultado | null>>(
    `/usuario/confirmar-email/${encodeURIComponent(token)}/`,
  )
  return data.dados ?? {}
}

/** CA4: solicita novo envio do e-mail de confirmação (endpoint a ser criado no backend). */
export async function reenviarConfirmacao(email: string) {
  const { data } = await api.post<ApiEnvelope<unknown>>('/usuario/reenviar-confirmacao/', { email })
  return data
}