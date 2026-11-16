<template>
  <div class="rounded-xl border border-indigo-100 bg-indigo-50/40 p-4" data-testid="assistente-tecnico">
    <div class="flex items-center justify-between gap-3 mb-3">
      <div>
        <p class="text-[11px] font-bold text-indigo-600 uppercase tracking-wider">🤖 Assistente técnico (IA)</p>
        <p class="text-xs text-gray-500 mt-0.5">Orientações baseadas no equipamento e nos manuais cadastrados. Não altera a ordem.</p>
      </div>
    </div>

    <div v-if="historico.length" class="space-y-3 mb-3 max-h-80 overflow-y-auto pr-1">
      <div v-for="(item, i) in historico" :key="i" class="space-y-2">
        <div class="ml-auto max-w-[85%] bg-indigo-600 text-white text-sm rounded-xl rounded-br-sm px-3 py-2 whitespace-pre-wrap">{{ item.pergunta }}</div>
        <div class="max-w-[95%] bg-white border border-gray-200 rounded-xl rounded-bl-sm px-3 py-2">
          <p v-if="item.aviso" class="text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2 py-1 mb-2">⚠️ {{ item.aviso }}</p>
          <p class="text-sm text-gray-700 whitespace-pre-wrap">{{ item.resposta }}</p>
          <p v-if="item.manuais.length" class="mt-2 text-[10px] font-semibold text-gray-400">
            Base consultada: {{ item.manuais.map((m) => m.titulo + (m.versao ? ` (v${m.versao})` : '')).join(', ') }}
          </p>
        </div>
      </div>
    </div>

    <p v-if="erro" role="alert" class="mb-3 text-xs font-semibold rounded-lg px-3 py-2 border"
      :class="erro.tipo === 'INDISPONIVEL' ? 'text-orange-700 bg-orange-50 border-orange-200' : 'text-red-700 bg-red-50 border-red-200'">
      {{ erro.tipo === 'INDISPONIVEL' ? `${erro.mensagem} As demais funções da ordem seguem disponíveis.` : erro.mensagem }}
    </p>

    <form @submit.prevent="enviar" class="flex flex-col sm:flex-row gap-2">
      <textarea v-model="pergunta" rows="2" :maxlength="PERGUNTA_MAX" :disabled="enviando"
        placeholder="Ex.: O ar-condicionado liga mas não gela. O que devo verificar primeiro?"
        class="flex-1 bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500 resize-none disabled:opacity-60"
        @keydown.enter.exact.prevent="enviar"></textarea>
      <button type="submit" :disabled="enviando || perguntaInvalida"
        class="px-4 py-2 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
        {{ enviando ? 'Consultando...' : 'Perguntar' }}
      </button>
    </form>
    <p class="mt-1 text-[10px] text-gray-400 text-right">{{ pergunta.trim().length }}/{{ PERGUNTA_MAX }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { InteligenciaError, consultarAssistente, type ErroIA, type ManualBase } from '@/services/inteligenciaService'

const props = defineProps<{ idOrdem: number }>()

const PERGUNTA_MIN = 5
const PERGUNTA_MAX = 1000

interface ItemConversa {
  pergunta: string
  resposta: string
  aviso: string | null
  manuais: ManualBase[]
}

const pergunta = ref('')
const historico = ref<ItemConversa[]>([])
const enviando = ref(false)
const erro = ref<ErroIA | null>(null)

const perguntaInvalida = computed(() => {
  const tamanho = pergunta.value.trim().length
  return tamanho < PERGUNTA_MIN || tamanho > PERGUNTA_MAX
})

watch(() => props.idOrdem, () => {
  historico.value = []
  pergunta.value = ''
  erro.value = null
})

async function enviar() {
  if (enviando.value || perguntaInvalida.value) return
  const texto = pergunta.value.trim()
  enviando.value = true
  erro.value = null
  try {
    const dados = await consultarAssistente(props.idOrdem, texto)
    historico.value.push({
      pergunta: texto,
      resposta: dados.resposta,
      aviso: dados.aviso,
      manuais: dados.base_conhecimento?.manuais ?? [],
    })
    pergunta.value = ''
  } catch (e) {
    erro.value = e instanceof InteligenciaError
      ? e.info
      : { tipo: 'GENERICO', mensagem: 'Não foi possível consultar o assistente.' }
  } finally {
    enviando.value = false
  }
}
</script>
