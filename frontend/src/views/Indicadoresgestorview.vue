<template>
  <div class="p-8">
    <div class="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Minha Visão Gerencial</h1>
        <p class="text-sm text-gray-500 mt-1">Acompanhamento das ordens sob sua gestão e filas de triagem</p>
      </div>
      <div class="flex items-end gap-3">
        <span v-if="ultimaAtualizacao" class="text-[11px] text-gray-400 font-semibold pb-2.5">Atualizado às {{ ultimaAtualizacao }}</span>
        <button @click="carregar(true)" :disabled="loading"
          class="px-4 py-2 text-xs font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-lg shadow-sm cursor-pointer disabled:opacity-50 mb-0.5">
          ↻ Atualizar
        </button>
        <div class="w-full md:w-48">
          <label class="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1 block">Período de Análise</label>
          <select v-model="periodo" @change="carregar(true)" class="w-full bg-white border border-gray-200 text-gray-700 text-sm font-bold rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer shadow-sm">
            <option v-for="p in PERIODOS" :key="p.valor" :value="p.valor">{{ p.rotulo }}</option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="loading && !indicadores" class="bg-white rounded-xl border border-gray-100 p-12 text-center text-gray-400 font-medium">A carregar painel...</div>
    <div v-else-if="erro && !indicadores" class="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
      <p class="text-sm font-semibold text-red-700 mb-3">{{ erro }}</p>
      <button @click="carregar(true)" class="px-4 py-2 text-xs font-bold text-red-700 bg-white border border-red-200 rounded-lg hover:bg-red-100 cursor-pointer">Tentar novamente</button>
    </div>

    <template v-else-if="indicadores">
      <p v-if="erro" class="mb-4 text-xs font-semibold text-orange-700 bg-orange-50 border border-orange-200 rounded-lg px-4 py-2">
        Não foi possível atualizar agora. Exibindo os últimos dados carregados.
      </p>

      <div class="grid grid-cols-2 gap-4 mb-6 lg:grid-cols-4">
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 relative overflow-hidden">
          <div class="bg-blue-600 absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10"></div>
          <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2"><span>🏢</span> Volume Sob Gestão</p>
          <p class="text-4xl font-extrabold tracking-tight mb-1 text-blue-700" data-testid="kpi-total">{{ indicadores.totalOrdens }}</p>
          <p class="text-[11px] text-gray-400 font-semibold uppercase">Ordens no Período</p>
        </div>
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 relative overflow-hidden">
          <div class="bg-orange-600 absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10"></div>
          <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2"><span>⏳</span> Fila de Triagem</p>
          <p class="text-4xl font-extrabold tracking-tight mb-1 text-orange-600" data-testid="kpi-triagem">{{ indicadores.abertas }}</p>
          <p class="text-[11px] text-gray-400 font-semibold uppercase">Pendentes de Triagem</p>
        </div>
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 relative overflow-hidden">
          <div class="bg-emerald-500 absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10"></div>
          <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2"><span>✅</span> Total Solucionado</p>
          <p class="text-4xl font-extrabold tracking-tight mb-1 text-emerald-600" data-testid="kpi-solucionado">{{ indicadores.concluidas }}</p>
          <p class="text-[11px] text-gray-400 font-semibold uppercase">Histórico Finalizado</p>
        </div>
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 relative overflow-hidden">
          <div class="bg-purple-600 absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10"></div>
          <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2"><span>⏱️</span> Tempo Médio</p>
          <p class="text-4xl font-extrabold tracking-tight mb-1 text-purple-700" data-testid="kpi-tempo">{{ formatarTempoMedio(indicadores.tempoMedio) }}</p>
          <p class="text-[11px] text-gray-400 font-semibold uppercase">Média de Resolução</p>
        </div>
      </div>

      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-8 flex flex-col">
        <div class="flex justify-between items-start mb-6">
          <div>
            <h2 class="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2"><span>⚖️</span> Saúde da Manutenção</h2>
            <p class="text-[10px] text-gray-400 font-semibold uppercase mt-1">A meta é manter as preventivas sempre acima das corretivas</p>
          </div>
          <span class="text-xs font-black px-4 py-1.5 rounded-full" :class="pctPreventiva >= 50 ? 'bg-purple-100 text-purple-700 border border-purple-200' : 'bg-orange-100 text-orange-700 border border-orange-200'">
            {{ pctPreventiva }}% Proativo
          </span>
        </div>
        <div class="flex justify-between items-end mb-3 px-1">
          <div class="flex flex-col">
            <span class="text-4xl font-black text-purple-600 leading-none">{{ tipos.preventiva }}</span>
            <span class="text-[10px] font-bold text-purple-400 uppercase tracking-wider mt-1">Preventivas (Concluídas)</span>
          </div>
          <div class="flex flex-col items-end">
            <span class="text-4xl font-black text-gray-600 leading-none">{{ tipos.corretiva }}</span>
            <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mt-1">Corretivas (Concluídas)</span>
          </div>
        </div>
        <div class="w-full h-8 bg-gray-100 rounded-xl overflow-hidden flex shadow-inner border border-gray-200/50">
          <div v-if="pctPreventiva > 0" class="h-full bg-gradient-to-r from-purple-500 to-purple-400 transition-all duration-1000 flex items-center justify-center text-xs text-white font-bold" :style="{ width: `${pctPreventiva}%` }">
            <span v-if="pctPreventiva > 10">{{ pctPreventiva }}%</span>
          </div>
          <div v-if="pctPreventiva < 100" class="h-full bg-gradient-to-r from-gray-400 to-gray-300 transition-all duration-1000 flex items-center justify-center text-xs text-white font-bold" :style="{ width: `${100 - pctPreventiva}%` }">
            <span v-if="100 - pctPreventiva > 10">{{ 100 - pctPreventiva }}%</span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-6">
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col">
          <h2 class="text-sm font-bold text-gray-800 mb-6 uppercase tracking-wider">Status das Manutenções</h2>
          <div class="space-y-4 flex-1">
            <div v-for="item in status" :key="item.chave" class="flex items-center gap-4 group">
              <span class="w-44 text-xs font-semibold text-gray-500 group-hover:text-gray-800 transition-colors shrink-0">{{ item.rotulo }}</span>
              <div class="flex-1 bg-gray-50 rounded-full h-2.5 border border-gray-100 overflow-hidden">
                <div class="h-2.5 rounded-full transition-all duration-1000 ease-out" :class="item.barra"
                  :style="{ width: `${indicadores.totalOrdens > 0 ? (item.quantidade / indicadores.totalOrdens) * 100 : 0}%` }"></div>
              </div>
              <span class="text-xs font-bold w-8 text-right" :class="item.texto">{{ item.quantidade }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col">
          <h2 class="text-sm font-bold text-gray-800 mb-6 uppercase tracking-wider flex items-center justify-between">
            <span>Desempenho da Minha Equipe</span>
            <span class="text-[10px] text-blue-600 bg-blue-50 px-2 py-1 rounded-full border border-blue-100">TÉCNICOS</span>
          </h2>
          <div class="space-y-4 overflow-y-auto max-h-[280px] pr-2 flex-1">
            <div v-if="!indicadores.rankingTecnicos.length" class="h-full flex flex-col items-center justify-center py-6">
              <span class="text-3xl mb-2 opacity-50">🏆</span>
              <p class="text-sm text-gray-400 font-medium text-center">Nenhum dado gerado para a sua equipe ainda.</p>
            </div>
            <div v-for="(tec, index) in indicadores.rankingTecnicos" :key="tec.nome" class="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-100">
              <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-100 to-blue-50 flex items-center justify-center font-bold text-blue-700 text-xs shadow-inner border border-blue-200">#{{ index + 1 }}</div>
              <div class="flex-1">
                <div class="flex items-center justify-between gap-2">
                  <p class="text-sm font-bold text-gray-800">{{ tec.nome }}</p>
                  <span v-if="tec.satisfacao_media" class="text-[10px] font-bold text-amber-600">⭐ {{ tec.satisfacao_media }} ({{ tec.total_avaliacoes }})</span>
                </div>
                <div class="flex items-center gap-2 mt-1">
                  <div class="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div class="h-full bg-emerald-500 rounded-full" :style="{ width: `${tec.total > 0 ? (tec.concluidas / tec.total) * 100 : 0}%` }"></div>
                  </div>
                  <p class="text-[10px] text-gray-500 font-bold whitespace-nowrap">{{ tec.concluidas }} / {{ tec.total }} concluídas</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mb-6">
        <GargalosPainel :gargalos="gargalos" />
      </div>

      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col mb-6">
        <h2 class="text-sm font-bold text-gray-800 mb-2 uppercase tracking-wider flex items-center gap-2">
          <span class="text-blue-500">📈</span> Curva de Resolução
        </h2>
        <p class="text-[10px] text-gray-400 font-semibold uppercase mb-4">Volume de ordens concluídas nas últimas semanas</p>
        <div class="min-h-[220px] w-full relative">
          <LineChart v-if="maxSemana > 0" :data="chartDataSemanas" :options="chartOptionsSemanas" />
          <div v-else class="absolute inset-0 flex items-center justify-center">
            <p class="text-sm text-gray-400 font-medium italic">Aguardando as primeiras conclusões.</p>
          </div>
        </div>
      </div>

      <HistoricoResolucoes :resolucoes="resolucoes" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js'
import { Line as LineChart } from 'vue-chartjs'
import GargalosPainel from '@/components/GargalosPainel.vue'
import HistoricoResolucoes from '@/components/HistoricoResolucoes.vue'
import { PainelGestorError, carregarPainel } from '@/services/painelGestorService'
import type { IndicadoresGestor, OrdemPainel, PeriodoPainel } from '@/types/painelGestor'
import {
  PERIODOS, calcularGargalos, contarResolvidasPorTipo, distribuicaoStatus, formatarTempoMedio,
  historicoResolucoes, percentualPreventiva,
} from '@/utils/painelGestor'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

// CA2: o painel relê os dados persistidos periodicamente.
const INTERVALO_ATUALIZACAO_MS = 30_000

const periodo = ref<PeriodoPainel>('30d')
const indicadores = ref<IndicadoresGestor | null>(null)
const ordens = ref<OrdemPainel[]>([])
const loading = ref(true)
const erro = ref('')
const ultimaAtualizacao = ref('')
let timer: ReturnType<typeof setInterval> | null = null
let ultimaRequisicao = 0

async function carregar(manual = false) {
  if (manual) loading.value = true
  const requisicao = ++ultimaRequisicao
  try {
    const r = await carregarPainel(periodo.value)
    if (requisicao !== ultimaRequisicao) return // resposta antiga (ex.: período trocado no meio)
    indicadores.value = r.indicadores
    ordens.value = r.ordens
    erro.value = ''
    ultimaAtualizacao.value = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    if (requisicao !== ultimaRequisicao) return
    console.error('Erro ao carregar painel do gestor', e)
    erro.value = e instanceof PainelGestorError ? e.info.mensagem : 'Não foi possível carregar o painel. Tente novamente.'
  } finally {
    if (requisicao === ultimaRequisicao) loading.value = false
  }
}

const tipos = computed(() => contarResolvidasPorTipo(ordens.value, periodo.value))
const pctPreventiva = computed(() => percentualPreventiva(tipos.value.preventiva, tipos.value.corretiva))
const status = computed(() => (indicadores.value ? distribuicaoStatus(indicadores.value) : []))
const gargalos = computed(() => calcularGargalos(ordens.value))
const resolucoes = computed(() => historicoResolucoes(ordens.value))

const semanas = computed(() => indicadores.value?.semanas ?? [])
const maxSemana = computed(() => Math.max(0, ...semanas.value.map((s) => s.valor)))

const chartDataSemanas = computed(() => ({
  labels: semanas.value.map((s) => s.label),
  datasets: [{
    label: 'Concluídas',
    data: semanas.value.map((s) => s.valor),
    borderColor: '#3b82f6',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    borderWidth: 2,
    tension: 0.4,
    fill: true,
    pointBackgroundColor: '#ffffff',
    pointBorderColor: '#2563eb',
    pointBorderWidth: 2,
    pointRadius: 4,
  }],
}))

const chartOptionsSemanas = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { backgroundColor: 'rgba(17, 24, 39, 0.9)', padding: 10, cornerRadius: 8, displayColors: false },
  },
  scales: {
    y: { beginAtZero: true, border: { display: false }, grid: { color: '#f3f4f6' }, ticks: { stepSize: 1, font: { size: 10 } } },
    x: { border: { display: false }, grid: { display: false }, ticks: { font: { size: 10 } } },
  },
}

onMounted(() => {
  carregar(true)
  timer = setInterval(() => carregar(), INTERVALO_ATUALIZACAO_MS)
})
onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>