<template>
  <div class="bg-gray-50 p-4 rounded-xl border border-gray-100" data-testid="equipamento-ordem">
    <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Equipamento</p>

    <template v-if="temEquipamento">
      <p class="text-sm font-bold text-gray-800">🖥️ {{ nomeEquipamento }}</p>
      <p v-if="patrimonio" class="mt-1">
        <span class="text-[10px] bg-purple-100 text-purple-700 font-bold px-1.5 py-0.5 rounded border border-purple-200">PAT: {{ patrimonio }}</span>
      </p>
    </template>

    <p v-else-if="ehPreventivaAgrupada" class="text-sm font-medium text-gray-600">
      Preventiva agrupada: os equipamentos estão listados no checklist da ordem.
    </p>

    <p v-else class="text-sm font-medium text-gray-400">Nenhum equipamento informado nesta ordem.</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface OrdemComEquipamento {
  ativo?: number | null
  ativo_nome?: string | null
  ativo_patrimonio?: string | null
  tipo_manutencao?: string | null
}

const props = defineProps<{ ordem: OrdemComEquipamento | null | undefined }>()

const limpar = (valor?: string | null) =>
  String(valor ?? '')
    .replace(/\bNone\b/g, '')
    .replace(/\*/g, '')
    .trim()

const patrimonio = computed(() => limpar(props.ordem?.ativo_patrimonio))
const nomeEquipamento = computed(() => limpar(props.ordem?.ativo_nome) || 'Equipamento')
const temEquipamento = computed(() => !!props.ordem?.ativo || !!patrimonio.value)
const ehPreventivaAgrupada = computed(
  () => (props.ordem?.tipo_manutencao || '').toUpperCase() === 'PREVENTIVA' && !temEquipamento.value,
)
</script>

