<template>
  <div class="p-8">
    <div class="mb-6 flex flex-col xl:flex-row xl:items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Indicadores Gerenciais Globais</h1>
        <p class="text-sm text-gray-500 mt-1">Visão consolidada para apoiar decisões sobre manutenção e infraestrutura</p>
      </div>

      <div class="flex flex-wrap items-end gap-3">
        <div v-if="periodo === 'personalizado'" class="flex items-end gap-2">
          <div class="flex flex-col">
            <label class="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1 ml-1">De</label>
            <input v-model="inicio" type="date" data-testid="data-inicio"
              class="bg-white border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer shadow-sm" />
          </div>
          <div class="flex flex-col">
            <label class="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1 ml-1">Até</label>
            <input v-model="fim" type="date" data-testid="data-fim"
              class="bg-white border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer shadow-sm" />
          </div>
          <button @click="carregar(true)" :disabled="loading"
            class="px-4 py-2.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm cursor-pointer disabled:opacity-50">Aplicar</button>
        </div>

        <div class="w-full md:w-48">
          <label class="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1 block">Período de Análise</label>
          <select v-model="periodo" @change="aoTrocarPeriodo" data-testid="select-periodo"
            class="w-full bg-white border border-gray-200 text-gray-700 text-sm font-bold rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer shadow-sm">
            <option v-for="p in PERIODOS_GLOBAIS" :key="p.valor" :value="p.valor">{{ p.rotulo }}</option>
          </select>
        </div>

        <button @click="carregar(true)" :disabled="loading"
          class="px-4 py-2 text-xs font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-lg shadow-sm cursor-pointer disabled:opacity-50 mb-0.5">↻ Atualizar</button>
      </div>
    </div>

    <p v-if="erroPeriodo" role="alert" class="mb-4 text-xs font-semibold text-red-600">{{ erroPeriodo }}</p>

    <p v-if="indicadores && indicadores.intervalo.inicio" class="mb-4 text-[11px] font-bold text-gray-500 uppercase tracking-wider" data-testid="intervalo-aplicado">
      Intervalo aplicado a todos os indicadores: {{ formatarDataCurta(indicadores.intervalo.inicio) }} a {{ formatarDataCurta(indicadores.intervalo.fim) }}
    </p>

    <div v-if="loading && !indicadores" class="bg-white rounded-xl border border-gray-100 p-12 text-center text-gray-400 font-medium">A carregar indicadores...</div>

    <!-- CA2 -->
    <div v-else-if="erro?.tipo === 'SEM_PERMISSAO'" class="bg-white border border-red-200 rounded-xl p-12 text-center" data-testid="acesso-negado">
      <span class="text-5xl block mb-3">🔒</span>
      <p class="text-base font-bold text-gray-800">Acesso negado</p>
      <p class="text-sm text-gray-500 mt-1">Apenas usuários com permissão gerencial podem consultar os indicadores globais.</p>
    </div>

    <div v-else-if="erro?.tipo === 'INDISPONIVEL' && !indicadores" class="bg-white border border-gray-200 rounded-xl p-12 text-center">
      <span class="text-5xl block mb-3 opacity-60">🛠️</span>
      <p class="text-base font-bold text-gray-800">Recurso indisponível</p>
      <p class="text-sm text-gray-500 mt-1">O servidor ainda não oferece os indicadores globais.</p>
    </div>

    <div v-else-if="erro && !indicadores" class="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
      <p class="text-sm font-semibold text-red-700 mb-3">{{ erro.mensagem }}</p>
      <button @click="carregar(true)" class="px-4 py-2 text-xs font-bold text-red-700 bg-white border border-red-200 rounded-lg hover:bg-red-100 cursor-pointer">Tentar novamente</button>
    </div>

    <template v-else-if="indicadores">
      <p v-if="erro" class="mb-4 text-xs font-semibold text-orange-700 bg-orange-50 border border-orange-200 rounded-lg px-4 py-2">
        Não foi possível atualizar agora. Exibindo os últimos dados carregados.
      </p>

      <div class="grid grid-cols-2 gap-4 mb-6 lg:grid-cols-3">
        <div v-for="k in kpis" :key="k.chave" :data-testid="`kpi-${k.chave}`" :title="formulaDe(k.chave)"
          class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 relative overflow-hidden">
          <div class="absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10" :class="k.fundo"></div>
          <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2"><span>{{ k.icone }}</span> {{ k.rotulo }}</p>
          <p class="text-3xl font-extrabold tracking-tight mb-1" :class="k.cor" data-testid="kpi-valor">{{ k.valor }}</p>
          <p class="text-[11px] text-gray-400 font-semibold uppercase">{{ k.legenda }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-6">
        <BarrasDistribuicao titulo="Ocorrências por ativo" :subtitulo="`Top ${TOP_DISTRIBUICAO} equipamentos com mais ordens`"
          :itens="indicadores.porAtivo" testid="distribuicao-ativo" />
        <BarrasDistribuicao titulo="Ocorrências por localização" :subtitulo="`Top ${TOP_DISTRIBUICAO} ambientes com mais ordens`"
          :itens="indicadores.porLocalizacao" cor="bg-gradient-to-r from-emerald-400 to-emerald-500" testid="distribuicao-localizacao" />
      </div>

      <div class="mb-6">
        <PrediosOcorrencias :predios="indicadores.porPredio" />
      </div>

      <details class="bg-white rounded-xl p-6 shadow-sm border border-gray-100" data-testid="formulas">
        <summary class="text-sm font-bold text-gray-800 uppercase tracking-wider cursor-pointer">📐 Como cada indicador é calculado</summary>
        <dl class="mt-4 space-y-3">
          <div v-for="d in DOCUMENTACAO_INDICADORES" :key="d.chave">
            <dt class="text-xs font-bold text-gray-700">{{ d.titulo }}</dt>
            <dd class="text-xs text-gray-500">{{ d.formula }}</dd>
          </div>
        </dl>
      </details>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import BarrasDistribuicao from '@/components/BarrasDistribuicao.vue'
import PrediosOcorrencias from '@/components/PrediosOcorrencias.vue'
import { IndicadoresGlobaisError, buscarIndicadoresGlobais } from '@/services/indicadoresGlobaisService'
import type { ChaveIndicador, ErroGlobais, IndicadoresGlobais, PeriodoGlobal } from '@/types/indicadoresGlobais'
import {
  DOCUMENTACAO_INDICADORES, PERIODOS_GLOBAIS, TOP_DISTRIBUICAO, formatarDataCurta, formatarMttr,
  formatarPercentual, formatarSatisfacao, formulaDe, validarIntervalo,
} from '@/utils/indicadoresGlobais'

const periodo = ref<PeriodoGlobal>('30d')
const inicio = ref('')
const fim = ref('')
const indicadores = ref<IndicadoresGlobais | null>(null)
const loading = ref(true)
const erro = ref<ErroGlobais | null>(null)
const erroPeriodo = ref('')
let ultimaRequisicao = 0

async function carregar(manual = false) {
  erroPeriodo.value = ''
  if (periodo.value === 'personalizado') {
    const e = validarIntervalo(inicio.value, fim.value)
    if (e) {
      erroPeriodo.value = e
      return
    }
  }

  if (manual) loading.value = true
  const requisicao = ++ultimaRequisicao
  try {
    const dados = await buscarIndicadoresGlobais({ periodo: periodo.value, inicio: inicio.value, fim: fim.value })
    if (requisicao !== ultimaRequisicao) return // resposta antiga (período trocado no meio)
    indicadores.value = dados
    erro.value = null
  } catch (e) {
    if (requisicao !== ultimaRequisicao) return
    console.error('Erro ao carregar indicadores globais', e)
    erro.value = e instanceof IndicadoresGlobaisError
      ? e.info
      : { tipo: 'GENERICO', mensagem: 'Não foi possível carregar os indicadores. Tente novamente.' }
    if (erro.value.tipo === 'SEM_PERMISSAO') indicadores.value = null
  } finally {
    if (requisicao === ultimaRequisicao) loading.value = false
  }
}

// CA1: trocar o período recalcula tudo de uma vez; o personalizado espera o "Aplicar".
function aoTrocarPeriodo() {
  erroPeriodo.value = ''
  if (periodo.value !== 'personalizado') carregar(true)
}

const kpis = computed(() => {
  const i = indicadores.value
  if (!i) return []
  const lista: { chave: ChaveIndicador; icone: string; rotulo: string; valor: string; legenda: string; cor: string; fundo: string }[] = [
    { chave: 'backlog', icone: '📚', rotulo: 'Backlog ativo', valor: String(i.backlogAtivo), legenda: `Em andamento (${i.totalOrdens} ordens no período)`, cor: 'text-blue-700', fundo: 'bg-blue-600' },
    { chave: 'mttr', icone: '⏱️', rotulo: 'MTTR', valor: formatarMttr(i.mttrHoras), legenda: 'Tempo médio de resolução', cor: 'text-purple-700', fundo: 'bg-purple-600' },
    { chave: 'primeiraIntervencao', icone: '🎯', rotulo: '1ª intervenção', valor: formatarPercentual(i.resolucaoPrimeiraIntervencao), legenda: 'Resolvidas sem retorno', cor: 'text-emerald-600', fundo: 'bg-emerald-500' },
    { chave: 'satisfacao', icone: '⭐', rotulo: 'Satisfação', valor: formatarSatisfacao(i.satisfacaoMedia, i.totalAvaliacoes), legenda: 'Média das avaliações', cor: 'text-amber-600', fundo: 'bg-amber-500' },
    { chave: 'reincidencia', icone: '🔁', rotulo: 'Reincidência', valor: formatarPercentual(i.reincidencia), legenda: 'Mesmo ativo em 30 dias', cor: 'text-red-600', fundo: 'bg-red-500' },
    { chave: 'afetados', icone: '👥', rotulo: 'Usuários afetados', valor: String(i.totalAfetados), legenda: 'Pessoas distintas por ordem', cor: 'text-indigo-600', fundo: 'bg-indigo-500' },
  ]
  return lista
})

onMounted(() => carregar(true))
</script>