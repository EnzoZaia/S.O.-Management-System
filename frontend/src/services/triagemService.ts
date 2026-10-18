import axios from 'axios'
import api from '@/services/api'
import type { DadosTriagem, ErroTriagem } from '@/types/triagem'
import { ROTULO_CATEGORIA } from '@/utils/validacaoTriagem'

export class TriagemError extends Error {
  info: ErroTriagem
  constructor(info: ErroTriagem) {
    super(info.mensagem)
    this.info = info
  }
}

const STATUS_POR_DECISAO = { APROVAR: 'APROVADA', REPROVAR: 'REPROVADA', CANCELAR: 'CANCELADA' } as const

function normalizarErroTriagem(error: unknown): ErroTriagem {
  if (!axios.isAxiosError(error) || !error.response) {
    return { tipo: 'GENERICO', mensagem: 'Não foi possível conectar ao servidor. Tente novamente.', campos: {} }
  }
  const { status, data } = error.response
  const mensagem: string = data?.mensagem || data?.detail || 'Não foi possível registrar a decisão.'

  // CA3: o backend devolve 404 (fora do escopo) ou 403 (sem permissão).
  if (status === 403 || status === 404) return { tipo: 'FORA_ESCOPO', mensagem, campos: {} }

  const erros = data?.erros
  if (erros && typeof erros === 'object') {
    const campos: ErroTriagem['campos'] = {}
    const primeiro = (v: unknown) => (Array.isArray(v) ? String(v[0] ?? '') : String(v ?? ''))
    if (erros.categoria_manutencao) campos.categoria = primeiro(erros.categoria_manutencao)
    if (erros.prioridade_urgencia) campos.prioridade = primeiro(erros.prioridade_urgencia)
    if (erros.status_ordem_servico) campos.decisao = primeiro(erros.status_ordem_servico)
    if (Object.keys(campos).length) return { tipo: 'VALIDACAO', mensagem, campos }
  }

  if (/n[ãa]o pode mais ser alterada|status/i.test(mensagem)) return { tipo: 'STATUS_INVALIDO', mensagem, campos: {} }
  return { tipo: 'GENERICO', mensagem, campos: {} }
}

/** CA1/CA2/CA4: um único PATCH; a "observacao" vira o "Detalhes:" do histórico no backend. */
export async function decidirTriagem(idOrdem: number, dados: DadosTriagem) {
  const corpo: Record<string, string> = { status_ordem_servico: STATUS_POR_DECISAO[dados.decisao] }

  if (dados.decisao === 'APROVAR') {
    corpo.categoria_manutencao = dados.categoria as string
    corpo.prioridade_urgencia = dados.prioridade as string
    corpo.observacao =
      `Triagem aprovada. Categoria: ${ROTULO_CATEGORIA[dados.categoria as string]}; ` +
      `prioridade: ${dados.prioridade === 'SIM' ? 'Urgente' : 'Normal'}.`
  } else {
    corpo.observacao = (dados.justificativa ?? '').trim()
  }

  try {
    const { data } = await api.patch(`/ordem-servico/${idOrdem}/`, corpo)
    return data?.dados ?? null
  } catch (e) {
    throw new TriagemError(normalizarErroTriagem(e))
  }
}