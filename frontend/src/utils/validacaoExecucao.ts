import type {
  AtivoOpcao,
  CausaRaiz,
  DadosConclusao,
  ErrosConclusao,
  ErrosPausa,
  FormularioConclusao,
  FormularioPausa,
  MotivoPausa,
} from '@/types/execucao'

export const OBSERVACAO_MIN = 10
export const OBSERVACAO_MAX = 500
export const DETALHE_PAUSA_MIN = 5
export const DETALHE_PAUSA_MAX = 200
export const CAUSA_DETALHE_MAX = 150
export const INSUMOS_MAX = 10

export const CAUSAS_RAIZ: { valor: CausaRaiz; rotulo: string }[] = [
  { valor: 'DESGASTE_NATURAL', rotulo: 'Desgaste natural' },
  { valor: 'MAU_USO', rotulo: 'Mau uso' },
  { valor: 'FALHA_ELETRICA', rotulo: 'Falha elétrica' },
  { valor: 'FALTA_MANUTENCAO', rotulo: 'Falta de manutenção preventiva' },
  { valor: 'DEFEITO_FABRICACAO', rotulo: 'Defeito de fabricação' },
  { valor: 'OUTRA', rotulo: 'Outra (descrever)' },
]

export const MOTIVOS_PAUSA: { valor: MotivoPausa; rotulo: string; pergunta: string }[] = [
  { valor: 'AGUARDANDO_MATERIAL', rotulo: 'Falta de material', pergunta: 'Quais materiais faltam?' },
  { valor: 'AGUARDANDO_TERCEIRO', rotulo: 'Aguardando terceiro', pergunta: 'Qual terceiro/empresa?' },
]

const ROTULO_CAUSA: Record<string, string> = Object.fromEntries(CAUSAS_RAIZ.map((c) => [c.valor, c.rotulo]))

/** Valor para <input type="datetime-local"> no fuso local. */
export function agoraParaInput(): string {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

export function formatarDataHoraCurta(valor: string): string {
  const d = new Date(valor)
  if (Number.isNaN(d.getTime())) return valor
  return `${d.toLocaleDateString('pt-BR')} ${d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`
}

// CA2: a pausa exige motivo (material/terceiro) e o detalhe correspondente.
export function validarPausa(form: FormularioPausa): ErrosPausa {
  const erros: ErrosPausa = {}
  if (!form.motivo) erros.motivo = 'Selecione o motivo da pausa.'
  const detalhe = form.detalhe.trim()
  if (!detalhe) erros.detalhe = 'Informe o detalhe da pausa.'
  else if (detalhe.length < DETALHE_PAUSA_MIN) erros.detalhe = `Descreva com pelo menos ${DETALHE_PAUSA_MIN} caracteres.`
  else if (detalhe.length > DETALHE_PAUSA_MAX) erros.detalhe = `Use no máximo ${DETALHE_PAUSA_MAX} caracteres.`
  return erros
}

interface OpcoesConclusao {
  exigirCausaRaiz: boolean
  inicioExecucao: string | null
}

// CA3: sem observação técnica ou causa raiz a conclusão não segue.
export function validarConclusao(form: FormularioConclusao, opcoes: OpcoesConclusao): ErrosConclusao {
  const erros: ErrosConclusao = {}

  if (!form.tipoEquipamento) erros.equipamento = 'Selecione o que foi consertado.'
  else if (form.tipoEquipamento === 'AR_CONDICIONADO' && !form.patrimonio) {
    erros.equipamento = 'Selecione o ar-condicionado.'
  }

  const observacao = form.observacao.trim()
  if (!observacao) erros.observacao = 'Informe a observação técnica.'
  else if (observacao.length < OBSERVACAO_MIN) erros.observacao = `Descreva com pelo menos ${OBSERVACAO_MIN} caracteres.`
  else if (observacao.length > OBSERVACAO_MAX) erros.observacao = `Use no máximo ${OBSERVACAO_MAX} caracteres.`

  if (opcoes.exigirCausaRaiz) {
    if (!form.causaRaiz) erros.causaRaiz = 'Selecione a causa raiz.'
    else if (form.causaRaiz === 'OUTRA') {
      const detalhe = form.causaDetalhe.trim()
      if (detalhe.length < DETALHE_PAUSA_MIN) erros.causaDetalhe = 'Descreva a causa raiz.'
      else if (detalhe.length > CAUSA_DETALHE_MAX) erros.causaDetalhe = `Use no máximo ${CAUSA_DETALHE_MAX} caracteres.`
    }
  }

  if (!form.dataHoraFinal) erros.dataHoraFinal = 'Informe a data e hora final.'
  else {
    const final = Date.parse(form.dataHoraFinal)
    if (Number.isNaN(final)) erros.dataHoraFinal = 'Data e hora inválidas.'
    else if (final > Date.now() + 60_000) erros.dataHoraFinal = 'A data final não pode estar no futuro.'
    else if (opcoes.inicioExecucao && final < Date.parse(opcoes.inicioExecucao)) {
      erros.dataHoraFinal = 'A data final não pode ser anterior ao início da execução.'
    }
  }

  const insumos = form.insumos
  if (insumos.length > INSUMOS_MAX) erros.insumos = `Informe no máximo ${INSUMOS_MAX} insumos.`
  else if (insumos.some((i) => !i.descricao.trim() && i.quantidade.trim())) {
    erros.insumos = 'Informe a descrição dos insumos com quantidade.'
  }

  return erros
}

export function textoCausaRaiz(form: FormularioConclusao): string | undefined {
  if (!form.causaRaiz) return undefined
  if (form.causaRaiz === 'OUTRA') return `Outra: ${form.causaDetalhe.trim()}`
  return ROTULO_CAUSA[form.causaRaiz]
}

/**
 * Monta o payload de conclusão. O texto vira o "Detalhes:" do histórico no backend; a tag [PAT: ...]
 * é a que o backend usa para vincular o ativo e recalcular a próxima preventiva.
 * Evitar as palavras "Detalhes:" e "Justificativa:" aqui, pois as telas de histórico as usam como separador.
 */
export function montarDadosConclusao(form: FormularioConclusao, ativos: AtivoOpcao[]): DadosConclusao {
  const ativo = form.tipoEquipamento === 'AR_CONDICIONADO' ? ativos.find((a) => a.codigo_patrimonial === form.patrimonio) : undefined
  const equipamento = ativo ? `[PAT: ${ativo.codigo_patrimonial}]` : 'Diversos/Outros'
  const causa = textoCausaRaiz(form)
  const insumos = form.insumos
    .filter((i) => i.descricao.trim())
    .map((i) => (i.quantidade.trim() ? `${i.descricao.trim()} (${i.quantidade.trim()})` : i.descricao.trim()))

  const partes = [
    `Serviço concluído ${equipamento}.`,
    `Observação técnica: ${form.observacao.trim()}`,
    causa ? `Causa raiz: ${causa}.` : '',
    `Concluído em: ${formatarDataHoraCurta(form.dataHoraFinal)}.`,
    insumos.length ? `Insumos extraordinários: ${insumos.join(', ')}.` : '',
  ]

  return {
    observacao: partes.filter(Boolean).join(' '),
    causaRaiz: causa,
    idAtivo: ativo?.id_ativo ?? ativo?.id,
  }
}