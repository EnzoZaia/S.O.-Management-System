import type { OrdemPainel, PeriodoPainel } from '@/types/painelGestor'
import type { OrdemDaFila, ResumoFila, SituacaoFila, TempoPorTipo } from '@/types/painelTecnico'
import { STATUS_RESOLVIDOS, dentroDoPeriodo } from '@/utils/painelGestor'

const MS_DIA = 86_400_000

const STATUS_PARA_INICIAR = ['APROVADA', 'ATRIBUIDA', 'REABERTA']
const STATUS_PAUSADAS = ['AGUARDANDO_MATERIAL', 'AGUARDANDO_TERCEIRO', 'PAUSADA']

export const SITUACOES_FILA: { valor: SituacaoFila; rotulo: string; cor: string; classes: string }[] = [
  { valor: 'PARA_INICIAR', rotulo: 'Para iniciar', cor: '#10b981', classes: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  { valor: 'EM_EXECUCAO', rotulo: 'Em execução', cor: '#f59e0b', classes: 'bg-amber-100 text-amber-700 border-amber-200' },
  { valor: 'PAUSADA', rotulo: 'Pausadas', cor: '#f97316', classes: 'bg-orange-100 text-orange-700 border-orange-200' },
  { valor: 'AGUARDANDO_VALIDACAO', rotulo: 'Aguardando validação', cor: '#3b82f6', classes: 'bg-blue-100 text-blue-700 border-blue-200' },
]

function situacaoDe(status: string): SituacaoFila | null {
  if (STATUS_PARA_INICIAR.includes(status)) return 'PARA_INICIAR'
  if (status === 'EM_EXECUCAO') return 'EM_EXECUCAO'
  if (STATUS_PAUSADAS.includes(status)) return 'PAUSADA'
  if (status === 'AGUARDANDO_VALIDACAO') return 'AGUARDANDO_VALIDACAO'
  return null
}

/** Ordens do técnico que ainda estão em andamento (a situação atual independe do período). */
export function calcularFilaTecnico(ordens: OrdemPainel[], agora = Date.now()): OrdemDaFila[] {
  const fila: OrdemDaFila[] = []
  for (const ordem of ordens) {
    const situacao = situacaoDe(ordem.status_ordem_servico)
    if (!situacao) continue
    const aberta = new Date(ordem.dt_abertura).getTime()
    const dias = Number.isNaN(aberta) ? 0 : Math.max(0, Math.floor((agora - aberta) / MS_DIA))
    fila.push({ ordem, situacao, diasEmAberto: dias })
  }
  return fila
}

export function resumirFila(fila: OrdemDaFila[]): ResumoFila {
  const r: ResumoFila = { paraIniciar: 0, emExecucao: 0, pausadas: 0, aguardandoValidacao: 0, urgentes: 0, total: fila.length }
  for (const item of fila) {
    if (item.situacao === 'PARA_INICIAR') r.paraIniciar++
    else if (item.situacao === 'EM_EXECUCAO') r.emExecucao++
    else if (item.situacao === 'PAUSADA') r.pausadas++
    else r.aguardandoValidacao++
    if (item.situacao !== 'AGUARDANDO_VALIDACAO' && item.ordem.prioridade_urgencia === 'SIM') r.urgentes++
  }
  return r
}

/** Próximas ordens a atender: urgentes primeiro, depois as mais antigas. Exclui o que já depende do solicitante. */
export function proximasOrdens(fila: OrdemDaFila[], limite = 6): OrdemDaFila[] {
  return fila
    .filter((f) => f.situacao !== 'AGUARDANDO_VALIDACAO')
    .sort((a, b) => {
      const urg = Number(b.ordem.prioridade_urgencia === 'SIM') - Number(a.ordem.prioridade_urgencia === 'SIM')
      return urg || b.diasEmAberto - a.diasEmAberto
    })
    .slice(0, limite)
}

/** Tempo médio de resolução (abertura -> conclusão) das ordens resolvidas no período, por tipo. */
export function tempoMedioPorTipo(ordens: OrdemPainel[], periodo: PeriodoPainel): TempoPorTipo {
  const soma = { CORRETIVA: 0, PREVENTIVA: 0 }
  const qtd = { CORRETIVA: 0, PREVENTIVA: 0 }
  for (const o of ordens) {
    if (!STATUS_RESOLVIDOS.includes(o.status_ordem_servico) || !o.dt_conclusao) continue
    if (!dentroDoPeriodo(o.dt_abertura, periodo)) continue
    const duracao = Date.parse(o.dt_conclusao) - Date.parse(o.dt_abertura)
    if (Number.isNaN(duracao)) continue
    const tipo = o.tipo_manutencao === 'PREVENTIVA' ? 'PREVENTIVA' : 'CORRETIVA'
    soma[tipo] += Math.max(0, duracao)
    qtd[tipo]++
  }
  return {
    corretivaMs: qtd.CORRETIVA ? soma.CORRETIVA / qtd.CORRETIVA : null,
    preventivaMs: qtd.PREVENTIVA ? soma.PREVENTIVA / qtd.PREVENTIVA : null,
    corretivaTotal: qtd.CORRETIVA,
    preventivaTotal: qtd.PREVENTIVA,
  }
}

/** Urgentes resolvidas no período (abertas dentro do período, como no restante do painel). */
export function urgentesResolvidas(ordens: OrdemPainel[], periodo: PeriodoPainel): number {
  return ordens.filter(
    (o) =>
      STATUS_RESOLVIDOS.includes(o.status_ordem_servico) &&
      o.prioridade_urgencia === 'SIM' &&
      dentroDoPeriodo(o.dt_abertura, periodo),
  ).length
}