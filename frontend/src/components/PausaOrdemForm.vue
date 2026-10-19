<template>
  <div class="w-full animate-fade-in bg-white p-5 rounded-xl border border-gray-200 shadow-sm" data-testid="form-pausa">
    <h3 class="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2"><span>⏸️</span> Pausar execução</h3>

    <div class="space-y-4">
      <div class="space-y-1.5">
        <label class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Motivo da pausa *</label>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <button v-for="m in MOTIVOS_PAUSA" :key="m.valor" type="button" @click="escolher(m.valor)"
            :class="form.motivo === m.valor ? 'bg-orange-500 text-white border-orange-500 shadow-md' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'"
            class="py-2.5 rounded-xl border text-sm font-bold transition-all cursor-pointer">{{ m.rotulo }}</button>
        </div>
        <p v-if="erros.motivo" role="alert" class="text-[11px] font-medium text-red-600">{{ erros.motivo }}</p>
      </div>

      <div v-if="form.motivo" class="space-y-1.5">
        <label for="detalhe-pausa" class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">{{ pergunta }} *</label>
        <textarea id="detalhe-pausa" v-model="form.detalhe" @blur="validarCampo" rows="2" :maxlength="DETALHE_PAUSA_MAX"
          :class="erros.detalhe ? 'border-red-500 focus:ring-red-400' : 'border-gray-200 focus:ring-orange-400'"
          class="w-full bg-gray-50 border text-gray-700 text-sm rounded-lg p-3 outline-none focus:ring-2 resize-none"></textarea>
        <div class="flex justify-between text-[11px]">
          <span class="text-red-600 font-medium">{{ erros.detalhe }}</span>
          <span class="text-gray-400 font-semibold">{{ form.detalhe.trim().length }}/{{ DETALHE_PAUSA_MAX }}</span>
        </div>
      </div>
    </div>

    <div class="flex justify-end gap-3 pt-4 mt-4 border-t border-gray-100">
      <button @click="emit('cancelar')" :disabled="enviando"
        class="px-5 py-2.5 text-sm font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl cursor-pointer disabled:opacity-50">Voltar</button>
      <button @click="confirmar" :disabled="enviando"
        class="px-5 py-2.5 text-sm font-bold text-white bg-orange-500 hover:bg-orange-600 rounded-xl shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
        {{ enviando ? 'Salvando...' : 'Confirmar pausa' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DadosPausa, ErrosPausa, FormularioPausa, MotivoPausa } from '@/types/execucao'
import { DETALHE_PAUSA_MAX, MOTIVOS_PAUSA, validarPausa } from '@/utils/validacaoExecucao'

defineProps<{ enviando: boolean }>()
const emit = defineEmits<{
  (e: 'cancelar'): void
  (e: 'confirmar', dados: DadosPausa): void
}>()

const form = ref<FormularioPausa>({ motivo: '', detalhe: '' })
const erros = ref<ErrosPausa>({})

const pergunta = computed(() => MOTIVOS_PAUSA.find((m) => m.valor === form.value.motivo)?.pergunta ?? '')

function escolher(motivo: MotivoPausa) {
  form.value.motivo = motivo
  erros.value = { ...erros.value, motivo: undefined }
}

function validarCampo() {
  erros.value = { ...erros.value, detalhe: validarPausa(form.value).detalhe }
}

function confirmar() {
  erros.value = validarPausa(form.value)
  if (Object.keys(erros.value).length > 0 || !form.value.motivo) return
  emit('confirmar', { motivo: form.value.motivo, detalhe: form.value.detalhe.trim() })
}
</script>