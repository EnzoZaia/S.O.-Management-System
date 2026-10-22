<template>
  <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100" data-testid="historico-resolucoes">
    <h2 class="text-sm font-bold text-gray-800 mb-1 uppercase tracking-wider flex items-center gap-2">
      <span>🗂️</span> Histórico de Resoluções
    </h2>
    <p class="text-[10px] text-gray-400 font-semibold uppercase mb-4">Ordens da minha área concluídas ou encerradas, da mais recente para a mais antiga</p>

    <div v-if="resolucoes.length === 0" class="py-8 text-center text-sm text-gray-400 font-medium" data-testid="sem-resolucoes">
      Nenhuma ordem resolvida até o momento.
    </div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="text-[10px] text-gray-400 uppercase tracking-wider border-b border-gray-100">
            <th class="py-2 pr-4 font-semibold">Ordem</th>
            <th class="py-2 pr-4 font-semibold">Tipo</th>
            <th class="py-2 pr-4 font-semibold">Local</th>
            <th class="py-2 pr-4 font-semibold">Técnico</th>
            <th class="py-2 pr-4 font-semibold">Concluída em</th>
            <th class="py-2 font-semibold text-right">Tempo total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in exibidas" :key="r.ordem.id_ordem_servico" class="border-b border-gray-50 hover:bg-gray-50 transition-colors">
            <td class="py-3 pr-4 text-sm font-bold text-gray-800">#{{ r.ordem.id_ordem_servico }}</td>
            <td class="py-3 pr-4">
              <span :class="r.ordem.tipo_manutencao === 'PREVENTIVA' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'"
                class="text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                {{ r.ordem.tipo_manutencao === 'PREVENTIVA' ? 'Preventiva' : 'Corretiva' }}
              </span>
            </td>
            <td class="py-3 pr-4 text-xs text-gray-600 max-w-[220px] truncate">{{ r.ordem.predio_nome || 'N/I' }} - {{ r.ordem.localizacao_nome || 'N/I' }}</td>
            <td class="py-3 pr-4 text-xs text-gray-600">{{ r.ordem.tecnico_nome || '—' }}</td>
            <td class="py-3 pr-4 text-xs text-gray-600 whitespace-nowrap">{{ formatarDataHora(r.concluidaEm) }}</td>
            <td class="py-3 text-xs font-bold text-gray-700 text-right whitespace-nowrap">{{ formatarDuracao(r.duracaoMs) }}</td>
          </tr>
        </tbody>
      </table>

      <div v-if="resolucoes.length > LIMITE_INICIAL" class="pt-4 text-center">
        <button type="button" @click="verTodas = !verTodas"
          class="text-xs font-bold text-blue-600 hover:text-blue-800 cursor-pointer">
          {{ verTodas ? 'Mostrar menos' : `Ver todas (${resolucoes.length})` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ResolucaoHistorico } from '@/utils/painelGestor'
import { formatarDuracao } from '@/utils/apontamentoTempo'
import { formatarDataHora } from '@/utils/statusOrdem'

const LIMITE_INICIAL = 8

const props = defineProps<{ resolucoes: ResolucaoHistorico[] }>()
const verTodas = ref(false)
const exibidas = computed(() => (verTodas.value ? props.resolucoes : props.resolucoes.slice(0, LIMITE_INICIAL)))
</script>