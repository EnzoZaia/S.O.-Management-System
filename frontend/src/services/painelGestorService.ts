import axios from 'axios'
import api from '@/services/api'
import type { ErroPainel, IndicadoresGestor, OrdemPainel, PeriodoPainel } from '@/types/painelGestor'
import { normalizarIndicadores } from '@/utils/painelGestor'

export class PainelGestorError extends Error {
  info: ErroPainel
  constructor(info: ErroPainel) {
    super(info.mensagem)
    this.info = info
  }
}

function normalizarErro(error: unknown): ErroPainel {
  if (!axios.isAxiosError(error) || !error.response) {
    return { tipo: 'GENERICO', mensagem: 'Não foi possível conectar ao servidor. Tente novamente.' }
  }
  const { status, data } = error.response
  const mensagem: string = data?.mensagem || data?.detail || 'Não foi possível carregar o painel.'
  if (status === 401 || status === 403) return { tipo: 'SEM_PERMISSAO', mensagem }
  return { tipo: 'GENERICO', mensagem }
}

/** CA1/CA3: o backend já devolve só os dados do escopo do gestor autenticado. */
export async function buscarIndicadores(periodo: PeriodoPainel): Promise<IndicadoresGestor> {
  const { data } = await api.get('/ordem-servico/dashboard/indicadores/', { params: { periodo } })
  return normalizarIndicadores(data?.dados ?? data)
}

/** Ordens do escopo do gestor (as dele + a fila de triagem): base dos gargalos e do histórico. */
export async function listarOrdensDoEscopo(): Promise<OrdemPainel[]> {
  const { data } = await api.get('/ordem-servico/')
  return (data?.dados || data || []) as OrdemPainel[]
}

/** CA2: cada chamada lê o estado persistido; a tela repete a chamada periodicamente. */
export async function carregarPainel(periodo: PeriodoPainel) {
  try {
    const [indicadores, ordens] = await Promise.all([buscarIndicadores(periodo), listarOrdensDoEscopo()])
    return { indicadores, ordens }
  } catch (e) {
    throw new PainelGestorError(normalizarErro(e))
  }
}