<template>
  <div @click.self="emit('fechar')" class="fixed inset-0 bg-black/60 flex items-center justify-center z-[60] p-4 animate-fade-in">
    <div class="bg-white rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
      <div class="p-6 border-b border-gray-100 bg-gray-50 flex justify-between items-center shrink-0">
        <div>
          <p class="text-xs font-bold text-blue-600 uppercase tracking-wider">Validação do serviço</p>
          <h2 class="text-xl font-bold text-gray-800 mt-1">OS #{{ ordem.id_ordem_servico }}</h2>
        </div>
        <button @click="emit('fechar')" :disabled="enviando" class="text-gray-400 hover:text-gray-700 p-2 rounded-full hover:bg-gray-200 transition-colors cursor-pointer" aria-label="Fechar">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>

      <div class="p-6 overflow-y-auto space-y-5">
        <div>
          <p class="text-sm font-bold text-gray-800">O problema foi realmente resolvido?</p>
          <p class="text-xs text-gray-500 mt-1">{{ extrairProblema(ordem.descricao_servico) }}</p>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <button type="button" @click="decisao = 'SIM'" :class="decisao === 'SIM' ? 'bg-emerald-600 text-white border-emerald-600 shadow-md' : 'bg-white text-emerald-700 border-emerald-200 hover:bg-emerald-50'" class="py-3 rounded-xl border text-sm font-bold transition-all cursor-pointer">👍 Sim, foi resolvido</button>
          <button type="button" @click="decisao = 'NAO'" :class="decisao === 'NAO' ? 'bg-red-600 text-white border-red-600 shadow-md' : 'bg-white text-red-600 border-red-200 hover:bg-red-50'" class="py-3 rounded-xl border text-sm font-bold transition-all cursor-pointer">👎 Não resolvido</button>
        </div>

        <div v-if="decisao === 'SIM'" class="bg-emerald-50 border border-emerald-100 rounded-xl p-4 text-xs text-emerald-800 font-semibold">
          Ao confirmar, você será direcionado à avaliação do atendimento. A ordem só é encerrada depois dela.
        </div>

        <div v-if="decisao === 'NAO'" class="space-y-4">
          <div class="bg-red-50 border border-red-100 rounded-xl p-4 text-xs text-red-800 font-semibold">
            A ordem volta para o técnico responsável e o gestor será avisado.
          </div>

          <div class="space-y-1.5">
            <label for="just" class="text-xs font-bold text-gray-500 uppercase tracking-wider">Justificativa *</label>
            <textarea id="just" v-model="justificativa" @blur="validarJust" rows="3" :maxlength="JUSTIFICATIVA_MAX"
              placeholder="Explique o que ainda não foi resolvido..."
              :class="erroJust ? 'border-red-500 focus:ring-red-400' : 'border-gray-200 focus:ring-blue-500'"
              class="w-full bg-gray-50 border text-gray-700 text-sm rounded-lg p-3 outline-none focus:ring-2 resize-none"></textarea>
            <div class="flex justify-between text-[11px]">
              <span class="text-red-600 font-medium">{{ erroJust }}</span>
              <span class="text-gray-400 font-semibold">{{ justificativa.trim().length }}/{{ JUSTIFICATIVA_MAX }}</span>
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Nova evidência (opcional)</label>
            <label class="flex items-center justify-center gap-2 border-2 border-dashed border-gray-200 rounded-lg py-3 text-xs font-bold text-indigo-600 hover:bg-indigo-50 cursor-pointer">
              📎 Anexar fotos (até {{ EVIDENCIAS_MAX }}, {{ EVIDENCIA_TAMANHO_MAX_MB }} MB cada)
              <input type="file" accept="image/*" multiple class="hidden" @change="aoEscolherArquivos" />
            </label>
            <ul v-if="evidencias.length" class="space-y-1">
              <li v-for="(arq, i) in evidencias" :key="arq.name + i" class="flex items-center justify-between bg-gray-50 border border-gray-100 rounded-lg px-3 py-1.5 text-xs text-gray-700">
                <span class="truncate pr-2">🖼️ {{ arq.name }}</span>
                <button type="button" @click="removerArquivo(i)" class="text-red-500 font-bold cursor-pointer" :aria-label="`Remover ${arq.name}`">✕</button>
              </li>
            </ul>
            <p v-if="erroEvid" class="text-[11px] text-red-600 font-medium">{{ erroEvid }}</p>
          </div>
        </div>
      </div>

      <div class="p-5 border-t border-gray-100 bg-gray-50 flex justify-end gap-3 shrink-0">
        <button @click="emit('fechar')" :disabled="enviando" class="px-5 py-2.5 text-sm font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl cursor-pointer disabled:opacity-50">Cancelar</button>
        <button @click="confirmar" :disabled="!decisao || enviando"
          :class="decisao === 'NAO' ? 'bg-red-600 hover:bg-red-700' : 'bg-emerald-600 hover:bg-emerald-700'"
          class="px-5 py-2.5 text-sm font-bold text-white rounded-xl shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
          {{ enviando ? 'Enviando...' : decisao === 'NAO' ? 'Confirmar reprovação' : 'Confirmar e avaliar' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { OrdemPortal, ResultadoValidacao } from '@/types/portal'
import { extrairProblema } from '@/utils/statusOrdem'
import {
  EVIDENCIAS_MAX, EVIDENCIA_TAMANHO_MAX_MB, JUSTIFICATIVA_MAX, validarEvidencias, validarJustificativa,
} from '@/utils/validacaoOrdem'

defineProps<{ ordem: OrdemPortal; enviando: boolean }>()
const emit = defineEmits<{
  (e: 'fechar'): void
  (e: 'confirmar', resultado: ResultadoValidacao): void
}>()

const decisao = ref<'SIM' | 'NAO' | null>(null)
const justificativa = ref('')
const evidencias = ref<File[]>([])
const erroJust = ref('')
const erroEvid = ref('')

function validarJust() {
  erroJust.value = validarJustificativa(justificativa.value) ?? ''
}

function aoEscolherArquivos(evento: Event) {
  const input = evento.target as HTMLInputElement
  const novos = [...evidencias.value, ...Array.from(input.files ?? [])]
  input.value = ''
  erroEvid.value = validarEvidencias(novos) ?? ''
  if (!erroEvid.value) evidencias.value = novos
}

function removerArquivo(indice: number) {
  evidencias.value = evidencias.value.filter((_, i) => i !== indice)
  erroEvid.value = ''
}

function confirmar() {
  if (!decisao.value) return
  if (decisao.value === 'SIM') {
    emit('confirmar', { aprovada: true })
    return
  }
  validarJust() 
  if (erroJust.value || erroEvid.value) return
  emit('confirmar', {
    aprovada: false,
    justificativa: justificativa.value.trim(),
    evidencias: evidencias.value.length ? evidencias.value : undefined,
  })
}
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.2s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
</style>