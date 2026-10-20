<template>
  <div @click.self="emit('fechar')" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 animate-fade-in">
    <div class="bg-white rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]" data-testid="modal-resultados">
      <div class="p-6 border-b border-gray-100 bg-gray-50 flex justify-between items-center shrink-0">
        <div>
          <p class="text-xs font-bold text-purple-600 uppercase tracking-wider">Resultado dos ativos</p>
          <h2 class="text-xl font-bold text-gray-800 mt-1">OS #{{ grupo.id_ordem_servico }}</h2>
          <p class="text-xs text-gray-500 mt-0.5">Técnico: {{ grupo.tecnico_nome || 'N/I' }}</p>
        </div>
        <button @click="emit('fechar')" :disabled="enviando" aria-label="Fechar"
          class="text-gray-400 hover:text-gray-700 p-2 rounded-full hover:bg-gray-200 transition-colors cursor-pointer">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>

      <div class="p-6 overflow-y-auto space-y-4">
        <div class="bg-purple-50 border border-purple-100 rounded-xl p-3 text-xs text-purple-800 font-semibold">
          A ordem é encerrada automaticamente quando todos os ativos tiverem resultado. Ativos não concluídos voltam ao painel como pendentes com o motivo informado.
        </div>

        <div v-for="item in grupo.itens" :key="item.ativo" class="border border-gray-200 rounded-xl p-4 space-y-3">
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm font-bold text-gray-800 truncate">{{ nomes[item.ativo] || `Ativo #${item.ativo}` }}</p>
            <span v-if="item.resultado !== 'PENDENTE'"
              :class="item.resultado === 'CONCLUIDO' ? 'bg-emerald-100 text-emerald-700 border-emerald-200' : 'bg-orange-100 text-orange-700 border-orange-200'"
              class="text-[10px] font-bold px-2 py-0.5 rounded-full border whitespace-nowrap">
              {{ item.resultado === 'CONCLUIDO' ? 'Concluído' : 'Não concluído' }}
            </span>
          </div>

          <p v-if="item.resultado === 'NAO_CONCLUIDO' && item.motivo" class="text-xs text-gray-600 italic">"{{ item.motivo }}"</p>

          <template v-if="item.resultado === 'PENDENTE'">
            <div class="grid grid-cols-2 gap-2">
              <button type="button" @click="escolher(item.ativo, 'CONCLUIDO')" :disabled="enviando"
                :class="escolhas[item.ativo] === 'CONCLUIDO' ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-emerald-700 border-emerald-200 hover:bg-emerald-50'"
                class="py-2 rounded-lg border text-xs font-bold cursor-pointer transition-colors">✅ Concluído</button>
              <button type="button" @click="escolher(item.ativo, 'NAO_CONCLUIDO')" :disabled="enviando"
                :class="escolhas[item.ativo] === 'NAO_CONCLUIDO' ? 'bg-orange-500 text-white border-orange-500' : 'bg-white text-orange-600 border-orange-200 hover:bg-orange-50'"
                class="py-2 rounded-lg border text-xs font-bold cursor-pointer transition-colors">↩️ Não concluído</button>
            </div>
            <div v-if="escolhas[item.ativo] === 'NAO_CONCLUIDO'" class="space-y-1">
              <textarea v-model="motivos[item.ativo]" @blur="validarUm(item.ativo)" rows="2" :maxlength="MOTIVO_MAX" placeholder="Por que este ativo não foi concluído?"
                :class="errosMotivo[item.ativo] ? 'border-red-500 focus:ring-red-400' : 'border-gray-200 focus:ring-blue-500'"
                class="w-full bg-gray-50 border text-gray-700 text-sm rounded-lg p-3 outline-none focus:ring-2 resize-none"></textarea>
              <div class="flex justify-between text-[11px]">
                <span class="text-red-600 font-medium">{{ errosMotivo[item.ativo] }}</span>
                <span class="text-gray-400 font-semibold">{{ (motivos[item.ativo] ?? '').trim().length }}/{{ MOTIVO_MAX }}</span>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="p-5 border-t border-gray-100 bg-gray-50 flex justify-end gap-3 shrink-0">
        <button @click="emit('fechar')" :disabled="enviando" class="px-5 py-2.5 text-sm font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl cursor-pointer disabled:opacity-50">Fechar</button>
        <button @click="confirmar" :disabled="enviando || Object.keys(escolhas).length === 0"
          class="px-5 py-2.5 text-sm font-bold text-white bg-purple-600 hover:bg-purple-700 rounded-xl shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
          {{ enviando ? 'Salvando...' : 'Registrar resultados' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { GrupoPreventiva, ResultadoItem, ResultadoItemEnvio } from '@/types/preventivaGrupo'
import { MOTIVO_MAX, validarMotivo, validarResultados } from '@/utils/validacaoPreventivaGrupo'

defineProps<{ grupo: GrupoPreventiva; nomes: Record<number, string>; enviando: boolean }>()
const emit = defineEmits<{
  (e: 'fechar'): void
  (e: 'confirmar', itens: ResultadoItemEnvio[]): void
}>()

const escolhas = ref<Record<number, ResultadoItem>>({})
const motivos = ref<Record<number, string>>({})
const errosMotivo = ref<Record<number, string>>({})

function escolher(id: number, r: ResultadoItem) {
  escolhas.value = { ...escolhas.value, [id]: r }
  errosMotivo.value = { ...errosMotivo.value, [id]: '' }
}

function validarUm(id: number) {
  errosMotivo.value = { ...errosMotivo.value, [id]: validarMotivo(motivos.value[id] ?? '') ?? '' }
}

// CA4: não concluído exige motivo.
function confirmar() {
  errosMotivo.value = validarResultados(escolhas.value, motivos.value)
  if (Object.keys(errosMotivo.value).length > 0) return

  const itens: ResultadoItemEnvio[] = Object.entries(escolhas.value).map(([id, r]) => ({
    ativo: Number(id),
    resultado: r as ResultadoItemEnvio['resultado'],
    ...(r === 'NAO_CONCLUIDO' ? { motivo: (motivos.value[Number(id)] ?? '').trim() } : {}),
  }))
  emit('confirmar', itens)
}
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.2s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
</style>