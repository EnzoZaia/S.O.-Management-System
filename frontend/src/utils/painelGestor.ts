import type {
  CategoriaGargalo,
  GargaloOrdem,
  IndicadoresGestor,
  OrdemPainel,
  PeriodoPainel,
  ResumoGargalos,
} from '@/types/painelGestor'

const MS_DIA = 86_400_000
export const STATUS_RESOLVIDOS = ['CONCLUIDA', 'ENCERRADA']

export const PERIODOS: { valor: PeriodoPainel; rotulo: string }[] = [
  { valor: '30d', rotulo: 'Últimos 30 Dias' },
  { valor: 'mes_atual', rotulo: 'Este Mês' },
  { valor: 'mes_passado', rotulo: 'Mês Passado' },
  { valor: 'ano', rotulo: 'Este Ano' },
]

export const CATEGORIAS_GARGALO: { valor: CategoriaGargalo; rotulo: string; cor: string; classes: string }[] = [
  { valor: 'SEM_TRIAGEM', rotulo: 'Sem triagem', cor: '#f97316', classes: 'bg-orange-100 text-orange-700 border-orange-200' },
  { valor: 'SEM_TECNICO', rotulo: 'Sem técnico', cor: '#ef4444', classes: 'bg-red-100 text-red-700 border-red-200' },
  { valor: 'AGUARDANDO_MATERIAL', rotulo: 'Aguardando material', cor: '#eab308', classes: 'bg-yellow-100 text-yellow-700 border-yellow-200' },
  { valor: 'AGUARDANDO_TERCEIRO', rotulo: 'Dependente de terceiro', cor: '#a855f7', classes: 'bg-purple-100 text-purple-700 border-purple-200' },
]

const num = (v: unknown): number => {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

/** Aceita o payload cru do backend e devolve um objeto completo e tipado, sem campos faltando. */
export function normalizarIndicadores(bruto: any): IndicadoresGestor {
  const d = bruto ?? {}
  const status: Record<string, number> = {}
  for (const [chave, valor] of Object.entries(d.statusDetalhados ?? {})) status[chave] = num(valor)
  const p = d.pendencias ?? {}
  const t = d.tipo_manutencao ?? {}
  return {
    totalOrdens: num(d.totalOrdens),
    abertas: num(d.abertas),
    concluidas: num(d.concluidas),
    aguardandoValidacao: num(d.aguardandoValidacao),
    tempoMedio: typeof d.tempo_medio === 'string' ? d.tempo_medio : '0d',
    statusDetalhados: status,
    tipoManutencao: { preventiva: num(t.preventiva), corretiva: num(t.corretiva) },
    rankingTecnicos: Array.isArray(d.rankingTecnicos)
      ? d.rankingTecnicos.map((r: any) => ({
          nome: String(r?.nome ?? 'Técnico'),
          total: num(r?.total),
          concluidas: num(r?.concluidas),
          satisfacao_media: r?.satisfacao_media ?? null,
          total_avaliacoes: num(r?.total_avaliacoes),
        }))
      : [],
    satisfacaoMedia: d.satisfacaoMedia ?? null,
    totalAvaliacoes: num(d.totalAvaliacoes),
    pendencias: {
      aguardando_aprovacao: num(p.aguardando_aprovacao),
      aguardando_material: num(p.aguardando_material),
      aguardando_terceiro: num(p.aguardando_terceiro),
      aguardando_validacao: num(p.aguardando_validacao),
      sem_tecnico: num(p.sem_tecnico),
    },
    semanas: Array.isArray(d.semanas)
      ? d.semanas.map((s: any) => ({ label: String(s?.label ?? ''), valor: num(s?.valor) }))
      : [],
  }
}

/** "1.5d" (dias, vindo do backend) -> "36h". */
export function formatarTempoMedio(tempo: string): string {
  if (!tempo || tempo === '0d') return '0h'
  const valor = parseFloat(String(tempo).replace(',', '.').replace(/[^0-9.]/g, ''))
  if (Number.isNaN(valor) || valor === 0) return '0h'
  const horasTotais = valor * 24
  const horas = Math.floor(horasTotais)
  const minutos = Math.round((horasTotais - horas) * 60)
  if (horas === 0) return `${minutos}m`
  if (minutos === 0) return `${horas}h`
  return `${horas}h ${minutos}m`
}

/** Mesma janela usada pelo backend (sobre dt_abertura). */
export function dentroDoPeriodo(iso: string, periodo: PeriodoPainel, agora = new Date()): boolean {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return false
  if (periodo === 'mes_atual') return d.getFullYear() === agora.getFullYear() && d.getMonth() === agora.getMonth()
  if (periodo === 'mes_passado') {
    const ref = new Date(agora.getFullYear(), agora.getMonth() - 1, 1)
    return d.getFullYear() === ref.getFullYear() && d.getMonth() === ref.getMonth()
  }
  if (periodo === 'ano') return d.getFullYear() === agora.getFullYear()
  return d.getTime() >= agora.getTime() - 30 * MS_DIA
}

/** Preventivas x corretivas realmente resolvidas no período (a base é a lista já filtrada pelo backend). */
export function contarResolvidasPorTipo(ordens: OrdemPainel[], periodo: PeriodoPainel) {
  const r = { preventiva: 0, corretiva: 0 }
  for (const o of ordens) {
    if (!STATUS_RESOLVIDOS.includes(o.status_ordem_servico)) continue
    if (!dentroDoPeriodo(o.dt_abertura, periodo)) continue
    if (o.tipo_manutencao === 'PREVENTIVA') r.preventiva++
    else r.corretiva++
  }
  return r
}

export function percentualPreventiva(preventiva: number, corretiva: number): number {
  const total = preventiva + corretiva
  return total === 0 ? 0 : Math.round((preventiva / total) * 100)
}

export function distribuicaoStatus(ind: IndicadoresGestor) {
  const s = ind.statusDetalhados
  const v = (k: string) => s[k] ?? 0
  return [
    { chave: 'ABERTA', rotulo: 'Pendentes de Triagem', quantidade: v('ABERTA'), barra: 'bg-gradient-to-r from-blue-400 to-blue-500', texto: 'text-blue-600' },
    { chave: 'APROVADA', rotulo: 'Aprovadas / Sem Iniciar', quantidade: v('APROVADA'), barra: 'bg-gradient-to-r from-emerald-400 to-emerald-500', texto: 'text-emerald-600' },
    { chave: 'EM_EXECUCAO', rotulo: 'Trabalho em Execução', quantidade: v('EM_EXECUCAO'), barra: 'bg-gradient-to-r from-yellow-400 to-yellow-500', texto: 'text-yellow-600' },
    { chave: 'PAUSADAS', rotulo: 'Pausadas (Material/Terceiros)', quantidade: v('AGUARDANDO_MATERIAL') + v('AGUARDANDO_TERCEIRO'), barra: 'bg-gradient-to-r from-orange-400 to-orange-500', texto: 'text-orange-600' },
    { chave: 'VALIDACAO', rotulo: 'Aguardando Validação', quantidade: v('AGUARDANDO_VALIDACAO'), barra: 'bg-gradient-to-r from-indigo-400 to-indigo-500', texto: 'text-indigo-600' },
    { chave: 'CONCLUIDAS', rotulo: 'Sucesso (Concluídas)', quantidade: v('CONCLUIDA') + v('ENCERRADA'), barra: 'bg-gradient-to-r from-teal-400 to-teal-500', texto: 'text-teal-600' },
    { chave: 'CANCELADAS', rotulo: 'Canceladas / Reprovadas', quantidade: v('CANCELADA') + v('REPROVADA'), barra: 'bg-gradient-to-r from-red-400 to-red-500', texto: 'text-red-600' },
  ]
}

function categoriaDoGargalo(o: OrdemPainel): CategoriaGargalo | null {
  switch (o.status_ordem_servico) {
    case 'ABERTA': return 'SEM_TRIAGEM'
    case 'APROVADA': return o.tecnico ? null : 'SEM_TECNICO'
    case 'AGUARDANDO_MATERIAL': return 'AGUARDANDO_MATERIAL'
    case 'AGUARDANDO_TERCEIRO': return 'AGUARDANDO_TERCEIRO'
    default: return null
  }
}

/** CA4: ordens bloqueadas, mais urgentes e mais antigas primeiro. É a situação atual, independe do período. */
export function calcularGargalos(ordens: OrdemPainel[], agora = Date.now()): GargaloOrdem[] {
  const lista: GargaloOrdem[] = []
  for (const ordem of ordens) {
    const categoria = categoriaDoGargalo(ordem)
    if (!categoria) continue
    const aberta = new Date(ordem.dt_abertura).getTime()
    const dias = Number.isNaN(aberta) ? 0 : Math.max(0, Math.floor((agora - aberta) / MS_DIA))
    lista.push({ ordem, categoria, diasEmAberto: dias })
  }
  return lista.sort((a, b) => {
    const urg = Number(b.ordem.prioridade_urgencia === 'SIM') - Number(a.ordem.prioridade_urgencia === 'SIM')
    return urg || b.diasEmAberto - a.diasEmAberto
  })
}

export function resumirGargalos(gargalos: GargaloOrdem[]): ResumoGargalos {
  const r: ResumoGargalos = { SEM_TRIAGEM: 0, SEM_TECNICO: 0, AGUARDANDO_MATERIAL: 0, AGUARDANDO_TERCEIRO: 0 }
  for (const g of gargalos) r[g.categoria]++
  return r
}

export interface ResolucaoHistorico {
  ordem: OrdemPainel
  concluidaEm: string
  duracaoMs: number
}

/** Histórico de resoluções: ordens concluídas/encerradas, da mais recente para a mais antiga. */
export function historicoResolucoes(ordens: OrdemPainel[]): ResolucaoHistorico[] {
  const lista: ResolucaoHistorico[] = []
  for (const ordem of ordens) {
    if (!STATUS_RESOLVIDOS.includes(ordem.status_ordem_servico)) continue
    const fim = ordem.dt_conclusao
    if (!fim) continue
    const duracao = Date.parse(fim) - Date.parse(ordem.dt_abertura)
    lista.push({ ordem, concluidaEm: fim, duracaoMs: Number.isNaN(duracao) ? 0 : Math.max(0, duracao) })
  }
  return lista.sort((a, b) => Date.parse(b.concluidaEm) - Date.parse(a.concluidaEm))
}