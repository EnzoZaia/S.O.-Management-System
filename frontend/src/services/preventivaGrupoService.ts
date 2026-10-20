import axios from 'axios'
import api from '@/services/api'
import type { DadosGerarOrdem, ErroGrupo, GrupoPreventiva, ResultadoItemEnvio } from '@/types/preventivaGrupo'

export class PreventivaGrupoError extends Error {
  info: ErroGrupo
  constructor(info: ErroGrupo) {
    super(info.mensagem)
    this.info = info
  }
}

function normalizarErro(error: unknown): ErroGrupo {
  if (!axios.isAxiosError(error) || !error.response) {
    return { tipo: 'GENERICO', mensagem: 'Não foi possível conectar ao servidor. Tente novamente.' }
  }
  const { status, data } = error.response
  const mensagem: string = data?.mensagem || data?.detail || 'Não foi possível concluir a operação.'

  if (status === 403) return { tipo: 'FORA_ESCOPO', mensagem }
  if (status === 404 || status === 405 || status === 501) return { tipo: 'INDISPONIVEL', mensagem }
  if (status === 409) return { tipo: 'STATUS_INVALIDO', mensagem }
  if (/mesmo pr[ée]dio/i.test(mensagem)) return { tipo: 'MESMO_PREDIO', mensagem }
  if (status === 400 && data?.erros) return { tipo: 'VALIDACAO', mensagem }
  return { tipo: 'GENERICO', mensagem }
}

const lista = <T>(data: any): T[] => data?.dados || data || []

export async function carregarDadosPainel() {
  const [ativos, predios, locs, grupos] = await Promise.all([
    api.get('/ativo/'),
    api.get('/predio/'),
    api.get('/localizacao/'),
    listarGrupos(),
  ])
  return { ativos: lista<any>(ativos.data), predios: lista<any>(predios.data), localizacoes: lista<any>(locs.data), grupos }
}

/** Tolerante: enquanto o backend não expõe as ordens agrupadas, o painel funciona sem elas. */
export async function listarGrupos(): Promise<GrupoPreventiva[]> {
  try {
    const { data } = await api.get('/ordem-servico/preventivas-agrupadas/')
    return lista<GrupoPreventiva>(data)
  } catch {
    return []
  }
}

export async function listarTecnicos(): Promise<any[]> {
  try {
    const { data } = await api.get('/usuario/')
    return lista<any>(data).filter((u) => u.grupo_descricao === 'TECNICO')
  } catch {
    return []
  }
}

/** CA3: um único POST cria uma OS (um código) e vincula todos os ativos. */
export async function gerarOrdemAgrupada(dados: DadosGerarOrdem): Promise<{ id_ordem_servico?: number }> {
  try {
    const { data } = await api.post('/ordem-servico/preventivas-agrupadas/', dados)
    return data?.dados ?? {}
  } catch (e) {
    throw new PreventivaGrupoError(normalizarErro(e))
  }
}

/** CA4: o backend encerra a OS quando todos os itens têm resultado. */
export async function registrarResultados(idOrdem: number, itens: ResultadoItemEnvio[]) {
  try {
    const { data } = await api.patch(`/ordem-servico/preventivas-agrupadas/${idOrdem}/resultados/`, { itens })
    return data?.dados ?? {}
  } catch (e) {
    throw new PreventivaGrupoError(normalizarErro(e))
  }
}