<template>
  <div data-testid="apontamento-tempo">
    <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">⏱️ Apontamento de tempo</p>
    <div class="bg-gray-50/50 rounded-2xl border border-gray-100 p-5 space-y-3">
      <div v-if="loading" class="text-center text-gray-400 font-medium py-3">A carregar apontamento...</div>
      <div v-else-if="erro" class="text-center text-sm text-red-600 font-semibold py-3">{{ erro }}</div>
      <div v-else-if="!resumo.inicio" class="text-center text-gray-400 font-medium py-3" data-testid="sem-inicio">
        A execução ainda não foi iniciada.
      </div>
      <template v-else>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div class="bg-white border border-gray-100 rounded-xl p-3">
            <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Início</p>
            <p class="text-sm font-bold text-gray-800">{{ formatarDataHora(resumo.inicio) }}</p>
          </div>
          <div class="bg-white border border-emerald-100 rounded-xl p-3">
            <p class="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">Tempo trabalhado</p>
            <p class="text-sm font-bold text-gray-800" data-testid="tempo-trabalhado">{{ formatarDuracao(resumo.tempoTrabalhadoMs) }}</p>
          </div>
          <div class="bg-white border border-orange-100 rounded-xl p-3">
            <p class="text-[10px] font-bold text-orange-600 uppercase tracking-wider">Tempo em pausa</p>
            <p class="text-sm font-bold text-gray-800">{{ formatarDuracao(resumo.tempoPausadoMs) }}</p>
          </div>
        </div>

        <p v-if="resumo.fim" class="text-xs font-semibold text-teal-700">
          Execução finalizada em {{ formatarDataHora(resumo.fim) }}.
        </p>
        <p v-else-if="resumo.emPausa" class="text-xs font-semibold text-orange-600">
          Cronômetro pausado: a ordem está em pausa.
        </p>
        <p v-else class="text-xs font-semibold text-blue-600">Cronômetro em andamento.</p>

        <ul v-if="resumo.pausas.length" class="space-y-1" data-testid="lista-pausas">
          <li v-for="(p, i) in resumo.pausas" :key="i"
            class="flex items-center justify-between bg-white border border-gray-100 rounded-lg px-3 py-1.5 text-xs text-gray-700">
            <span class="font-bold">{{ ROTULO_MOTIVO_PAUSA[p.motivo] || p.motivo }}</span>
            <span class="text-gray-500">
              {{ formatarDataHora(p.inicio) }} → {{ p.fim ? formatarDataHora(p.fim) : 'em andamento' }}
              · {{ formatarDuracao(p.duracaoMs) }}
            </span>
          </li>
        </ul>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { buscarEventosOrdem } from '@/services/execucaoService'
import type { EventoStatus } from '@/types/execucao'
import { calcularApontamento, formatarDuracao, ROTULO_MOTIVO_PAUSA } from '@/utils/apontamentoTempo'
import { formatarDataHora } from '@/utils/statusOrdem'

const props = defineProps<{ idOrdem: number; status?: string; versao?: number }>()
const emit = defineEmits<{ (e: 'carregado', inicio: string | null): void }>()

const eventos = ref<EventoStatus[]>([])
const loading = ref(true)
const erro = ref('')
const agora = ref(Date.now())
let timer: ReturnType<typeof setInterval> | null = null

const resumo = computed(() => calcularApontamento(eventos.value, agora.value))

async function carregar() {
  loading.value = true
  erro.value = ''
  try {
    eventos.value = await buscarEventosOrdem(props.idOrdem)
    agora.value = Date.now()
    emit('carregado', resumo.value.inicio)
  } catch (e) {
    console.error('Erro ao carregar apontamento', e)
    eventos.value = []
    erro.value = 'Não foi possível carregar o apontamento de tempo.'
    emit('carregado', null)
  } finally {
    loading.value = false
  }
}

watch(() => [props.idOrdem, props.status, props.versao], carregar)
onMounted(() => {
  carregar()
  timer = setInterval(() => { agora.value = Date.now() }, 30_000)
})
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>