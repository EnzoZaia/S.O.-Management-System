<template>
  <div ref="raiz" role="radiogroup" aria-label="Nota de 1 a 5 estrelas" :aria-readonly="readonly"
    class="inline-flex items-center gap-1" @mouseleave="hover = null">
    <button v-for="n in NOTA_MAX" :key="n" type="button" role="radio" :aria-checked="modelValue === n"
      :aria-label="`${n} ${n === 1 ? 'estrela' : 'estrelas'}`" :disabled="readonly" :tabindex="tabIndexDe(n)"
      @click="escolher(n)" @mouseenter="hover = n" @keydown="aoTeclar"
      :class="[tamanho, readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110', preenchida(n) ? 'text-amber-400' : 'text-gray-300']"
      class="transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded">
      <svg viewBox="0 0 24 24" fill="currentColor" class="w-full h-full">
        <path d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.007 5.404.433c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.433 2.082-5.007Z" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { NOTA_MAX, NOTA_MIN } from '@/utils/validacaoAvaliacao'

const props = withDefaults(
  defineProps<{ modelValue: number | null; readonly?: boolean; size?: 'sm' | 'lg' }>(),
  { readonly: false, size: 'lg' },
)
const emit = defineEmits<{ (e: 'update:modelValue', valor: number): void }>()

const raiz = ref<HTMLElement | null>(null)
const hover = ref<number | null>(null)
const tamanho = computed(() => (props.size === 'sm' ? 'w-5 h-5' : 'w-10 h-10'))

function preenchida(n: number) {
  const ref = props.readonly ? props.modelValue : (hover.value ?? props.modelValue)
  return n <= (ref ?? 0)
}

// Roving tabindex: só uma estrela entra na ordem de tabulação.
function tabIndexDe(n: number) {
  return n === (props.modelValue ?? NOTA_MIN) ? 0 : -1
}

function escolher(n: number) {
  if (!props.readonly) emit('update:modelValue', n)
}

async function aoTeclar(evento: KeyboardEvent) {
  if (props.readonly) return
  const atual = props.modelValue ?? 0
  let proxima: number | null = null
  if (evento.key === 'ArrowRight' || evento.key === 'ArrowUp') proxima = Math.min(NOTA_MAX, atual + 1)
  if (evento.key === 'ArrowLeft' || evento.key === 'ArrowDown') proxima = Math.max(NOTA_MIN, atual - 1)
  if (proxima === null) return
  evento.preventDefault()
  emit('update:modelValue', proxima)
  await nextTick()
  raiz.value?.querySelector<HTMLElement>('[aria-checked="true"]')?.focus()
}
</script>