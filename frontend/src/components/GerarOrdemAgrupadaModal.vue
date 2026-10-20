<template>
  <div @click.self="emit('fechar')" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 animate-fade-in">
    <div class="bg-white rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]" data-testid="modal-gerar-ordem">
      <div class="p-6 border-b border-gray-100 bg-gray-50 flex justify-between items-center shrink-0">
        <div>
          <p class="text-xs font-bold text-purple-600 uppercase tracking-wider">Preventiva agrupada</p>
          <h2 class="text-xl font-bold text-gray-800 mt-1">🏢 {{ card.nome_predio }}</h2>
        </div>
        <button @click="emit('fechar')" :disabled="enviando" aria-label="Fechar"
          class="text-gray-400 hover:text-gray-700 p-2 rounded-full hover:bg-gray-200 transition-colors cursor-pointer">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>

      <div class="p-6 overflow-y-auto space-y-5">
        <div class="flex items-center justify-between">
          <p class="text-xs text-gray-500">Só é possível agrupar ativos <strong>do mesmo prédio</strong>. Os ativos em execução já estão vinculados a uma OS.</p>
          <button type="button" @click="alternarTodos" :disabled="livres.length === 0"
            class="text-xs font-bold text-blue-600 hover:text-blue-800 cursor-pointer whitespace-nowrap ml-4 disabled:opacity-40">
            {{ todosMarcados ? 'Limpar seleção' : 'Selecionar todos' }}
          </button>
        </div>

        <ul class="space-y-2">
          <li v-for="a in card.ativos" :key="a.id_ativo"
            :class="a.situacao === 'EM_EXECUCAO' ? 'bg-gray-50 opacity-70' : marcado(a.id_ativo) ? 'bg-blue-50 border-blue-300' : 'bg-white hover:bg-gray-50'"
            class="border border-gray-200 rounded-xl p-4 flex items-start gap-3 transition-colors">
            <input type="checkbox" :id="`ativo-${a.id_ativo}`" :checked="marcado(a.id_ativo)" :disabled="a.situacao === 'EM_EXECUCAO' || enviando"
              @change="alternar(a.id_ativo)" class="mt-1 w-4 h-4 cursor-pointer disabled:cursor-not-allowed" />
            <label :for="`ativo-${a.id_ativo}`" class="flex-1 cursor-pointer">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-sm font-bold text-gray-800">❄️ {{ a.nome }}</span>
                <span class="text-[10px] font-bold px-1.5 py-0.5 bg-purple-100 text-purple-700 border border-purple-200 rounded">PAT: {{ a.codigo_patrimonial }}</span>
                <span :class="classeSituacao(a.situacao)" class="text-[10px] font-bold px-2 py-0.5 rounded-full border">{{ rotuloSituacao(a) }}</span>
              </div>
              <p class="text-xs text-gray-500 mt-1">📍 {{ a.localizacao_nome }}</p>
              <p class="text-[11px] text-gray-500 mt-1">
                <span class="font-bold text-gray-400">Última:</span> {{ formatarDataAtivo(a.dt_ultima_preventiva) }} ·
                <span class="font-bold text-blue-600">Prazo:</span> {{ formatarDataAtivo(a.dt_proxima_preventiva) }}
              </p>
              <p v-if="a.motivo_retorno" class="text-[11px] mt-1.5 text-orange-700 bg-orange-50 border border-orange-100 rounded-lg px-2 py-1">
                Voltou como não concluído: "{{ a.motivo_retorno }}"
              </p>
              <p v-if="a.grupo_codigo" class="text-[11px] mt-1.5 text-indigo-700 font-semibold">Vinculado à OS #{{ a.grupo_codigo }}</p>
            </label>
          </li>
        </ul>
        <p v-if="erros.selecao" role="alert" class="text-xs font-medium text-red-600">{{ erros.selecao }}</p>

        <div class="space-y-1.5">
          <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Técnico responsável *</label>
          <select v-model="tecnico" @change="erros.tecnico = ''" :disabled="enviando"
            :class="erros.tecnico ? 'border-red-500' : 'border-gray-200'"
            class="w-full bg-white border text-gray-700 text-sm font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer">
            <option value="" disabled>Selecione um técnico...</option>
            <option v-for="t in tecnicos" :key="t.id_usuario" :value="t.id_usuario">{{ t.nome }}</option>
          </select>
          <p v-if="tecnicos.length === 0" class="text-[11px] text-gray-400">Nenhum técnico disponível para seleção.</p>
          <p v-if="erros.tecnico" role="alert" class="text-[11px] font-medium text-red-600">{{ erros.tecnico }}</p>
        </div>
      </div>

      <div class="p-5 border-t border-gray-100 bg-gray-50 flex items-center justify-between gap-3 shrink-0">
        <span class="text-xs font-bold text-gray-500">{{ selecionados.length }} ativo(s) selecionado(s)</span>
        <div class="flex gap-3">
          <button @click="emit('fechar')" :disabled="enviando" class="px-5 py-2.5 text-sm font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl cursor-pointer disabled:opacity-50">Cancelar</button>
          <button @click="confirmar" :disabled="enviando"
            class="px-5 py-2.5 text-sm font-bold text-white bg-purple-600 hover:bg-purple-700 rounded-xl shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
            {{ enviando ? 'Gerando...' : 'Gerar ordem agrupada' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { AtivoPainel, CardPredio, ErrosGeracao } from '@/types/preventivaGrupo'
import { formatarDataAtivo } from '@/utils/painelPreventivas'
import { validarGeracao } from '@/utils/validacaoPreventivaGrupo'

const props = defineProps<{ card: CardPredio; tecnicos: any[]; enviando: boolean }>()
const emit = defineEmits<{
  (e: 'fechar'): void
  (e: 'confirmar', dados: { predio: number; tecnico: number; ativos: number[] }): void
}>()

const marcados = ref<number[]>([])
const tecnico = ref<number | ''>('')
const erros = ref<ErrosGeracao>({})

const livres = computed(() => props.card.ativos.filter((a) => a.situacao !== 'EM_EXECUCAO'))
const selecionados = computed(() => props.card.ativos.filter((a) => marcados.value.includes(a.id_ativo)))
const todosMarcados = computed(() => livres.value.length > 0 && marcados.value.length === livres.value.length)

const marcado = (id: number) => marcados.value.includes(id)

function alternar(id: number) {
  marcados.value = marcado(id) ? marcados.value.filter((x) => x !== id) : [...marcados.value, id]
  erros.value = { ...erros.value, selecao: '' }
}

function alternarTodos() {
  marcados.value = todosMarcados.value ? [] : livres.value.map((a) => a.id_ativo)
  erros.value = { ...erros.value, selecao: '' }
}

function rotuloSituacao(a: AtivoPainel) {
  if (a.situacao === 'EM_EXECUCAO') return 'Em execução'
  if (a.situacao === 'ATRASADA') return `Atrasada (${Math.abs(a.dias ?? 0)} dias)`
  return a.dias !== null && a.dias >= 0 ? `Vence em ${a.dias} dias` : 'Pendente'
}

function classeSituacao(s: AtivoPainel['situacao']) {
  if (s === 'ATRASADA') return 'bg-red-50 text-red-700 border-red-200'
  if (s === 'EM_EXECUCAO') return 'bg-amber-100 text-amber-700 border-amber-200'
  return 'bg-orange-50 text-orange-600 border-orange-200'
}

// CA2/CA3: valida mesmo prédio, técnico e seleção antes de enviar.
function confirmar() {
  erros.value = validarGeracao(selecionados.value, tecnico.value)
  if (erros.value.selecao || erros.value.tecnico) return
  emit('confirmar', { predio: props.card.id_predio, tecnico: Number(tecnico.value), ativos: marcados.value })
}
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.2s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
</style>