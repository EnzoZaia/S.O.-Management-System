import type { ErrosChecklistAtivo, ItemChecklist, ItemChecklistEnvio } from '@/types/checklistPreventiva'
import { validarMotivo } from '@/utils/validacaoPreventivaGrupo'

export function contarPendentes(itens: ItemChecklist[]): number {
  return itens.filter((i) => i.resultado === 'PENDENTE').length
}

export function contarRespondidos(itens: ItemChecklist[]): number {
  return itens.length - contarPendentes(itens)
}

/** Itens não executados exigem motivo. */
function errosDeMotivo(itens: ItemChecklist[]): Record<number, string> {
  const erros: Record<number, string> = {}
  for (const item of itens) {
    if (item.resultado !== 'NAO_EXECUTADO') continue
    const erro = validarMotivo(item.motivo ?? '')
    if (erro) erros[item.id_item] = erro
  }
  return erros
}

export function temErros(e: ErrosChecklistAtivo): boolean {
  return Object.keys(e.itens).length > 0 || !!e.motivo || !!e.geral
}

/** Salvar progresso: só exige motivo nos itens marcados como não executados. */
export function validarRascunho(itens: ItemChecklist[]): ErrosChecklistAtivo {
  return { itens: errosDeMotivo(itens) }
}

/**
 * CA3: concluir o ativo como executado exige o checklist completo.
 * Decisão: se algum item ficou "não executado", o ativo só pode ser registrado como "Não concluído".
 */
export function validarConclusaoExecutada(itens: ItemChecklist[]): ErrosChecklistAtivo {
  const erros: ErrosChecklistAtivo = { itens: errosDeMotivo(itens) }
  const pendentes = contarPendentes(itens)
  if (pendentes > 0) {
    erros.geral = `Checklist incompleto: faltam ${pendentes} item(ns). Responda todos antes de concluir o ativo.`
  } else if (itens.some((i) => i.resultado === 'NAO_EXECUTADO')) {
    erros.geral = 'Há itens não executados. Registre este ativo como "Não concluído".'
  }
  return erros
}

/** Ativo não concluído exige o motivo (mesma regra da US13, CA4). */
export function validarNaoConcluido(itens: ItemChecklist[], motivoAtivo: string): ErrosChecklistAtivo {
  const erros: ErrosChecklistAtivo = { itens: errosDeMotivo(itens) }
  const erroMotivo = validarMotivo(motivoAtivo)
  if (erroMotivo) erros.motivo = erroMotivo
  return erros
}

export function montarItensEnvio(itens: ItemChecklist[]): ItemChecklistEnvio[] {
  const envio: ItemChecklistEnvio[] = []
  for (const i of itens) {
    if (i.resultado === 'PENDENTE') continue
    envio.push({
      item: i.id_item,
      resultado: i.resultado,
      ...(i.resultado === 'NAO_EXECUTADO' ? { motivo: (i.motivo ?? '').trim() } : {}),
    })
  }
  return envio
}