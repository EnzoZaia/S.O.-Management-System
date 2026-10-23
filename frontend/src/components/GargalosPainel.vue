<template>
  <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col" data-testid="painel-gargalos">
    <div class="flex items-start justify-between gap-3 mb-1">
      <h2 class="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
        <span class="text-red-500">⚠️</span> Gargalos da Minha Área
      </h2>
      <span class="text-[10px] font-bold text-gray-500 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-200 whitespace-nowrap">
        {{ gargalos.length }} ordem(ns) bloqueada(s)
      </span>
    </div>
    <p class="text-[10px] text-gray-400 font-semibold uppercase mb-4">Situação atual das ordens que travam a conclusão</p>

    <div v-if="gargalos.length === 0" class="py-10 text-center" data-testid="sem-gargalos">
      <span class="text-4xl opacity-30 mb-2 block">🎉</span>
      <p class="text-sm text-gray-400 font-medium">Nenhum gargalo registrado!</p>
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="min-h-[200px] relative">
        <Doughnut :data="dadosGrafico" :options="opcoesGrafico" />
      </div>

      <div class="lg:col-span-2 space-y-3">
        <div class="flex flex-wrap gap-2">
          <button type="button" @click="filtro = 'TODAS'"
            :class="filtro === 'TODAS' ? 'bg-blue-600 text-white border-blue-600' : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'"
            class="px-3 py-1.5 text-[11px] font-bold rounded-full border transition-colors cursor-pointer">
            Todas ({{ gargalos.length }})
          </button>
          <button v-for="c in CATEGORIAS_GARGALO" :key="c.valor" type="button" @click="filtro = c.valor"
            :class="filtro === c.valor ? 'bg-blue-600 text-white border-blue-600' : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'"
            class="px-3 py-1.5 text-[11px] font-bold rounded-full border transition-colors cursor-pointer">
            {{ c.rotulo }} ({{ resumo[c.valor] }})
          </button>
        </div>

        <ul class="space-y-2 max-h-[260px] overflow-y-auto pr-1">
          <li v-if="visiveis.length === 0" class="text-center text-xs text-gray-400 font-medium py-6">
            Nenhuma ordem nesta categoria.
          </li>
          <li v-for="g in visiveis" :key="g.ordem.id_ordem_servico" data-testid="gargalo-item"
            class="border border-gray-100 rounded-lg p-3 hover:bg-gray-50 transition-colors">
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-xs font-black px-2 py-0.5 bg-gray-100 text-gray-700 rounded-md">OS #{{ g.ordem.id_ordem_servico }}</span>
              <span :class="classeCategoria(g.categoria)" class="text-[10px] font-bold px-2 py-0.5 rounded-full border">{{ rotuloCategoria(g.categoria) }}</span>
              <span v-if="g.ordem.prioridade_urgencia === 'SIM'" class="text-[10px] font-bold px-2 py-0.5 bg-red-100 text-red-700 rounded-md">🚨 Urgente</span>
              <span class="ml-auto text-[10px] font-bold text-gray-500">{{ g.diasEmAberto }} dia(s) em aberto</span>
            </div>
            <p class="text-xs font-bold text-gray-800 mt-1.5 truncate">
              {{ g.ordem.predio_nome || 'N/I' }} <span class="font-medium text-gray-500">- {{ g.ordem.localizacao_nome || 'N/I' }}</span>
            </p>
            <p class="text-xs text-gray-600 truncate" :title="extrairProblema(g.ordem.descricao_servico)">{{ extrairProblema(g.ordem.descricao_servico) }}</p>
            <p class="text-[10px] text-gray-400 font-semibold mt-1">
              {{ g.ordem.tecnico_nome ? `👷 ${g.ordem.tecnico_nome}` : 'Sem técnico atribuído' }}
            </p>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'vue-chartjs'
import type { CategoriaGargalo, GargaloOrdem } from '@/types/painelGestor'
import { CATEGORIAS_GARGALO, resumirGargalos } from '@/utils/painelGestor'
import { extrairProblema } from '@/utils/statusOrdem'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{ gargalos: GargaloOrdem[] }>()

const filtro = ref<CategoriaGargalo | 'TODAS'>('TODAS')

const resumo = computed(() => resumirGargalos(props.gargalos))
const visiveis = computed(() =>
  filtro.value === 'TODAS' ? props.gargalos : props.gargalos.filter((g) => g.categoria === filtro.value),
)

const rotuloCategoria = (c: CategoriaGargalo) => CATEGORIAS_GARGALO.find((x) => x.valor === c)?.rotulo ?? c
const classeCategoria = (c: CategoriaGargalo) => CATEGORIAS_GARGALO.find((x) => x.valor === c)?.classes ?? ''

const dadosGrafico = computed(() => ({
  labels: CATEGORIAS_GARGALO.map((c) => c.rotulo),
  datasets: [{
    backgroundColor: CATEGORIAS_GARGALO.map((c) => c.cor),
    borderColor: '#ffffff',
    borderWidth: 2,
    data: CATEGORIAS_GARGALO.map((c) => resumo.value[c.valor]),
    hoverOffset: 4,
  }],
}))

const opcoesGrafico = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '65%',
  plugins: {
    legend: { position: 'bottom' as const, labels: { font: { size: 10 }, usePointStyle: true, boxWidth: 8 } },
    tooltip: { backgroundColor: 'rgba(17, 24, 39, 0.9)', padding: 10, cornerRadius: 8 },
  },
}
</script>