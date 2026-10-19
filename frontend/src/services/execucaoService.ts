import axios from 'axios'
import api from '@/services/api'
import type {
  DadosConclusao,
  DadosPausa,
  ErroExecucao,
  EventoStatus,
  RespostaExecucao,
} from '@/types/execucao'

export class ExecucaoError extends Error {
  info: ErroExecucao
  constructor(info: ErroExecucao) {
    super(info.mensagem)
    this.info = info
  }
}

function primeiro(valor: unknown): string {
  return Array.isArray(valor) ? String(valor[0] ?? '') : String(valor ?? '')
}

function normalizarErroExecucao(error: unknown): ErroExecucao {
  if (!axios.isAxiosError(error) || !error.response) {
    return { tipo: 'GENERICO', mensagem: 'Não foi possível conectar ao servidor. Tente novamente.', campos: {} }
  }
  const { status, data } = error.response
  const mensagem: string = data?.mensagem || data?.detail || 'Não foi possível registrar a operação.'

  // O técnico só enxerga as ordens atribuídas a ele: fora do escopo o backend devolve 404/403.
  if (status === 403 || status === 404) return { tipo: 'FORA_ESCOPO', mensagem, campos: {} }

  const erros = data?.erros
  if (erros && typeof erros === 'object') {
    const campos: ErroExecucao['campos'] = {}
    if (erros.causa_raiz) campos.causaRaiz = primeiro(erros.causa_raiz)
    if (erros.observacao) campos.observacao = primeiro(erros.observacao)
    if (Object.keys(campos).length) return { tipo: 'VALIDACAO', mensagem, campos }
  }

  if (/n[ãa]o pode mais ser alterada|status/i.test(mensagem)) return { tipo: 'STATUS_INVALIDO', mensagem, campos: {} }
  return { tipo: 'GENERICO', mensagem, campos: {} }
}

async function alterarStatus(idOrdem: number, corpo: Record<string, unknown>): Promise<RespostaExecucao | null> {
  try {
    const { data } = await api.patch(`/ordem-servico/${idOrdem}/`, corpo)
    return (data?.dados ?? null) as RespostaExecucao | null
  } catch (e) {
    throw new ExecucaoError(normalizarErroExecucao(e))
  }
}

/** CA1: o backend registra a data/hora da mudança para EM_EXECUCAO no histórico (início do apontamento). */
export function iniciarExecucao(idOrdem: number, retomada = false) {
  return alterarStatus(idOrdem, {
    status_ordem_servico: 'EM_EXECUCAO',
    observacao: retomada ? 'Técnico retomou o serviço.' : 'Técnico iniciou o serviço.',
  })
}

/** CA2: o status de pausa + o motivo no histórico delimitam o período de pausa. */
export function pausarExecucao(idOrdem: number, dados: DadosPausa) {
  return alterarStatus(idOrdem, { status_ordem_servico: dados.motivo, observacao: dados.detalhe.trim() })
}

/** CA4: o backend leva a corretiva para AGUARDANDO_VALIDACAO (ou CONCLUIDA se ninguém puder validar). */
export function concluirExecucao(idOrdem: number, dados: DadosConclusao) {
  const corpo: Record<string, unknown> = { status_ordem_servico: 'CONCLUIDA', observacao: dados.observacao }
  if (dados.causaRaiz) corpo.causa_raiz = dados.causaRaiz
  if (dados.idAtivo !== undefined) corpo.ativo = dados.idAtivo
  return alterarStatus(idOrdem, corpo)
}

export async function buscarEventosOrdem(idOrdem: number): Promise<EventoStatus[]> {
  const { data } = await api.get(`/ordem-servico/${idOrdem}/historico/`)
  const lista: EventoStatus[] = data?.dados || data || []
  return [...lista].sort((a, b) => Date.parse(a.data_registro) - Date.parse(b.data_registro))
}