import type { CategoriaManutencao, ErrosTriagem, FormularioTriagem } from '@/types/triagem'

export const JUSTIFICATIVA_TRIAGEM_MIN = 10
export const JUSTIFICATIVA_TRIAGEM_MAX = 200

export const CATEGORIAS: { valor: CategoriaManutencao; rotulo: string }[] = [
  { valor: 'REFRIGERACAO', rotulo: '❄️ Refrigeração' },
  { valor: 'ELETRICA', rotulo: '⚡ Elétrica' },
  { valor: 'GERAIS', rotulo: '🔧 Gerais' },
]

export const ROTULO_CATEGORIA: Record<string, string> = {
  REFRIGERACAO: 'Refrigeração',
  ELETRICA: 'Elétrica',
  GERAIS: 'Gerais',
}

export function validarJustificativaTriagem(texto: string, decisao: 'REPROVAR' | 'CANCELAR'): string | null {
  const valor = texto.trim()
  const acao = decisao === 'CANCELAR' ? 'o cancelamento' : 'a reprovação'
  if (!valor) return `Informe a justificativa para ${acao}.`
  if (valor.length < JUSTIFICATIVA_TRIAGEM_MIN) return `Descreva com pelo menos ${JUSTIFICATIVA_TRIAGEM_MIN} caracteres.`
  if (valor.length > JUSTIFICATIVA_TRIAGEM_MAX) return `Use no máximo ${JUSTIFICATIVA_TRIAGEM_MAX} caracteres.`
  return null
}

// CA1 (aprovar exige categoria e prioridade válidas) e CA2 (cancelar/reprovar exige justificativa).
export function validarTriagem(form: FormularioTriagem): ErrosTriagem {
  const erros: ErrosTriagem = {}

  if (!form.decisao) {
    erros.decisao = 'Escolha uma decisão: aprovar, reprovar ou cancelar.'
    return erros
  }

  if (form.decisao === 'APROVAR') {
    if (!CATEGORIAS.some((c) => c.valor === form.categoria)) erros.categoria = 'Selecione a categoria técnica.'
    if (form.prioridade !== 'SIM' && form.prioridade !== 'NAO') erros.prioridade = 'Selecione a prioridade.'
    return erros
  }

  const erroJust = validarJustificativaTriagem(form.justificativa, form.decisao)
  if (erroJust) erros.justificativa = erroJust
  return erros
}