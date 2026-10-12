<template>
  <div class="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4">
    <div class="max-w-md w-full bg-white rounded-3xl shadow-xl border border-gray-100 p-8 text-center animate-fade-in">

      <div v-if="status === 'loading'" class="flex flex-col items-center py-6">
        <div class="w-16 h-16 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin mb-6"></div>
        <h2 class="text-xl font-bold text-gray-800">Verificando seu e-mail...</h2>
        <p class="text-sm text-gray-500 mt-2">Aguarde um momento enquanto validamos seu link.</p>
      </div>

      <div v-else-if="status === 'success'" class="flex flex-col items-center" data-testid="confirmacao-sucesso">
        <div class="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mb-6 shadow-sm border border-emerald-200">
          <span class="text-4xl">✅</span>
        </div>
        <h2 class="text-2xl font-bold text-gray-800">E-mail Confirmado!</h2>
        <p class="text-sm text-gray-500 mt-3 mb-6 leading-relaxed">Sua conta foi ativada com sucesso. Você já pode acessar o sistema.</p>

        <div v-if="ra" class="w-full bg-blue-50 border border-blue-100 rounded-2xl p-4 mb-6">
          <p class="text-[11px] font-bold text-blue-600 uppercase tracking-wider mb-1">Seu RA</p>
          <p class="text-3xl font-black text-blue-800 tracking-widest" data-testid="ra">{{ ra }}</p>
          <p class="text-[11px] text-gray-500 mt-1">Guarde este número: ele identifica você nas solicitações.</p>
        </div>

        <button @click="irParaLogin" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3.5 rounded-xl transition-colors shadow-md cursor-pointer">Acessar o Sistema</button>
      </div>

      <!-- CA4: token inválido/expirado -> conta segue pendente e oferece novo envio -->
      <div v-else class="flex flex-col items-center" data-testid="confirmacao-erro">
        <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mb-6 shadow-sm border border-red-200">
          <span class="text-4xl">❌</span>
        </div>
        <h2 class="text-2xl font-bold text-gray-800">{{ tituloErro }}</h2>
        <p class="text-sm text-gray-500 mt-3 mb-6 leading-relaxed">{{ mensagemErro }}</p>

        <div class="w-full text-left space-y-2 mb-4">
          <label for="email-reenvio" class="text-xs font-bold text-gray-500 uppercase tracking-wide">Receber novo link</label>
          <input id="email-reenvio" v-model="emailReenvio" type="email" autocomplete="email" placeholder="seu.email@fho.edu.br"
            class="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm outline-none focus:border-blue-600" @keyup.enter="reenvio.reenviar(emailReenvio)" />
          <p v-if="reenvio.erro.value" class="text-xs font-medium text-red-600">{{ reenvio.erro.value }}</p>
          <p v-if="reenvio.sucesso.value" class="text-xs font-semibold text-emerald-600">Novo e-mail enviado! Verifique sua caixa de entrada.</p>
          <button @click="reenvio.reenviar(emailReenvio)" :disabled="reenvio.enviando.value || reenvio.segundosRestantes.value > 0"
            class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer">
            {{ reenvio.enviando.value ? 'Enviando...' : reenvio.segundosRestantes.value > 0 ? `Reenviar em ${reenvio.segundosRestantes.value}s` : 'Reenviar e-mail de confirmação' }}
          </button>
        </div>

        <button @click="irParaLogin" class="w-full bg-white hover:bg-gray-50 text-gray-700 font-bold py-3.5 rounded-xl transition-colors border border-gray-200 cursor-pointer shadow-sm">Voltar para o Login</button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { confirmarEmail, normalizarErroApi } from '@/services/cadastroService'
import { useReenvioConfirmacao } from '@/composables/useReenvioConfirmacao'

type StatusConfirmacao = 'loading' | 'success' | 'invalid' | 'expired'

const route = useRoute()
const router = useRouter()
const reenvio = useReenvioConfirmacao()

const status = ref<StatusConfirmacao>('loading')
const ra = ref('')
const mensagemBackend = ref('')
const emailReenvio = ref('')

const tituloErro = computed(() => (status.value === 'expired' ? 'Link Expirado' : 'Link Inválido'))
const mensagemErro = computed(
  () =>
    mensagemBackend.value ||
    'O link de confirmação não é válido ou já foi utilizado. Sua conta continua pendente: solicite um novo envio abaixo.',
)

onMounted(async () => {
  const token = route.params.token
  if (typeof token !== 'string' || !token) {
    status.value = 'invalid'
    return
  }

  try {
    const resultado = await confirmarEmail(token)
    ra.value = resultado.ra ?? ''
    status.value = 'success'
  } catch (e) {
    const erro = normalizarErroApi(e, '')
    mensagemBackend.value = erro.mensagem
    status.value = /expirad/i.test(erro.mensagem) ? 'expired' : 'invalid'
  }
})

function irParaLogin() {
  router.push('/')
}
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>