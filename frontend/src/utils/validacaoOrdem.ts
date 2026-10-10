import axios from 'axios'
import type { ErroValidacao, ValidacaoRegistrada } from '@/types/portal'

export const JUSTIFICATIVA_MIN = 10

export const JUSTIFICATIVA_MAX = 200
export const EVIDENCIAS_MAX = 3
export const EVIDENCIA_TAMANHO_MAX_MB = 5

export function validarJustificativa(texto: string): string | null {
  const valor = texto.trim()
  if (!valor) return 'Informe o motivo da reprovação.'
  if (valor.length < JUSTIFICATIVA_MIN) return `Descreva com pelo menos ${JUSTIFICATIVA_MIN} caracteres.`
  if (valor.length > JUSTIFICATIVA_MAX) return `Use no máximo ${JUSTIFICATIVA_MAX} caracteres.`
  return null
}

export function validarEvidencias(arquivos: File[]): string | null {
  if (arquivos.length > EVIDENCIAS_MAX) return `Envie no máximo ${EVIDENCIAS_MAX} arquivos.`
  for (const arquivo of arquivos) {
    if (!arquivo.type.startsWith('image/')) return `"${arquivo.name}" não é uma imagem.`
    if (arquivo.size > EVIDENCIA_TAMANHO_MAX_MB * 1024 * 1024) {
      return `"${arquivo.name}" passa de ${EVIDENCIA_TAMANHO_MAX_MB} MB.`
    }
  }
  return null
}

export function normalizarErroValidacao(error: unknown): ErroValidacao {
  if (!axios.isAxiosError(error) || !error.response) {
    return { tipo: 'GENERICO', mensagem: 'Não foi possível conectar ao servidor. Tente novamente.' }
  }
  const { status, data } = error.response
  const mensagem: string = data?.mensagem || data?.detail || 'Não foi possível registrar a validação.'
  const validacao: ValidacaoRegistrada | null =
    data?.dados && typeof data.dados === 'object' && 'aprovada' in data.dados ? data.dados : null

  if (status === 403) return { tipo: 'SEM_PERMISSAO', mensagem }
  if (status === 409 || /j[áa] (foi )?respond/i.test(mensagem)) {
    return { tipo: 'JA_RESPONDIDA', mensagem, validacao }
  }
  if (/aguardando|status/i.test(mensagem)) return { tipo: 'STATUS_INVALIDO', mensagem }
  return { tipo: 'GENERICO', mensagem }
}