<template>
  <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col" :data-testid="testid">
    <h2 class="text-sm font-bold text-gray-800 uppercase tracking-wider">{{ titulo }}</h2>
    <p class="text-[10px] text-gray-400 font-semibold uppercase mt-1 mb-5">{{ subtitulo }}</p>

    <div v-if="itens.length === 0" class="py-8 text-center text-sm text-gray-400 font-medium">Sem ocorrências no período.</div>

    <ul v-else class="space-y-3">
      <li v-for="(item, i) in itens" :key="item.chave" class="flex items-center gap-3">
        <span class="w-6 text-[11px] font-black text-gray-400">#{{ i + 1 }}</span>
        <div class="min-w-0 w-40 shrink-0">
          <p class="text-xs font-bold text-gray-800 truncate" :title="item.rotulo">{{ item.rotulo }}</p>
          <p v-if="item.detalhe" class="text-[10px] text-gray-400 font-semibold truncate">{{ item.detalhe }}</p>
        </div>
        <div class="flex-1 bg-gray-50 rounded-full h-2.5 border border-gray-100 overflow-hidden">
          <div class="h-2.5 rounded-full transition-all duration-700" :class="cor"
            :style="{ width: `${maximo > 0 ? (item.total / maximo) * 100 : 0}%` }"></div>
        </div>
        <span class="w-8 text-right text-xs font-bold text-gray-700">{{ item.total }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ItemDistribuicao } from '@/types/indicadoresGlobais'
import { maiorTotal } from '@/utils/indicadoresGlobais'

const props = withDefaults(
  defineProps<{ titulo: string; subtitulo: string; itens: ItemDistribuicao[]; cor?: string; testid?: string }>(),
  { cor: 'bg-gradient-to-r from-blue-400 to-blue-500', testid: 'distribuicao' },
)

const maximo = computed(() => maiorTotal(props.itens))
</script>