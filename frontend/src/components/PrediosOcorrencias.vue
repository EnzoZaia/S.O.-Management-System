<template>
  <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100" data-testid="predios-ocorrencias">
    <h2 class="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2"><span>🏢</span> Prédios com mais ocorrências</h2>
    <p class="text-[10px] text-gray-400 font-semibold uppercase mt-1 mb-5">Volume de ordens e usuários afetados (cada pessoa conta uma vez por ordem)</p>

    <div v-if="predios.length === 0" class="py-8 text-center text-sm text-gray-400 font-medium">Sem ocorrências no período.</div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="text-[10px] text-gray-400 uppercase tracking-wider border-b border-gray-100">
            <th class="py-2 pr-4 font-semibold">#</th>
            <th class="py-2 pr-4 font-semibold">Prédio</th>
            <th class="py-2 pr-4 font-semibold w-1/2">Ocorrências</th>
            <th class="py-2 font-semibold text-right">Afetados</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(p, i) in predios" :key="p.chave" class="border-b border-gray-50 hover:bg-gray-50 transition-colors" data-testid="linha-predio">
            <td class="py-3 pr-4 text-xs font-black text-gray-400">{{ i + 1 }}</td>
            <td class="py-3 pr-4 text-sm font-bold text-gray-800">{{ p.nome }}</td>
            <td class="py-3 pr-4">
              <div class="flex items-center gap-3">
                <div class="flex-1 bg-gray-50 rounded-full h-2.5 border border-gray-100 overflow-hidden">
                  <div class="h-2.5 rounded-full bg-gradient-to-r from-purple-400 to-purple-500 transition-all duration-700"
                    :style="{ width: `${maximo > 0 ? (p.totalOcorrencias / maximo) * 100 : 0}%` }"></div>
                </div>
                <span class="w-8 text-right text-xs font-bold text-gray-700">{{ p.totalOcorrencias }}</span>
              </div>
            </td>
            <td class="py-3 text-sm font-bold text-gray-700 text-right">{{ p.totalAfetados }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PredioOcorrencias } from '@/types/indicadoresGlobais'

const props = defineProps<{ predios: PredioOcorrencias[] }>()
const maximo = computed(() => props.predios.reduce((m, p) => Math.max(m, p.totalOcorrencias), 0))
</script>