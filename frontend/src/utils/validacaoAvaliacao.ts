import axios from 'axios'
import type { AvaliacaoRegistrada, ErroAvaliacao } from '@/types/portal'

export const NOTA_MIN = 1
export const NOTA_MAX = 5
export const COMENTARIO_MAX = 300

export const ROTULOS_NOTA: Record<number, string> = {
  1: 'Muito ruim',
  2: 'Ruim',
  3: 'Regular',
  4: 'Bom',
  5: 'Excelente',
}

// CA2: a nota é obrigatória e precisa estar entre 1 e 5.
export function validarNota(nota: number | null): string | null {
  if (nota === null || nota === undefined) return 'Selecione uma nota de 1 a 5 estrelas.'
  if (!Number.isInteger(nota) || nota < NOTA_MIN || nota > NOTA_MAX) {
    return `A nota deve ser de ${NOTA_MIN} a ${NOTA_MAX} estrelas.`
  }
  return null
}

// O comentário é opcional; só limita o tamanho.
export function validarComentario(texto: string): string | null {
  if (texto.trim().length > COMENTARIO_MAX) return `Use no máximo ${COMENTARIO_MAX} caracteres.`
  return null
}

export function normalizarErroAvaliacao(error: unknown): ErroAvaliacao {
  if (!axios.isAxiosError(error) || !error.response) {
    return { tipo: 'GENERICO', mensagem: 'Não foi possível conectar ao servidor. Tente novamente.' }
  }
  const { status, data } = error.response
  const mensagem: string = data?.mensagem || data?.detail || 'Não foi possível registrar a avaliação.'
  const avaliacao: AvaliacaoRegistrada | null =
    data?.dados && typeof data.dados === 'object' && 'nota' in data.dados ? data.dados : null

  if (status === 403) return { tipo: 'SEM_PERMISSAO', mensagem }
  // CA3: duplicidade
  if (status === 409 || /j[áa] (foi )?avali/i.test(mensagem)) {
    return { tipo: 'JA_AVALIADA', mensagem, avaliacao }
  }
  if (/aguardando|status|aprova|valida/i.test(mensagem)) return { tipo: 'STATUS_INVALIDO', mensagem }
  return { tipo: 'GENERICO', mensagem }
}