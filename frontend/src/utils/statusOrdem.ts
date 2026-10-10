import type { EventoHistorico, FiltroStatusPortal, InfoStatus, OrdemPortal } from '@/types/portal'


const STATUS: Record<string, InfoStatus> = {
  ABERTA: {
    rotulo: 'Solicitada',
    descricao: 'Recebemos sua solicitação e ela aguarda análise do gestor.',
    icone: '📨',
    classes: 'bg-slate-100 text-slate-700 border-slate-200',
    ponto: 'bg-slate-400',
  },
  APROVADA: {
    rotulo: 'Aprovada',
    descricao: 'Sua solicitação foi aprovada e aguarda o início do atendimento.',
    icone: '✅',
    classes: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    ponto: 'bg-emerald-500',
  },
  REPROVADA: {
    rotulo: 'Reprovada',
    descricao: 'Sua solicitação não foi aprovada pelo gestor.',
    icone: '🚫',
    classes: 'bg-red-100 text-red-700 border-red-200',
    ponto: 'bg-red-500',
  },
  EM_EXECUCAO: {
    rotulo: 'Em atendimento',
    descricao: 'Um técnico está executando o serviço.',
    icone: '🔧',
    classes: 'bg-amber-100 text-amber-700 border-amber-200',
    ponto: 'bg-amber-500',
  },
  AGUARDANDO_MATERIAL: {
    rotulo: 'Aguardando material',
    descricao: 'O atendimento está pausado até a chegada de material.',
    icone: '📦',
    classes: 'bg-orange-100 text-orange-700 border-orange-200',
    ponto: 'bg-orange-500',
  },
  AGUARDANDO_TERCEIRO: {
    rotulo: 'Aguardando terceiro',
    descricao: 'O atendimento depende de uma empresa ou fornecedor externo.',
    icone: '🏢',
    classes: 'bg-purple-100 text-purple-700 border-purple-200',
    ponto: 'bg-purple-500',
  },
  AGUARDANDO_VALIDACAO: {
    rotulo: 'Aguardando sua validação',
    descricao: 'O serviço foi executado. Confirme se o problema foi resolvido.',
    icone: '📝',
    classes: 'bg-blue-100 text-blue-700 border-blue-200',
    ponto: 'bg-blue-500',
  },
  CONCLUIDA: {
    rotulo: 'Concluída',
    descricao: 'O serviço foi concluído.',
    icone: '🎉',
    classes: 'bg-teal-100 text-teal-700 border-teal-200',
    ponto: 'bg-teal-500',
  },
  ENCERRADA: {
    rotulo: 'Encerrada',
    descricao: 'A ordem foi encerrada.',
    icone: '📁',
    classes: 'bg-gray-100 text-gray-600 border-gray-200',
    ponto: 'bg-gray-400',
  },
  CANCELADA: {
    rotulo: 'Cancelada',
    descricao: 'A ordem foi cancelada.',
    icone: '❌',
    classes: 'bg-red-100 text-red-700 border-red-200',
    ponto: 'bg-red-400',
  },
}

const PADRAO: InfoStatus = {
  rotulo: 'Em análise',
  descricao: 'Situação em atualização.',
  icone: '⏳',
  classes: 'bg-gray-100 text-gray-500 border-gray-200',
  ponto: 'bg-gray-400',
}

export function infoStatus(status?: string): InfoStatus {
  return (status && STATUS[status]) || PADRAO
}

export const STATUS_FINALIZADOS = ['CONCLUIDA', 'ENCERRADA', 'CANCELADA', 'REPROVADA']

export function ehFinalizada(os: Pick<OrdemPortal, 'status_ordem_servico'>): boolean {
  return STATUS_FINALIZADOS.includes(os.status_ordem_servico)
}

export function pertenceAoFiltro(os: OrdemPortal, filtro: FiltroStatusPortal): boolean {
  if (filtro === 'TODOS') return true
  if (filtro === 'AGUARDANDO_VOCE') return os.status_ordem_servico === 'AGUARDANDO_VALIDACAO'
  if (filtro === 'FINALIZADAS') return ehFinalizada(os)
  return !ehFinalizada(os) && os.status_ordem_servico !== 'AGUARDANDO_VALIDACAO'
}


export function nomeTecnico(os: OrdemPortal): string | null {
  if (!os.tecnico) return null
  const nome = os.tecnico_nome?.trim()
  return nome && nome !== 'Não atribuído' ? nome : null
}


export function acoesPermitidas(os: Pick<OrdemPortal, 'status_ordem_servico'>) {
  const s = os.status_ordem_servico
  return {
    validar: s === 'AGUARDANDO_VALIDACAO',
    evidencia: ['APROVADA', 'EM_EXECUCAO', 'AGUARDANDO_MATERIAL', 'AGUARDANDO_TERCEIRO', 'AGUARDANDO_VALIDACAO'].includes(s),
    avaliar: s === 'CONCLUIDA' || s === 'ENCERRADA',
  }
}

export function extrairProblema(descricao?: string): string {
  if (!descricao) return 'Sem descrição detalhada.'
  return descricao.replace(/\[.*?\]\s*(-\s*Local:.*?\s*)?-\s*(Problema:\s*)?/, '').trim()
}


export function formatarEvento(evento: EventoHistorico): { principal: string; detalhe: string } {
  const texto = String(evento.desc_historico || '').trim()
  const m = texto.match(/(.*?)(?:Detalhes:|Justificativa:)(.*)/i)
  const principal = (m?.[1] ?? texto).trim()
  const detalhe = m?.[2]?.trim() ?? ''

  const traduzido = principal.replace(/Status alterado:\s*(\w+)\s*->\s*(\w+)\.?/, (_, de: string, para: string) => {
    return `Status alterado de "${infoStatus(de).rotulo}" para "${infoStatus(para).rotulo}".`
  })
  return { principal: traduzido || 'Atualização registrada.', detalhe }
}

export function formatarData(iso?: string | null): string {
  if (!iso) return 'N/I'
  return new Date(iso).toLocaleDateString('pt-BR')
}

export function formatarDataHora(iso?: string | null): string {
  if (!iso) return 'N/I'
  const d = new Date(iso)
  return `${d.toLocaleDateString('pt-BR')} às ${d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`
}

export function podeTerValidacao(os: Pick<OrdemPortal, 'status_ordem_servico' | 'tipo_manutencao'>): boolean {
  if ((os.tipo_manutencao || 'CORRETIVA').toUpperCase() !== 'CORRETIVA') return false
  return !['ABERTA', 'APROVADA', 'REPROVADA', 'CANCELADA', 'AGUARDANDO_VALIDACAO'].includes(os.status_ordem_servico)
}