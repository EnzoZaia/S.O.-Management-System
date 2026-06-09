<template>
  <div class="p-8">
    <div class="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Minha Visão Gerencial</h1>
        <p class="text-sm text-gray-500 mt-1">Acompanhamento das ordens sob sua gestão e filas de triagem</p>
      </div>
      <div class="w-full md:w-48">
        <label class="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1 block">Período de Análise</label>
        <select v-model="filtroPeriodo" @change="buscarDadosDashboard" class="w-full bg-white border border-gray-200 text-gray-700 text-sm font-bold rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer shadow-sm">
          <option value="30d">Últimos 30 Dias</option>
          <option value="mes_atual">Este Mês</option>
          <option value="mes_passado">Mês Passado</option>
          <option value="ano">Este Ano</option>
        </select>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4 mb-6 lg:grid-cols-4">
      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer relative overflow-hidden group">
        <div class="bg-blue-600 absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10 transition-transform group-hover:scale-110"></div>
        <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2"><span>🏢</span> Volume Sob Gestão</p>
        <p class="text-4xl font-extrabold tracking-tight mb-1 text-blue-700">{{ dadosBrutos.totalOrdens }}</p>
        <p class="text-[11px] text-gray-400 font-semibold uppercase">Ordens no Período</p>
      </div>

      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer relative overflow-hidden group">
        <div class="bg-orange-600 absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10 transition-transform group-hover:scale-110"></div>
        <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2"><span>⏳</span> Fila de Triagem</p>
        <p class="text-4xl font-extrabold tracking-tight mb-1 text-orange-600">{{ dadosBrutos.abertas }}</p>
        <p class="text-[11px] text-gray-400 font-semibold uppercase">Pendentes de Atribuição</p>
      </div>

      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer relative overflow-hidden group">
        <div class="bg-emerald-500 absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10 transition-transform group-hover:scale-110"></div>
        <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2"><span>✅</span> Sucesso da Equipe</p>
        <p class="text-4xl font-extrabold tracking-tight mb-1 text-emerald-600">{{ dadosBrutos.concluidas }}</p>
        <p class="text-[11px] text-gray-400 font-semibold uppercase">Histórico Finalizado</p>
      </div>

      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer relative overflow-hidden group">
        <div class="bg-purple-600 absolute -right-4 -top-4 w-24 h-24 rounded-full opacity-10 transition-transform group-hover:scale-110"></div>
        <p class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2"><span>⏱️</span> Tempo Médio </p>
        <p class="text-4xl font-extrabold tracking-tight mb-1 text-purple-700">{{ dadosBrutos.tempo_medio || '0d' }}</p>
        <p class="text-[11px] text-gray-400 font-semibold uppercase">Média de Resolução</p>
      </div>
    </div>

    <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-8 flex flex-col">
      <div class="flex justify-between items-start mb-6">
         <div>
           <h2 class="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2"><span>⚖️</span> Saúde da Manutenção Institucional</h2>
           <p class="text-[10px] text-gray-400 font-semibold uppercase mt-1">A meta é manter as preventivas sempre acima das corretivas</p>
         </div>
         <span class="text-xs font-black px-4 py-1.5 rounded-full" :class="pctPreventiva >= 50 ? 'bg-purple-100 text-purple-700 border border-purple-200' : 'bg-orange-100 text-orange-700 border border-orange-200'">
           {{ pctPreventiva }}% Proativo
         </span>
      </div>

      <div class="flex justify-between items-end mb-3 px-1">
         <div class="flex flex-col">
           <span class="text-4xl font-black text-purple-600 leading-none">{{ dadosBrutos.tipo_manutencao.preventiva }}</span>
           <span class="text-[10px] font-bold text-purple-400 uppercase tracking-wider mt-1"> Preventivas</span>
         </div>
         <div class="flex flex-col items-end">
           <span class="text-4xl font-black text-gray-600 leading-none">{{ dadosBrutos.tipo_manutencao.corretiva }}</span>
           <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mt-1"> Corretivas</span>
         </div>
      </div>

      <div class="w-full h-8 bg-gray-100 rounded-xl overflow-hidden flex shadow-inner border border-gray-200/50">
        <div v-if="pctPreventiva > 0" class="h-full bg-gradient-to-r from-purple-500 to-purple-400 transition-all duration-1000 flex items-center justify-center text-xs text-white font-bold shadow-[inset_0_2px_4px_rgba(0,0,0,0.1)]" :style="{ width: `${pctPreventiva}%` }">
          <span v-if="pctPreventiva > 10">{{ pctPreventiva }}%</span>
        </div>
        <div v-if="pctPreventiva < 100" class="h-full bg-gradient-to-r from-gray-400 to-gray-300 transition-all duration-1000 flex items-center justify-center text-xs text-white font-bold shadow-[inset_0_2px_4px_rgba(0,0,0,0.1)]" :style="{ width: `${100 - pctPreventiva}%` }">
           <span v-if="(100 - pctPreventiva) > 10">{{ 100 - pctPreventiva }}%</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">

      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col">
        <h2 class="text-sm font-bold text-gray-800 mb-6 uppercase tracking-wider">Status das Manutenções</h2>
        <div class="space-y-4 flex-1">
          <div v-for="item in ordensPorStatus" :key="item.status" class="flex items-center gap-4 cursor-pointer group">
            <span class="w-36 text-xs font-semibold text-gray-500 group-hover:text-gray-800 transition-colors shrink-0">{{ item.label }}</span>
            <div class="flex-1 bg-gray-50 rounded-full h-2.5 border border-gray-100 overflow-hidden">
              <div class="h-2.5 rounded-full transition-all duration-1000 ease-out relative" 
                   :class="item.corGradiente"
                   :style="{ width: `${dadosBrutos.totalOrdens > 0 ? (item.quantidade / dadosBrutos.totalOrdens) * 100 : 0}%` }">
              </div>
            </div>
            <span class="text-xs font-bold w-8 text-right transition-colors" :class="item.corTexto">{{ item.quantidade || 0 }}</span>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col">
        <h2 class="text-sm font-bold text-gray-800 mb-6 uppercase tracking-wider flex items-center justify-between">
          <span>Desempenho da Minha Equipe</span>
          <span class="text-[10px] text-blue-600 bg-blue-50 px-2 py-1 rounded-full border border-blue-100">TÉCNICOS</span>
        </h2>
        <div class="space-y-4 overflow-y-auto max-h-[250px] pr-2 flex-1">
          <div v-if="!tecnicos.length" class="h-full flex flex-col items-center justify-center py-6">
            <span class="text-3xl mb-2 opacity-50">🏆</span>
            <p class="text-sm text-gray-400 font-medium text-center">Nenhum dado gerado para a sua equipe ainda.</p>
          </div>
          <div v-else v-for="(tec, index) in tecnicos" :key="tec.nome" class="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer border border-transparent hover:border-gray-100">
            <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-100 to-blue-50 flex items-center justify-center font-bold text-blue-700 text-xs shadow-inner border border-blue-200">#{{ index + 1 }}</div>
            <div class="flex-1">
              <p class="text-sm font-bold text-gray-800">{{ tec.nome }}</p>
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

      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col">
        <h2 class="text-sm font-bold text-gray-800 mb-2 uppercase tracking-wider flex items-center gap-2">
          <span class="text-red-500">⚠️</span> Gargalos Operacionais
        </h2>
        <p class="text-[10px] text-gray-400 font-semibold uppercase mb-4">Análise de pendências que travam a conclusão</p>
        <div class="flex-1 min-h-[220px] flex items-center justify-center">
          <Doughnut v-if="temGargalos" :data="chartDataGargalos" :options="chartOptionsDoughnut" />
          <div v-else class="text-center">
            <span class="text-4xl opacity-30 mb-2 block">🎉</span>
            <p class="text-sm text-gray-400 font-medium">Nenhum gargalo registrado!</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col">
        <h2 class="text-sm font-bold text-gray-800 mb-2 uppercase tracking-wider flex items-center gap-2">
          <span class="text-blue-500">📈</span> Curva de Resolução
        </h2>
        <p class="text-[10px] text-gray-400 font-semibold uppercase mb-4">Volume de ordens concluídas nas últimas semanas</p>
        <div class="flex-1 min-h-[220px] w-full relative">
           <LineChart v-if="maxSemana > 0" :data="chartDataSemanas" :options="chartOptionsSemanas" />
           <div v-else class="absolute inset-0 flex items-center justify-center">
             <p class="text-sm text-gray-400 font-medium italic">Aguardando as primeiras conclusões.</p>
           </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, Filler } from 'chart.js'
import { Doughnut, Line as LineChart } from 'vue-chartjs'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, Filler)

const filtroPeriodo = ref('30d')

const dadosBrutos = ref({
  totalOrdens: 0, abertas: 0, emExecucao: 0, concluidas: 0, tempo_medio: '0d',
  statusDetalhados: { ABERTA: 0, APROVADA: 0, EM_EXECUCAO: 0, AGUARDANDO_MATERIAL: 0, AGUARDANDO_TERCEIRO: 0, CONCLUIDA: 0, REPROVADA: 0, CANCELADA: 0, ENCERRADA: 0 },
  tipo_manutencao: { preventiva: 0, corretiva: 0 },
  rankingTecnicos: [] as Array<{ nome: string; total: number; concluidas: number }>,
  pendencias: { aguardando_aprovacao: 0, aguardando_material: 0, aguardando_terceiro: 0, sem_tecnico: 0 },
  semanas: [] as Array<{ label: string; valor: number }>
})

const pctPreventiva = computed(() => {
  const total = dadosBrutos.value.tipo_manutencao.preventiva + dadosBrutos.value.tipo_manutencao.corretiva
  if (total === 0) return 0
  return Math.round((dadosBrutos.value.tipo_manutencao.preventiva / total) * 100)
})

const temGargalos = computed(() => {
  const p = dadosBrutos.value.pendencias
  return (p.aguardando_aprovacao + p.aguardando_material + p.aguardando_terceiro + p.sem_tecnico) > 0
})

const chartDataGargalos = computed(() => {
  const p = dadosBrutos.value.pendencias
  return {
    labels: ['Sem Triagem', 'Falta Material', 'Terceirizado', 'Aprovada sem Equipe'],
    datasets: [{
      backgroundColor: ['#f97316', '#eab308', '#a855f7', '#ef4444'],
      borderColor: '#ffffff',
      borderWidth: 2,
      data: [p.aguardando_aprovacao, p.aguardando_material, p.aguardando_terceiro, p.sem_tecnico],
      hoverOffset: 4
    }]
  }
})

const chartOptionsDoughnut = {
  responsive: true, maintainAspectRatio: false, cutout: '65%',
  plugins: {
    legend: { position: 'right' as const, labels: { font: { size: 11, family: "'Inter', sans-serif" }, usePointStyle: true, boxWidth: 8 } },
    tooltip: { backgroundColor: 'rgba(17, 24, 39, 0.9)', padding: 10, cornerRadius: 8, bodyFont: { font: { family: "'Inter', sans-serif" } } }
  }
}

const semanas = computed(() => dadosBrutos.value?.semanas?.length ? dadosBrutos.value.semanas : [])
const maxSemana = computed(() => Math.max(...semanas.value.map(s => s.valor), 0))

const chartDataSemanas = computed(() => ({
  labels: semanas.value.map(s => s.label),
  datasets: [{
    label: 'Concluídas',
    data: semanas.value.map(s => s.valor),
    borderColor: '#3b82f6', 
    backgroundColor: 'rgba(59, 130, 246, 0.1)', 
    borderWidth: 2,
    tension: 0.4, 
    fill: true,
    pointBackgroundColor: '#ffffff',
    pointBorderColor: '#2563eb',
    pointBorderWidth: 2,
    pointRadius: 4,
  }]
}))

const chartOptionsSemanas = {
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { backgroundColor: 'rgba(17, 24, 39, 0.9)', padding: 10, cornerRadius: 8, displayColors: false }
  },
  scales: {
    y: { beginAtZero: true, border: { display: false }, grid: { color: '#f3f4f6' }, ticks: { stepSize: 1, font: { size: 10 } } },
    x: { border: { display: false }, grid: { display: false }, ticks: { font: { size: 10 } } }
  }
}

const ordensPorStatus = computed(() => {
  const statusGeral = dadosBrutos.value?.statusDetalhados || {}
  return [
    { status: 'ABERTA', label: 'Pendentes de Triagem', quantidade: statusGeral.ABERTA || 0, corGradiente: 'bg-gradient-to-r from-blue-400 to-blue-500', corTexto: 'text-blue-600' },
    { status: 'APROVADA', label: 'Aprovadas / Sem Iniciar', quantidade: statusGeral.APROVADA || 0, corGradiente: 'bg-gradient-to-r from-emerald-400 to-emerald-500', corTexto: 'text-emerald-600' },
    { status: 'EM_EXECUCAO', label: 'Trabalho em Execução', quantidade: statusGeral.EM_EXECUCAO || 0, corGradiente: 'bg-gradient-to-r from-yellow-400 to-yellow-500', corTexto: 'text-yellow-600' },
    { status: 'AGUARDANDO_MATERIAL', label: 'Pausadas (Material/Terceiros)', quantidade: (statusGeral.AGUARDANDO_MATERIAL || 0) + (statusGeral.AGUARDANDO_TERCEIRO || 0), corGradiente: 'bg-gradient-to-r from-orange-400 to-orange-500', corTexto: 'text-orange-600' },
    { status: 'CONCLUIDA', label: 'Sucesso (Concluídas)', quantidade: (statusGeral.CONCLUIDA || 0) + (statusGeral.ENCERRADA || 0), corGradiente: 'bg-gradient-to-r from-teal-400 to-teal-500', corTexto: 'text-teal-600' },
    { status: 'CANCELADA', label: 'Canceladas / Reprovadas', quantidade: (statusGeral.CANCELADA || 0) + (statusGeral.REPROVADA || 0), corGradiente: 'bg-gradient-to-r from-red-400 to-red-500', corTexto: 'text-red-600' },
  ]
})

const tecnicos = computed(() => dadosBrutos.value?.rankingTecnicos || [])

async function buscarDadosDashboard() {
  try {
    const token = localStorage.getItem('token')
    const response = await api.get(`/ordem-servico/dashboard/indicadores/?periodo=${filtroPeriodo.value}`, { headers: { Authorization: `Bearer ${token}` } })
    const dadosApi = response.data?.dados || response.data || {}
    
    dadosBrutos.value = {
      totalOrdens: dadosApi.totalOrdens || 0, abertas: dadosApi.abertas || 0, emExecucao: dadosApi.emExecucao || 0, concluidas: dadosApi.concluidas || 0, tempo_medio: dadosApi.tempo_medio || '0d',
      statusDetalhados: {
        ABERTA: dadosApi.statusDetalhados?.ABERTA || 0, APROVADA: dadosApi.statusDetalhados?.APROVADA || 0, EM_EXECUCAO: dadosApi.statusDetalhados?.EM_EXECUCAO || 0,
        AGUARDANDO_MATERIAL: dadosApi.statusDetalhados?.AGUARDANDO_MATERIAL || 0, AGUARDANDO_TERCEIRO: dadosApi.statusDetalhados?.AGUARDANDO_TERCEIRO || 0,
        CONCLUIDA: dadosApi.statusDetalhados?.CONCLUIDA || 0, REPROVADA: dadosApi.statusDetalhados?.REPROVADA || 0, CANCELADA: dadosApi.statusDetalhados?.CANCELADA || 0, ENCERRADA: dadosApi.statusDetalhados?.ENCERRADA || 0,
      },
      tipo_manutencao: dadosApi.tipo_manutencao || { preventiva: 0, corretiva: 0 },
      rankingTecnicos: dadosApi.rankingTecnicos || [],
      pendencias: dadosApi.pendencias || { aguardando_aprovacao: 0, aguardando_material: 0, aguardando_terceiro: 0, sem_tecnico: 0 },
      semanas: dadosApi.semanas || []
    }
  } catch (e) { console.error('Erro ao buscar dados do dashboard:', e) }
}

onMounted(() => buscarDadosDashboard())
</script>