import axios from 'axios'
import api from '@/services/api'
import type { ConsultaIndicadores } from '@/types/indicadoresGlobais'

export type TipoErroIA = 'SEM_ACESSO' | 'INDISPONIVEL' | 'VALIDACAO' | 'GENERICO'

export interface ErroIA {
  tipo: TipoErroIA
  mensagem: string
}

export class InteligenciaError extends Error {
  info: ErroIA
  constructor(info: ErroIA) {
    super(info.mensagem)
    this.info = info
  }
}

export interface ManualBase {
  id_manual: number
  titulo: string
  versao: string | null
  conteudo_lido: boolean
}

export interface RespostaAssistente {
  pergunta: string
  resposta: string
  aviso: string | null
  modelo: string
  dt_consulta: string
  base_conhecimento: {
    possui_manual: boolean
    manuais: ManualBase[]
    equipamento: { tipo: string; marca: string | null; modelo: string | null; codigo_patrimonial: string } | null
  }
}

export interface AnaliseIntelligence {
  id_insight: number
  periodo: { rotulo: string; inicio: string; fim: string }
  indicadores_usados: {
    indicadores: Record<string, number | null>
    predios_mais_ocorrencias: { predio: string; total: number }[]
    ocorrencias_por_tipo_de_ativo: Record<string, number>
  }
  analise: string
  modelo: string
  gerado_em: string
}

function normalizarErro(error: unknown, padrao: string): ErroIA {
  if (!axios.isAxiosError(error) || !error.response) {
    if (axios.isAxiosError(error) && error.code === 'ECONNABORTED') {
      return { tipo: 'INDISPONIVEL', mensagem: 'O serviço de IA demorou demais para responder. Tente novamente.' }
    }
    return { tipo: 'GENERICO', mensagem: 'Não foi possível conectar ao servidor. Tente novamente.' }
  }
  const { status, data } = error.response
  const mensagem: string = data?.mensagem || data?.detail || padrao
  if (status === 401 || status === 403 || status === 404) return { tipo: 'SEM_ACESSO', mensagem }
  if (status === 503 || status === 502 || status === 504) return { tipo: 'INDISPONIVEL', mensagem }
  if (status === 400 && data?.erros) return { tipo: 'VALIDACAO', mensagem }
  return { tipo: 'GENERICO', mensagem }
}

export async function consultarAssistente(idOrdem: number, pergunta: string): Promise<RespostaAssistente> {
  try {
    const { data } = await api.post(`/ordem-servico/${idOrdem}/assistente/`, { pergunta }, { timeout: 120000 })
    return data.dados as RespostaAssistente
  } catch (e) {
    throw new InteligenciaError(normalizarErro(e, 'Não foi possível consultar o assistente.'))
  }
}

export async function gerarAnaliseIntelligence(consulta: ConsultaIndicadores): Promise<AnaliseIntelligence> {
  const corpo = consulta.periodo === 'personalizado'
    ? { inicio: consulta.inicio ?? '', fim: consulta.fim ?? '' }
    : { periodo: consulta.periodo }
  try {
    const { data } = await api.post('/indicadores/intelligence/', corpo, { timeout: 120000 })
    const dados = data?.dados as AnaliseIntelligence | undefined
    if (!dados || typeof dados.analise !== 'string' || !dados.analise.trim()) {
      throw new InteligenciaError({ tipo: 'INDISPONIVEL', mensagem: 'O serviço de IA retornou uma resposta inválida.' })
    }
    return dados
  } catch (e) {
    if (e instanceof InteligenciaError) throw e
    throw new InteligenciaError(normalizarErro(e, 'Não foi possível gerar a análise.'))
  }
}
