<template>
  <div class="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4">
    <div class="max-w-md w-full bg-white rounded-3xl shadow-xl border border-gray-100 p-8 text-center animate-fade-in">
      
      <div v-if="status === 'loading'" class="flex flex-col items-center py-6">
        <div class="w-16 h-16 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin mb-6"></div>
        <h2 class="text-xl font-bold text-gray-800">Verificando seu e-mail...</h2>
        <p class="text-sm text-gray-500 mt-2">Aguarde um momento enquanto validamos seu link.</p>
      </div>

      <div v-else-if="status === 'success'" class="flex flex-col items-center">
        <div class="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mb-6 shadow-sm border border-emerald-200">
          <span class="text-4xl">✅</span>
        </div>
        <h2 class="text-2xl font-bold text-gray-800">E-mail Confirmado!</h2>
        <p class="text-sm text-gray-500 mt-3 mb-8 leading-relaxed">
          Sua conta foi ativada com sucesso. Você já pode acessar o sistema FHO com suas credenciais.
        </p>
        <button @click="irParaLogin" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3.5 rounded-xl transition-colors shadow-md cursor-pointer">
          Acessar o Sistema
        </button>
      </div>

      <div v-else class="flex flex-col items-center">
        <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mb-6 shadow-sm border border-red-200">
          <span class="text-4xl">❌</span>
        </div>
        <h2 class="text-2xl font-bold text-gray-800">Link Inválido ou Expirado</h2>
        <p class="text-sm text-gray-500 mt-3 mb-8 leading-relaxed">
          {{ mensagemErro }}
        </p>
        <button @click="irParaLogin" class="w-full bg-white hover:bg-gray-50 text-gray-700 font-bold py-3.5 rounded-xl transition-colors border border-gray-200 cursor-pointer shadow-sm">
          Voltar para o Login
        </button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api' 

const route = useRoute()
const router = useRouter()

const status = ref('loading') 
const mensagemErro = ref('O link de confirmação que você acessou não é válido ou já foi utilizado.')

onMounted(async () => {
  const token = route.params.token
  
  if (!token) {
    status.value = 'error'
    return
  }

  try {
    await api.get(`/usuario/confirmar-email/${token}/`)
    status.value = 'success'
  } catch (error: any) {
    status.value = 'error'
    if (error.response?.data?.mensagem) {
      mensagemErro.value = error.response.data.mensagem
    }
  }
})

function irParaLogin() {
  router.push('/') 
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>