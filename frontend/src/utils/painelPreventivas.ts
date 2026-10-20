import type { AtivoPainel, CardPredio, GrupoPreventiva, ItemGrupo } from '@/types/preventivaGrupo'

export const DIAS_ALERTA = 15
export const STATUS_GRUPO_FECHADO = ['ENCERRADA', 'CANCELADA', 'CONCLUIDA']
const MS_DIA = 86_400_000

export function parseDataLocal(iso?: string | null): Date | null {
  if (!iso) return null
  const d = new Date(`${iso.slice(0, 10)}T12:00:00`)
  return Number.isNaN(d.getTime()) ? null : d
}

export function formatarDataAtivo(iso?: string | null): string {
  const d = parseDataLocal(iso)
  return d ? d.toLocaleDateString('pt-BR') : 'N/I'
}

export function diasPara(iso?: string | null, hoje = new Date()): number | null {
  const d = parseDataLocal(iso)
  return d ? Math.ceil((d.getTime() - hoje.getTime()) / MS_DIA) : null
}

export function grupoAtivo(g: Pick<GrupoPreventiva, 'status_ordem_servico'>): boolean {
  return !STATUS_GRUPO_FECHADO.includes(g.status_ordem_servico)
}

const idDe = (o: any, ...chaves: string[]) => {
  for (const c of chaves) if (o?.[c] !== undefined && o?.[c] !== null) return o[c]
  return undefined
}

/**
 * Monta os cards por prédio. Entram no painel: ativos atrasados, a vencer em até DIAS_ALERTA dias,
 * em execução numa OS agrupada, ou devolvidos como "não concluídos" (CA4).
 */
export function construirPainel(ativos: any[], predios: any[], localizacoes: any[], grupos: GrupoPreventiva[]): CardPredio[] {
  const locPorId = new Map(localizacoes.map((l) => [String(idDe(l, 'id_localizacao', 'id')), l]))
  const prediosPorId = new Map(predios.map((p) => [String(idDe(p, 'id_predio', 'id')), p]))

  const ultimoItem = new Map<number, { item: ItemGrupo; grupo: GrupoPreventiva }>()
  for (const grupo of [...grupos].sort((a, b) => a.id_ordem_servico - b.id_ordem_servico)) {
    for (const item of grupo.itens) ultimoItem.set(item.ativo, { item, grupo })
  }

  const cards = new Map<number, CardPredio>()

  for (const a of ativos) {
    const idAtivo = Number(idDe(a, 'id_ativo', 'id'))
    const loc = locPorId.get(String(idDe(a, 'localizacao', 'id_localizacao', 'localizacao_id')))
    if (!loc) continue
    const idPredio = Number(idDe(loc, 'predio', 'id_predio'))
    const predio = prediosPorId.get(String(idPredio))
    if (!predio) continue

    const ult = ultimoItem.get(idAtivo)
    const emExecucao = !!ult && grupoAtivo(ult.grupo) && ult.item.resultado === 'PENDENTE'
    const devolvido = !!ult && !grupoAtivo(ult.grupo) && ult.item.resultado === 'NAO_CONCLUIDO'
    const dias = diasPara(a.dt_proxima_preventiva)

    let situacao: AtivoPainel['situacao'] | null = null
    if (emExecucao) situacao = 'EM_EXECUCAO'
    else if (dias !== null && dias < 0) situacao = 'ATRASADA'
    else if (devolvido || (dias !== null && dias <= DIAS_ALERTA)) situacao = 'PENDENTE'
    if (!situacao) continue

    const item: AtivoPainel = {
      id_ativo: idAtivo,
      codigo_patrimonial: a.codigo_patrimonial || 'N/I',
      nome: `${a.marca ?? ''} ${a.modelo ?? ''}`.trim() || 'Equipamento',
      localizacao_nome: loc.desc_localizacao || loc.nome || 'N/I',
      id_predio: idPredio,
      dt_ultima_preventiva: a.dt_ultima_preventiva ?? null,
      dt_proxima_preventiva: a.dt_proxima_preventiva ?? null,
      dias,
      situacao,
      motivo_retorno: devolvido ? (ult!.item.motivo ?? null) : null,
      grupo_codigo: emExecucao ? ult!.grupo.id_ordem_servico : null,
    }

    let card = cards.get(idPredio)
    if (!card) {
      card = { id_predio: idPredio, nome_predio: predio.nome_predio || predio.nome, ativos: [], atrasados: 0, pendentes: 0, emExecucao: 0 }
      cards.set(idPredio, card)
    }
    card.ativos.push(item)
    if (situacao === 'ATRASADA') card.atrasados++
    else if (situacao === 'PENDENTE') card.pendentes++
    else card.emExecucao++
  }

  const peso = { ATRASADA: 0, PENDENTE: 1, EM_EXECUCAO: 2 } as const
  for (const c of cards.values()) c.ativos.sort((x, y) => peso[x.situacao] - peso[y.situacao] || (x.dias ?? 0) - (y.dias ?? 0))
  return [...cards.values()].sort((a, b) => b.atrasados - a.atrasados || a.nome_predio.localeCompare(b.nome_predio))
}