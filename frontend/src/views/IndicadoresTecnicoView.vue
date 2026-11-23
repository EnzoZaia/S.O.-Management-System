<template>
  <div class="p-8">
    <div class="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Meu Desempenho</h1>
        <p class="text-sm text-gray-500 mt-1">Acompanhe sua fila de trabalho e seus resultados</p>
      </div>
      <div class="flex items-end gap-3">
        <span v-if="ultimaAtualizacao" class="text-[11px] text-gray-400 font-semibold pb-2.5">Atualizado às {{ ultimaAtualizacao }}</span>
        <button @click="carregar(true)" :disabled="loading"
          class="px-4 py-2 text-xs font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-lg shadow-sm cursor-pointer disabled:opacity-50 mb-0.5">
          ↻ Atualizar
        </button>
        <div class="w-full md:w-48">
          <label class="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1 block">Período de Análise</label>
          <select v-model="periodo" @change="carregar(true)"
            class="w-full bg-white border border-gray-200 text-gray-700 text-sm font-bold rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer shadow-sm">
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

      <div v-if="resumo.urgentes > 0" role="alert" data-testid="alerta-urgentes"
        class="mb-6 text-sm font-bold text-red-700 bg-red-50 border border-red-200 rounded-xl px-5 py-3 flex items-center gap-2">
        <span>🚨</span> Você tem {{ resumo.urgentes }} ordem(ns) urgente(s) aguardando atendimento.
      </div>

      <div class="grid grid-cols-2 gap-4 mb-6 lg:grid-cols-4">
        <div v-for="k in kpis" :key="k.chave" :data-testid="`kpi-${k.chave}`"
          class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 relative overflow-hidden">
          <div class="absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10" :class="k.fundo"></div>
          <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2"><span>{{ k.icone }}</span> {{ k.rotulo }}</p>
          <p class="text-4xl font-extrabold tracking-tight mb-1" :class="k.cor">{{ k.valor }}</p>
          <p class="text-[11px] text-gray-400 font-semibold uppercase">{{ k.legenda }}</p>
        </div>
      </div>

      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6 flex flex-col">
        <div class="flex justify-between items-start mb-6">
          <div>
            <h2 class="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2"><span>⚖️</span> Perfil dos Meus Atendimentos</h2>
            <p class="text-[10px] text-gray-400 font-semibold uppercase mt-1">Preventivas e corretivas que concluí no período</p>
          </div>
          <span class="text-xs font-black px-4 py-1.5 rounded-full bg-purple-100 text-purple-700 border border-purple-200">
            {{ pctPreventiva }}% Preventivas
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
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col" data-testid="grafico-fila">
          <h2 class="text-sm font-bold text-gray-800 mb-1 uppercase tracking-wider flex items-center gap-2"><span>📋</span> Minha Fila Atual</h2>
          <p class="text-[10px] text-gray-400 font-semibold uppercase mb-4">Situação das ordens que estão comigo agora</p>
          <div class="flex-1 min-h-[220px] flex items-center justify-center">
            <Doughnut v-if="resumo.total > 0" :data="dadosFila" :options="opcoesFila" />
            <div v-else class="text-center">
              <span class="text-4xl opacity-30 mb-2 block">🎉</span>
              <p class="text-sm text-gray-400 font-medium">Nenhuma ordem em andamento!</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col">
          <h2 class="text-sm font-bold text-gray-800 mb-1 uppercase tracking-wider flex items-center gap-2"><span class="text-blue-500">📈</span> Minhas Conclusões por Semana</h2>
          <p class="text-[10px] text-gray-400 font-semibold uppercase mb-4">Volume de ordens concluídas nas últimas semanas</p>
          <div class="flex-1 min-h-[220px] w-full relative">
            <LineChart v-if="maxSemana > 0" :data="dadosSemanas" :options="opcoesSemanas" />
            <div v-else class="absolute inset-0 flex items-center justify-center">
              <p class="text-sm text-gray-400 font-medium italic">Aguardando as primeiras conclusões.</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col" data-testid="grafico-tempo">
          <h2 class="text-sm font-bold text-gray-800 mb-1 uppercase tracking-wider flex items-center gap-2"><span>⏱️</span> Tempo Médio por Tipo</h2>
          <p class="text-[10px] text-gray-400 font-semibold uppercase mb-4">Da abertura até a conclusão, no período</p>
          <div class="flex-1 min-h-[180px] relative">
            <BarChart v-if="temTempo" :data="dadosTempo" :options="opcoesTempo" />
            <div v-else class="absolute inset-0 flex items-center justify-center">
              <p class="text-sm text-gray-400 font-medium italic">Sem ordens concluídas no período.</p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col" data-testid="satisfacao">
          <h2 class="text-sm font-bold text-gray-800 mb-1 uppercase tracking-wider flex items-center gap-2"><span>⭐</span> Satisfação dos Solicitantes</h2>
          <p class="text-[10px] text-gray-400 font-semibold uppercase mb-4">Média das avaliações dos meus atendimentos</p>
          <div v-if="indicadores.satisfacaoMedia !== null" class="flex-1 flex flex-col items-center justify-center gap-3 py-4">
            <p class="text-5xl font-black text-amber-500">{{ indicadores.satisfacaoMedia.toFixed(1).replace('.', ',') }}<span class="text-lg text-gray-400 font-bold"> / 5</span></p>
            <EstrelasAvaliacao :model-value="Math.round(indicadores.satisfacaoMedia)" readonly />
            <p class="text-xs font-semibold text-gray-500">{{ indicadores.totalAvaliacoes }} avaliação(ões) no período</p>
          </div>
          <div v-else class="flex-1 flex flex-col items-center justify-center py-6">
            <span class="text-3xl mb-2 opacity-50">⭐</span>
            <p class="text-sm text-gray-400 font-medium text-center">Nenhuma avaliação recebida no período.</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100" data-testid="proximas-ordens">
        <h2 class="text-sm font-bold text-gray-800 mb-1 uppercase tracking-wider flex items-center gap-2"><span>🎯</span> Próximas Ordens a Atender</h2>
        <p class="text-[10px] text-gray-400 font-semibold uppercase mb-4">Urgentes primeiro, depois as mais antigas</p>

        <div v-if="proximas.length === 0" class="py-8 text-center text-sm text-gray-400 font-medium">Nenhuma ordem pendente de atendimento.</div>
        <ul v-else class="space-y-2">
          <li v-for="p in proximas" :key="p.ordem.id_ordem_servico" data-testid="proxima-item"
            class="border border-gray-100 rounded-lg p-3 hover:bg-gray-50 transition-colors">
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-xs font-black px-2 py-0.5 bg-gray-100 text-gray-700 rounded-md">OS #{{ p.ordem.id_ordem_servico }}</span>
              <span :class="classeSituacao(p.situacao)" class="text-[10px] font-bold px-2 py-0.5 rounded-full border">{{ rotuloSituacao(p.situacao) }}</span>
              <span :class="p.ordem.tipo_manutencao === 'PREVENTIVA' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'"
                class="text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                {{ p.ordem.tipo_manutencao === 'PREVENTIVA' ? 'Preventiva' : 'Corretiva' }}
              </span>
              <span v-if="p.ordem.prioridade_urgencia === 'SIM'" class="text-[10px] font-bold px-2 py-0.5 bg-red-100 text-red-700 rounded-md">🚨 Urgente</span>
              <span class="ml-auto text-[10px] font-bold text-gray-500">{{ p.diasEmAberto }} dia(s) em aberto</span>
            </div>
            <p class="text-xs font-bold text-gray-800 mt-1.5 truncate">
              {{ p.ordem.predio_nome || 'N/I' }} <span class="font-medium text-gray-500">- {{ p.ordem.localizacao_nome || 'N/I' }}</span>
            </p>
            <p class="text-xs text-gray-600 truncate" :title="extrairProblema(p.ordem.descricao_servico)">{{ extrairProblema(p.ordem.descricao_servico) }}</p>
          </li>
        </ul>
        <div class="pt-4 text-center">
          <button type="button" @click="router.push('/dashboard-tecnico/ordens')" class="text-xs font-bold text-blue-600 hover:text-blue-800 cursor-pointer">Ver todas as minhas ordens →</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Chart as ChartJS, ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend,
  type ChartOptions,
} from 'chart.js'
import { Bar as BarChart, Doughnut, Line as LineChart } from 'vue-chartjs'
import EstrelasAvaliacao from '@/components/EstrelasAvaliacao.vue'
import { PainelGestorError, carregarPainel } from '@/services/painelGestorService'
import type { IndicadoresGestor, OrdemPainel, PeriodoPainel } from '@/types/painelGestor'
import type { SituacaoFila } from '@/types/painelTecnico'
import { formatarDuracao } from '@/utils/apontamentoTempo'
import { PERIODOS, contarResolvidasPorTipo, formatarTempoMedio, percentualPreventiva } from '@/utils/painelGestor'
import {
  SITUACOES_FILA, calcularFilaTecnico, proximasOrdens, resumirFila, tempoMedioPorTipo, urgentesResolvidas,
} from '@/utils/painelTecnico'
import { extrairProblema } from '@/utils/statusOrdem'

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

// O painel relê os dados persistidos periodicamente.
const INTERVALO_ATUALIZACAO_MS = 30_000

const router = useRouter()
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
    // O backend já devolve apenas as ordens e indicadores do técnico autenticado.
    const r = await carregarPainel(periodo.value)
    if (requisicao !== ultimaRequisicao) return
    indicadores.value = r.indicadores
    ordens.value = r.ordens
    erro.value = ''
    ultimaAtualizacao.value = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    if (requisicao !== ultimaRequisicao) return
    console.error('Erro ao carregar painel do técnico', e)
    erro.value = e instanceof PainelGestorError ? e.info.mensagem : 'Não foi possível carregar o painel. Tente novamente.'
  } finally {
    if (requisicao === ultimaRequisicao) loading.value = false
  }
}

const fila = computed(() => calcularFilaTecnico(ordens.value))
const resumo = computed(() => resumirFila(fila.value))
const proximas = computed(() => proximasOrdens(fila.value))
const tipos = computed(() => contarResolvidasPorTipo(ordens.value, periodo.value))
const pctPreventiva = computed(() => percentualPreventiva(tipos.value.preventiva, tipos.value.corretiva))
const tempos = computed(() => tempoMedioPorTipo(ordens.value, periodo.value))
const urgentesFeitas = computed(() => urgentesResolvidas(ordens.value, periodo.value))

const kpis = computed(() => {
  const i = indicadores.value
  if (!i) return []
  return [
    { chave: 'para-iniciar', icone: '📥', rotulo: 'Para Iniciar', valor: String(resumo.value.paraIniciar), legenda: 'Aguardando você começar', cor: 'text-emerald-600', fundo: 'bg-emerald-500' },
    { chave: 'em-execucao', icone: '🔧', rotulo: 'Em Execução', valor: String(resumo.value.emExecucao), legenda: `${resumo.value.pausadas} pausada(s)`, cor: 'text-amber-600', fundo: 'bg-amber-500' },
    { chave: 'concluidas', icone: '✅', rotulo: 'Concluídas', valor: String(i.concluidas), legenda: `${urgentesFeitas.value} urgente(s) no período`, cor: 'text-teal-600', fundo: 'bg-teal-500' },
    { chave: 'tempo', icone: '⏱️', rotulo: 'Tempo Médio', valor: formatarTempoMedio(i.tempoMedio), legenda: 'Média de resolução', cor: 'text-purple-700', fundo: 'bg-purple-600' },
  ]
})

// === Gráfico: fila atual ===
const dadosFila = computed(() => ({
  labels: SITUACOES_FILA.map((s) => s.rotulo),
  datasets: [{
    backgroundColor: SITUACOES_FILA.map((s) => s.cor),
    borderColor: '#ffffff',
    borderWidth: 2,
    data: [resumo.value.paraIniciar, resumo.value.emExecucao, resumo.value.pausadas, resumo.value.aguardandoValidacao],
    hoverOffset: 4,
  }],
}))

const opcoesFila: ChartOptions<'doughnut'> = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '65%',
  plugins: {
    legend: { position: 'right', labels: { font: { size: 11 }, usePointStyle: true, boxWidth: 8 } },
    tooltip: { backgroundColor: 'rgba(17, 24, 39, 0.9)', padding: 10, cornerRadius: 8 },
  },
}

// === Gráfico: conclusões por semana ===
const semanas = computed(() => indicadores.value?.semanas ?? [])
const maxSemana = computed(() => Math.max(0, ...semanas.value.map((s) => s.valor)))

const dadosSemanas = computed(() => ({
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

const opcoesSemanas: ChartOptions<'line'> = {
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

// === Gráfico: tempo médio por tipo (em horas) ===
const temTempo = computed(() => tempos.value.corretivaMs !== null || tempos.value.preventivaMs !== null)
const horas = (ms: number | null) => (ms === null ? 0 : Math.round((ms / 3_600_000) * 10) / 10)

const dadosTempo = computed(() => ({
  labels: [`Corretivas (${tempos.value.corretivaTotal})`, `Preventivas (${tempos.value.preventivaTotal})`],
  datasets: [{
    data: [horas(tempos.value.corretivaMs), horas(tempos.value.preventivaMs)],
    backgroundColor: ['#9ca3af', '#a855f7'],
    borderRadius: 6,
    barThickness: 28,
  }],
}))

const opcoesTempo: ChartOptions<'bar'> = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(17, 24, 39, 0.9)', padding: 10, cornerRadius: 8, displayColors: false,
      callbacks: { label: (ctx) => formatarDuracao(Number(ctx.parsed.x) * 3_600_000) },
    },
  },
  scales: {
    x: { beginAtZero: true, border: { display: false }, grid: { color: '#f3f4f6' }, ticks: { font: { size: 10 } }, title: { display: true, text: 'horas', font: { size: 10 } } },
    y: { border: { display: false }, grid: { display: false }, ticks: { font: { size: 11 } } },
  },
}

const rotuloSituacao = (s: SituacaoFila) => SITUACOES_FILA.find((x) => x.valor === s)?.rotulo ?? s
const classeSituacao = (s: SituacaoFila) => SITUACOES_FILA.find((x) => x.valor === s)?.classes ?? ''

onMounted(() => {
  carregar(true)
  timer = setInterval(() => carregar(), INTERVALO_ATUALIZACAO_MS)
})
onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>