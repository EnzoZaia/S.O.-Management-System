import axios from 'axios'
import api from '@/services/api'
import type { ErroEvidencia, EvidenciaOrdem } from '@/types/portal'

export class EvidenciaError extends Error {
  info: ErroEvidencia
  constructor(info: ErroEvidencia) {
    super(info.mensagem)
    this.info = info
  }
}

function normalizarErroEvidencia(error: unknown): ErroEvidencia {
  if (!axios.isAxiosError(error) || !error.response) {
    return { tipo: 'GENERICO', mensagem: 'Não foi possível conectar ao servidor. Tente novamente.' }
  }
  const { status, data } = error.response
  const mensagem: string = data?.mensagem || data?.detail || 'Não foi possível enviar a evidência.'
  if (status === 403) return { tipo: 'SEM_PERMISSAO', mensagem }
  if (status === 409) return { tipo: 'STATUS_INVALIDO', mensagem }
  if (status === 400 || status === 413) return { tipo: 'ARQUIVO_INVALIDO', mensagem }
  return { tipo: 'GENERICO', mensagem }
}

// CA4: lista as evidências com autoria, em ordem de envio.
export async function listarEvidencias(idOrdem: number): Promise<EvidenciaOrdem[]> {
  const { data } = await api.get(`/ordem-servico/${idOrdem}/evidencias/`)
  const lista: EvidenciaOrdem[] = data?.dados || data || []
  return [...lista].sort((a, b) => a.ordem - b.ordem)
}

// CA1: envia um ou mais arquivos; o servidor define ordem, autor e data/hora.
export async function enviarEvidencias(idOrdem: number, arquivos: File[]): Promise<EvidenciaOrdem[]> {
  const form = new FormData()
  arquivos.forEach((arq) => form.append('arquivos', arq))
  try {
    const { data } = await api.post(`/ordem-servico/${idOrdem}/evidencias/`, form)
    return (data?.dados ?? []) as EvidenciaOrdem[]
  } catch (e) {
    throw new EvidenciaError(normalizarErroEvidencia(e))
  }
}