import type {
  ChaveIndicador,
  IndicadoresGlobais,
  ItemDistribuicao,
  PeriodoGlobal,
  PredioOcorrencias,
} from '@/types/indicadoresGlobais'
import { PERIODOS } from '@/utils/painelGestor'
import { formatarDuracao } from '@/utils/apontamentoTempo'
import { parseDataLocal } from '@/utils/painelPreventivas'

export const TOP_DISTRIBUICAO = 10

export const PERIODOS_GLOBAIS: { valor: PeriodoGlobal; rotulo: string }[] = [
  ...PERIODOS,
  { valor: 'personalizado', rotulo: 'Personalizado' },
]

/** CA3: fórmulas documentadas (o cálculo é do backend; a tela só as exibe). */
export const DOCUMENTACAO_INDICADORES: { chave: ChaveIndicador; titulo: string; formula: string }[] = [
  {
    chave: 'backlog',
    titulo: 'Backlog ativo',
    formula: 'Quantidade de ordens do período ainda em andamento (status ativos: triagem, aprovada, em execução, pausadas e aguardando validação).',
  },
  {
    chave: 'mttr',
    titulo: 'MTTR (tempo médio de resolução)',
    formula: 'Média de (data de conclusão − data de abertura) das ordens corretivas resolvidas no período.',
  },
  {
    chave: 'primeiraIntervencao',
    titulo: 'Resolução na primeira intervenção',
    formula: 'Corretivas resolvidas sem nenhuma reprovação do solicitante ÷ total de corretivas resolvidas no período × 100.',
  },
  {
    chave: 'satisfacao',
    titulo: 'Satisfação',
    formula: 'Média das notas (1 a 5) das avaliações registradas para ordens do período.',
  },
  {
    chave: 'reincidencia',
    titulo: 'Reincidência',
    formula: 'Corretivas abertas para um ativo que já teve outra corretiva resolvida nos 30 dias anteriores ÷ total de corretivas do período × 100.',
  },
  {
    chave: 'afetados',
    titulo: 'Usuários afetados',
    formula: 'Pessoas distintas vinculadas às ordens do período (solicitante + "eu também presenciei"); cada pessoa conta uma única vez por ordem.',
  },
]

export function formulaDe(chave: ChaveIndicador): string {
  return DOCUMENTACAO_INDICADORES.find((d) => d.chave === chave)?.formula ?? ''
}

const num = (v: unknown): number => {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

const numOuNulo = (v: unknown): number | null => {
  if (v === null || v === undefined || v === '') return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

const ordenar = <T extends { total: number }>(lista: T[]) => [...lista].sort((a, b) => b.total - a.total)

function normalizarDistribuicao(lista: unknown, montar: (r: any, i: number) => ItemDistribuicao): ItemDistribuicao[] {
  if (!Array.isArray(lista)) return []
  return ordenar(lista.map(montar)).slice(0, TOP_DISTRIBUICAO)
}

const ROTULO_TIPO_ATIVO: Record<string, string> = { AR_CONDICIONADO: 'Ar-condicionado', BEBEDOURO: 'Bebedouro' }

/** Data local (AAAA-MM-DD) de um instante ISO; `fimExclusivo` volta um dia quando o limite cai à meia-noite. */
function dataLocal(iso: unknown, fimExclusivo = false): string | null {
  if (typeof iso !== 'string' || !iso) return null
  if (iso.length <= 10) return iso
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  if (fimExclusivo && d.getHours() === 0 && d.getMinutes() === 0 && d.getSeconds() === 0) d.setDate(d.getDate() - 1)
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mes}-${dia}`
}

const primeiro = (...valores: unknown[]) => valores.find((v) => v !== undefined && v !== null)

/** Aceita o payload de GET /ordem-servico/indicadores-gerenciais/ e devolve um objeto completo e tipado. */
export function normalizarIndicadoresGlobais(bruto: any): IndicadoresGlobais {
  const d = bruto ?? {}

  const listaPredios = d.predios_mais_ocorrencias ?? d.por_predio
  const porPredio: PredioOcorrencias[] = Array.isArray(listaPredios)
    ? listaPredios
        .map((r: any, i: number) => ({
          chave: r?.id_predio ?? i,
          nome: String(r?.predio_nome ?? r?.nome_predio ?? r?.nome ?? 'Prédio'),
          totalOcorrencias: num(r?.total_ocorrencias ?? r?.total),
          totalAfetados: num(r?.total_afetados),
        }))
        .sort((a: PredioOcorrencias, b: PredioOcorrencias) => b.totalOcorrencias - a.totalOcorrencias)
    : []

  const afetados = primeiro(d.usuarios_afetados, d.total_afetados)

  return {
    intervalo: { inicio: dataLocal(d.periodo?.inicio), fim: dataLocal(d.periodo?.fim, true) },
    totalOrdens: num(primeiro(d.volume_total, d.total_ordens)),
    backlogAtivo: num(d.backlog_ativo),
    mttrHoras: numOuNulo(d.mttr_horas),
    resolucaoPrimeiraIntervencao: numOuNulo(primeiro(d.taxa_resolucao_primeira_intervencao, d.resolucao_primeira_intervencao)),
    satisfacaoMedia: numOuNulo(d.satisfacao_media),
    totalAvaliacoes: num(d.total_avaliacoes),
    reincidencia: numOuNulo(primeiro(d.taxa_reincidencia, d.reincidencia)),
    totalAfetados: afetados !== undefined
      ? num(afetados)
      : porPredio.reduce((soma, p) => soma + p.totalAfetados, 0),
    porAtivo: normalizarDistribuicao(d.distribuicao_por_ativo ?? d.por_ativo, (r, i) => ({
      chave: r?.id_ativo ?? r?.codigo_patrimonial ?? i,
      rotulo: String(r?.nome ?? ROTULO_TIPO_ATIVO[r?.tipo_ativo] ?? r?.codigo_patrimonial ?? 'Ativo'),
      detalhe: r?.codigo_patrimonial ? `PAT: ${r.codigo_patrimonial}` : null,
      total: num(r?.total),
    })),
    porLocalizacao: normalizarDistribuicao(d.distribuicao_por_localizacao ?? d.por_localizacao, (r, i) => ({
      chave: r?.id_localizacao ?? i,
      rotulo: String(r?.localizacao_nome ?? r?.nome ?? r?.desc_localizacao ?? 'Local'),
      detalhe: r?.predio_nome ?? null,
      total: num(r?.total),
    })),
    porPredio,
  }
}

export function formatarPercentual(valor: number | null): string {
  return valor === null ? '—' : `${valor.toFixed(1).replace('.', ',')}%`
}

export function formatarMttr(horas: number | null): string {
  return horas === null ? '—' : formatarDuracao(horas * 3_600_000)
}

export function formatarSatisfacao(media: number | null, total: number): string {
  return media === null ? '—' : `${media.toFixed(2).replace('.', ',')} / 5 (${total})`
}

export function formatarDataCurta(iso: string | null): string {
  const d = parseDataLocal(iso)
  return d ? d.toLocaleDateString('pt-BR') : '—'
}

function hojeIso(): string {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 10)
}

/** CA1: o intervalo personalizado precisa ser coerente antes de recalcular tudo. */
export function validarIntervalo(inicio: string, fim: string): string | null {
  if (!inicio || !fim) return 'Informe as datas inicial e final.'
  if (inicio > fim) return 'A data inicial não pode ser posterior à data final.'
  if (fim > hojeIso()) return 'A data final não pode estar no futuro.'
  return null
}

export function maiorTotal(itens: { total: number }[]): number {
  return itens.reduce((max, i) => Math.max(max, i.total), 0)
}