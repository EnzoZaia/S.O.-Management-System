import axios from 'axios'
import api from '@/services/api'
import type {
  AtivoChecklist,
  ChecklistOrdem,
  ErroChecklist,
  ItemChecklistEnvio,
  ResultadoAtivoChecklist,
} from '@/types/checklistPreventiva'

export class ChecklistError extends Error {
  info: ErroChecklist
  constructor(info: ErroChecklist) {
    super(info.mensagem)
    this.info = info
  }
}

const base = (idOrdem: number) => `/ordem-servico/preventivas-agrupadas/${idOrdem}`

function normalizarErro(error: unknown): ErroChecklist {
  if (!axios.isAxiosError(error) || !error.response) {
    return { tipo: 'GENERICO', mensagem: 'Não foi possível conectar ao servidor. Tente novamente.' }
  }
  const { status, data } = error.response
  const mensagem: string = (typeof data === 'object' && (data?.mensagem || data?.detail)) || 'Não foi possível concluir a operação.'

  if (status === 403) return { tipo: 'FORA_ESCOPO', mensagem }
  if (status === 404 || status === 405 || status === 501) return { tipo: 'INDISPONIVEL', mensagem }
  if (status === 409) return { tipo: 'STATUS_INVALIDO', mensagem }
  if (status === 400) {
    if (/checklist|incompleto|pendente/i.test(mensagem)) return { tipo: 'CHECKLIST_INCOMPLETO', mensagem }
    return { tipo: 'VALIDACAO', mensagem }
  }
  return { tipo: 'GENERICO', mensagem }
}

/** CA2: checklist digital de cada ativo da ordem agrupada. */
export async function buscarChecklist(idOrdem: number): Promise<ChecklistOrdem> {
  try {
    const { data } = await api.get(`${base(idOrdem)}/checklist/`)
    const dados = data?.dados ?? data ?? {}
    const ativos: AtivoChecklist[] = Array.isArray(dados.ativos) ? dados.ativos : []
    return { id_ordem_servico: idOrdem, ativos }
  } catch (e) {
    throw new ChecklistError(normalizarErro(e))
  }
}

/** Salva as respostas dos itens do ativo (progresso parcial). */
export async function salvarChecklistAtivo(idOrdem: number, ativo: number, itens: ItemChecklistEnvio[]) {
  try {
    await api.patch(`${base(idOrdem)}/ativos/${ativo}/checklist/`, { itens })
  } catch (e) {
    throw new ChecklistError(normalizarErro(e))
  }
}

/** CA4: o backend encerra a ordem quando o último ativo recebe resultado. */
export async function registrarResultadoAtivo(
  idOrdem: number,
  ativo: number,
  resultado: Exclude<ResultadoAtivoChecklist, 'PENDENTE'>,
  motivo?: string,
): Promise<{ status_ordem_servico?: string }> {
  try {
    const { data } = await api.patch(`${base(idOrdem)}/resultados/`, {
      itens: [{ ativo, resultado, ...(motivo ? { motivo } : {}) }],
    })
    return data?.dados ?? {}
  } catch (e) {
    throw new ChecklistError(normalizarErro(e))
  }
}

/** CA1/CA2: o backend gera o PDF; aqui só baixamos o arquivo. */
export async function baixarGuiaPdf(idOrdem: number): Promise<void> {
  try {
    const resposta = await api.get(`${base(idOrdem)}/guia/`, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([resposta.data], { type: 'application/pdf' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `guia-preventiva-OS-${idOrdem}.pdf`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    throw new ChecklistError(normalizarErro(e))
  }
}