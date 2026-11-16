<template>
  <div class="fixed bottom-6 right-6 z-40" data-testid="sino-notificacoes">
    <button @click="alternar" :aria-label="`Notificações (${naoLidas} não lidas)`"
      class="relative w-11 h-11 rounded-full bg-white border border-gray-200 shadow-md flex items-center justify-center text-xl hover:bg-gray-50 cursor-pointer">
      🔔
      <span v-if="naoLidas" class="absolute -top-1 -right-1 min-w-5 h-5 px-1 rounded-full bg-red-600 text-white text-[10px] font-bold flex items-center justify-center">
        {{ naoLidas > 99 ? '99+' : naoLidas }}
      </span>
    </button>

    <div v-if="aberto" class="absolute right-0 bottom-full mb-2 w-[min(22rem,calc(100vw-2rem))] bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden">
      <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <p class="text-sm font-bold text-gray-800">Notificações</p>
        <button v-if="naoLidas" @click="marcarTodas" class="text-[11px] font-bold text-blue-600 hover:underline cursor-pointer">Marcar todas como lidas</button>
      </div>
      <div class="max-h-96 overflow-y-auto">
        <p v-if="erro" class="p-4 text-xs font-semibold text-red-600">{{ erro }}</p>
        <p v-else-if="!notificacoes.length" class="p-6 text-center text-xs text-gray-400">Nenhuma notificação.</p>
        <button v-for="n in notificacoes" :key="n.id_notificacao" @click="ler(n)"
          class="w-full text-left px-4 py-3 border-b border-gray-50 hover:bg-gray-50 cursor-pointer"
          :class="n.lida ? 'opacity-60' : 'bg-blue-50/40'">
          <div class="flex items-start gap-2">
            <span v-if="!n.lida" class="mt-1.5 w-2 h-2 rounded-full bg-blue-600 shrink-0"></span>
            <div class="min-w-0">
              <p class="text-xs font-bold text-gray-800">{{ n.titulo }}</p>
              <p class="text-xs text-gray-600 mt-0.5 break-words">{{ n.mensagem }}</p>
              <p class="text-[10px] text-gray-400 mt-1">{{ formatar(n.dt_criacao) }}</p>
            </div>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { listarNotificacoes, marcarComoLida, type Notificacao } from '@/services/notificacaoService'

const INTERVALO_ATUALIZACAO_MS = 60000

const aberto = ref(false)
const notificacoes = ref<Notificacao[]>([])
const naoLidas = ref(0)
const erro = ref('')
let temporizador: ReturnType<typeof setInterval> | undefined

async function carregar() {
  try {
    const dados = await listarNotificacoes()
    notificacoes.value = dados.notificacoes
    naoLidas.value = dados.nao_lidas
    erro.value = ''
  } catch {
    erro.value = 'Não foi possível carregar as notificações.'
  }
}

function alternar() {
  aberto.value = !aberto.value
  if (aberto.value) carregar()
}

async function ler(n: Notificacao) {
  if (n.lida) return
  try {
    await marcarComoLida(n.id_notificacao)
    n.lida = true
    naoLidas.value = Math.max(0, naoLidas.value - 1)
  } catch {
    erro.value = 'Não foi possível marcar a notificação como lida.'
  }
}

async function marcarTodas() {
  await Promise.allSettled(notificacoes.value.filter((n) => !n.lida).map(ler))
}

function formatar(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

onMounted(() => {
  carregar()
  temporizador = setInterval(carregar, INTERVALO_ATUALIZACAO_MS)
})

onBeforeUnmount(() => {
  if (temporizador) clearInterval(temporizador)
})
</script>
