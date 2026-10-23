import axios from 'axios'
import api from '@/services/api'
import type { ConsultaIndicadores, ErroGlobais, IndicadoresGlobais } from '@/types/indicadoresGlobais'
import { normalizarIndicadoresGlobais } from '@/utils/indicadoresGlobais'

export class IndicadoresGlobaisError extends Error {
  info: ErroGlobais
  constructor(info: ErroGlobais) {
    super(info.mensagem)
    this.info = info
  }
}

function normalizarErro(error: unknown): ErroGlobais {
  if (!axios.isAxiosError(error) || !error.response) {
    return { tipo: 'GENERICO', mensagem: 'Não foi possível conectar ao servidor. Tente novamente.' }
  }
  const { status, data } = error.response
  const mensagem: string = data?.mensagem || data?.detail || 'Não foi possível carregar os indicadores.'

  // CA2: o backend nega quem não tem permissão gerencial.
  if (status === 401 || status === 403) return { tipo: 'SEM_PERMISSAO', mensagem }
  if (status === 404 || status === 405 || status === 501) return { tipo: 'INDISPONIVEL', mensagem }
  if (status === 400 && data?.erros) return { tipo: 'PERIODO_INVALIDO', mensagem }
  return { tipo: 'GENERICO', mensagem }
}

/** CA1: uma única chamada devolve todos os indicadores para o mesmo intervalo. */
export async function buscarIndicadoresGlobais(consulta: ConsultaIndicadores): Promise<IndicadoresGlobais> {
  const params: Record<string, string> = { periodo: consulta.periodo }
  if (consulta.periodo === 'personalizado') {
    params.data_inicio = consulta.inicio ?? ''
    params.data_fim = consulta.fim ?? ''
  }
  try {
    const { data } = await api.get('/ordem-servico/dashboard/indicadores-globais/', { params })
    return normalizarIndicadoresGlobais(data?.dados ?? data)
  } catch (e) {
    throw new IndicadoresGlobaisError(normalizarErro(e))
  }
}