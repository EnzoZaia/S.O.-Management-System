import type { AtivoPainel, ErrosGeracao, ResultadoItem } from '@/types/preventivaGrupo'

export const MOTIVO_MIN = 10
export const MOTIVO_MAX = 200

// CA1/CA2/CA3: seleção válida = ao menos 1 ativo livre, todos do mesmo prédio, com técnico responsável.
export function validarGeracao(selecionados: AtivoPainel[], tecnico: number | string | null | undefined): ErrosGeracao {
  const erros: ErrosGeracao = {}

  if (selecionados.length === 0) erros.selecao = 'Selecione ao menos um ativo.'
  else if (new Set(selecionados.map((a) => a.id_predio)).size > 1) {
    erros.selecao = 'Só é possível agrupar ativos do mesmo prédio. Gere uma ordem por prédio.'
  } else if (selecionados.some((a) => a.situacao === 'EM_EXECUCAO')) {
    erros.selecao = 'Há ativo já vinculado a uma ordem em execução.'
  }

  if (tecnico === '' || tecnico === null || tecnico === undefined) erros.tecnico = 'Selecione o técnico responsável.'
  return erros
}

// CA4: ativo não concluído exige o motivo.
export function validarMotivo(texto: string): string | null {
  const v = texto.trim()
  if (!v) return 'Informe o motivo.'
  if (v.length < MOTIVO_MIN) return `Descreva com pelo menos ${MOTIVO_MIN} caracteres.`
  if (v.length > MOTIVO_MAX) return `Use no máximo ${MOTIVO_MAX} caracteres.`
  return null
}

export function validarResultados(
  escolhas: Record<number, ResultadoItem>,
  motivos: Record<number, string>,
): Record<number, string> {
  const erros: Record<number, string> = {}
  for (const [id, r] of Object.entries(escolhas)) {
    if (r === 'NAO_CONCLUIDO') {
      const e = validarMotivo(motivos[Number(id)] ?? '')
      if (e) erros[Number(id)] = e
    }
  }
  return erros
}