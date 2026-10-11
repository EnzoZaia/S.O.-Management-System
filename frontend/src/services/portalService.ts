import api from '@/services/api'
import type {
  AvaliacaoRegistrada, ErroAvaliacao, ErroValidacao, EventoHistorico, OrdemPortal,
  ResultadoAvaliacao, ResultadoValidacao, ValidacaoRegistrada,
} from '@/types/portal'
import { normalizarErroAvaliacao } from '@/utils/validacaoAvaliacao'
import { normalizarErroValidacao } from '@/utils/validacaoOrdem'

export async function listarMinhasOrdens(): Promise<OrdemPortal[]> {
  const { data } = await api.get('/ordem-servico/')
  const lista: OrdemPortal[] = data?.dados || data || []
  return [...lista].sort(
    (a, b) => new Date(b.dt_abertura).getTime() - new Date(a.dt_abertura).getTime(),
  )
}


export async function buscarHistoricoOrdem(id: number): Promise<EventoHistorico[]> {
  const { data } = await api.get(`/ordem-servico/${id}/historico/`)
  const lista: EventoHistorico[] = data?.dados || data || []
  return [...lista].sort(
    (a, b) => new Date(b.data_registro).getTime() - new Date(a.data_registro).getTime(),
  )
}

export class ValidacaoError extends Error {
  info: ErroValidacao
  constructor(info: ErroValidacao) {
    super(info.mensagem)
    this.info = info
  }
}

export async function buscarOrdem(id: number): Promise<OrdemPortal> {
  const { data } = await api.get(`/ordem-servico/${id}/`)
  return data?.dados || data
}

export async function buscarValidacao(id: number): Promise<ValidacaoRegistrada | null> {
  try {
    const { data } = await api.get(`/ordem-servico/${id}/validacao/`)
    return data?.dados || null
  } catch {
    return null
  }
}

function montarCorpo(r: ResultadoValidacao): FormData | { aprovada: boolean; justificativa?: string } {
  if (!r.evidencias?.length) return { aprovada: r.aprovada, justificativa: r.justificativa }
  const form = new FormData()
  form.append('aprovada', String(r.aprovada))
  if (r.justificativa) form.append('justificativa', r.justificativa)
  r.evidencias.forEach((arquivo) => form.append('evidencias', arquivo))
  return form
}

export async function validarOrdem(id: number, resultado: ResultadoValidacao) {
  try {
    const { data } = await api.patch(`/ordem-servico/${id}/validar/`, montarCorpo(resultado))
    return (data?.dados ?? {}) as { status_ordem_servico?: string; validacao?: ValidacaoRegistrada }
  } catch (e) {
    throw new ValidacaoError(normalizarErroValidacao(e))
  }
}
export class AvaliacaoError extends Error {
  info: ErroAvaliacao
  constructor(info: ErroAvaliacao) {
    super(info.mensagem)
    this.info = info
  }
}

/** Retorna a avaliação já registrada para a ordem, ou null se ainda não existe. */
export async function buscarAvaliacao(id: number): Promise<AvaliacaoRegistrada | null> {
  try {
    const { data } = await api.get(`/ordem-servico/${id}/avaliacao/`)
    return data?.dados || null
  } catch {
    return null
  }
}

/** CA1: registra a avaliação; o backend encerra a ordem na mesma operação. */
export async function enviarAvaliacao(id: number, resultado: ResultadoAvaliacao) {
  try {
    const { data } = await api.post(`/ordem-servico/${id}/avaliar/`, {
      nota: resultado.nota,
      comentario: resultado.comentario,
    })
    return (data?.dados ?? {}) as { status_ordem_servico?: string; avaliacao?: AvaliacaoRegistrada }
  } catch (e) {
    throw new AvaliacaoError(normalizarErroAvaliacao(e))
  }
}