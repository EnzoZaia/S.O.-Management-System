<template>
  <div class="bg-white rounded-xl p-6 shadow-sm border border-indigo-100" data-testid="techorder-intelligence">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
      <div>
        <h2 class="text-sm font-bold text-gray-800 uppercase tracking-wider">✨ TechOrder Intelligence</h2>
        <p class="text-xs text-gray-500 mt-1">
          Análise em linguagem natural dos indicadores do período. Apenas dados agregados e anônimos são enviados à IA; é um apoio, não uma decisão.
        </p>
      </div>
      <button @click="gerar" :disabled="carregando || desabilitado"
        class="shrink-0 px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
        {{ carregando ? 'Analisando...' : analise ? 'Gerar nova análise' : 'Gerar análise' }}
      </button>
    </div>

    <div v-if="carregando" class="text-sm text-gray-400 font-medium py-6 text-center">
      Calculando indicadores e consultando a IA. Isso pode levar alguns segundos...
    </div>

    <p v-else-if="erro" role="alert" data-testid="intelligence-erro"
      class="text-xs font-semibold text-orange-700 bg-orange-50 border border-orange-200 rounded-lg px-4 py-3">
      {{ erro.mensagem }} Os indicadores nativos acima continuam válidos.
    </p>

    <div v-else-if="analise" data-testid="intelligence-analise">
      <div class="flex flex-wrap gap-x-4 gap-y-1 mb-3 text-[11px] font-bold text-gray-500 uppercase tracking-wider">
        <span>Período: {{ analise.periodo.rotulo }}</span>
        <span>Gerado em: {{ formatarDataHora(analise.gerado_em) }}</span>
      </div>
      <div class="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed bg-indigo-50/40 border border-indigo-100 rounded-lg p-4">{{ analise.analise }}</div>

      <details class="mt-4">
        <summary class="text-xs font-bold text-gray-600 cursor-pointer">Indicadores utilizados na análise</summary>
        <dl class="mt-3 grid grid-cols-2 md:grid-cols-3 gap-2">
          <div v-for="item in indicadoresUsados" :key="item.chave" class="bg-gray-50 border border-gray-100 rounded-lg px-3 py-2">
            <dt class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">{{ item.rotulo }}</dt>
            <dd class="text-sm font-bold text-gray-800">{{ item.valor }}</dd>
          </div>
        </dl>
      </details>
    </div>

    <p v-else class="text-xs text-gray-400">Clique em “Gerar análise” para interpretar os indicadores do período selecionado.</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { InteligenciaError, gerarAnaliseIntelligence, type AnaliseIntelligence, type ErroIA } from '@/services/inteligenciaService'
import type { ConsultaIndicadores } from '@/types/indicadoresGlobais'

const props = defineProps<{ consulta: ConsultaIndicadores; desabilitado?: boolean }>()

const ROTULOS: Record<string, string> = {
  volume_total: 'Volume total',
  volume_corretivas: 'Corretivas',
  volume_preventivas: 'Preventivas',
  backlog_ativo: 'Backlog ativo',
  fila_triagem: 'Fila de triagem',
  total_solucionadas: 'Solucionadas',
  tempo_medio_horas: 'Tempo médio (h)',
  mttr_horas: 'MTTR (h)',
  taxa_resolucao_primeira_intervencao: '1ª intervenção (%)',
  satisfacao_media: 'Satisfação média',
  total_avaliacoes: 'Avaliações',
  reincidencias: 'Reincidências',
  taxa_reincidencia: 'Reincidência (%)',
  usuarios_afetados: 'Usuários afetados',
  saude_ativos: 'Saúde média dos ativos',
}

const analise = ref<AnaliseIntelligence | null>(null)
const carregando = ref(false)
const erro = ref<ErroIA | null>(null)
let requisicaoAtual = 0

watch(() => [props.consulta.periodo, props.consulta.inicio, props.consulta.fim], () => {
  requisicaoAtual++
  analise.value = null
  erro.value = null
  carregando.value = false
})

function formatarValor(valor: unknown): string {
  if (valor === null || valor === undefined) return 'Sem dados'
  if (typeof valor === 'number') return Number.isInteger(valor) ? String(valor) : valor.toFixed(2).replace('.', ',')
  if (typeof valor === 'object') {
    const media = (valor as Record<string, unknown>).nota_media
    return typeof media === 'number' ? media.toFixed(1).replace('.', ',') : 'Sem dados'
  }
  return String(valor)
}

const indicadoresUsados = computed(() => {
  const indicadores = analise.value?.indicadores_usados?.indicadores ?? {}
  return Object.entries(indicadores).map(([chave, valor]) => ({
    chave,
    rotulo: ROTULOS[chave] ?? chave,
    valor: formatarValor(valor),
  }))
})

function formatarDataHora(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

async function gerar() {
  if (carregando.value) return
  const requisicao = ++requisicaoAtual
  carregando.value = true
  erro.value = null
  try {
    const dados = await gerarAnaliseIntelligence(props.consulta)
    if (requisicao !== requisicaoAtual) return
    analise.value = dados
  } catch (e) {
    if (requisicao !== requisicaoAtual) return
    analise.value = null
    erro.value = e instanceof InteligenciaError
      ? e.info
      : { tipo: 'GENERICO', mensagem: 'Não foi possível gerar a análise.' }
  } finally {
    if (requisicao === requisicaoAtual) carregando.value = false
  }
}
</script>
