<template>
  <div class="p-8 max-w-4xl mx-auto">
    <div class="mb-8 flex items-center gap-4">
      <button @click="voltar" class="p-2.5 bg-white border border-gray-200 hover:bg-gray-50 hover:border-blue-300 text-gray-600 hover:text-blue-600 rounded-full shadow-sm transition-all cursor-pointer" title="Voltar ao Dashboard">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"></path></svg>
      </button>
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Meu Perfil</h1>
        <p class="text-sm text-gray-500 mt-1">Gira as suas informações pessoais e credenciais de acesso</p>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center p-12">
      <p class="text-gray-400 font-medium animate-pulse">A carregar dados...</p>
    </div>

    <div v-else class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="bg-gradient-to-r from-blue-700 to-blue-900 p-8 flex items-center gap-6">
        <div class="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center text-3xl font-bold text-white border-4 border-white/30 shadow-inner">
          {{ avatarInicial }}
        </div>
        <div>
          <h2 class="text-2xl font-bold text-white">{{ perfil.nome }}</h2>
          <p class="text-blue-200 font-medium mt-1">{{ perfil.grupo_descricao || 'Utilizador do Sistema' }}</p>
        </div>
      </div>

      <div class="p-8 space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-2">
            <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Nome Completo</label>
            <input v-model="form.nome" type="text" class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-800 outline-none focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all" />
          </div>
          
          <div class="space-y-2">
            <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">E-mail</label>
            <input v-model="form.email" type="email" class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-800 outline-none focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all" />
          </div>
        </div>

        <hr class="border-gray-100 my-6" />

        <div>
          <h3 class="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span>🔒</span> Alterar Senha (Opcional)
          </h3>
          <p class="text-xs text-gray-500 mb-4 mb-4">Deixe em branco se não quiser alterar a sua senha atual.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Nova Senha</label>
              <input v-model="form.senha" type="password" placeholder="••••••••" class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-800 outline-none focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all" />
            </div>
            
            <div class="space-y-2">
              <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Confirmar Nova Senha</label>
              <input v-model="form.confirmar_senha" type="password" placeholder="••••••••" class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm font-medium text-gray-800 outline-none focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all" />
            </div>
          </div>
        </div>

        <div class="pt-6 flex justify-end">
          <button @click="salvarAlteracoes" :disabled="saving" class="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-lg shadow-md transition-colors disabled:bg-blue-400 cursor-pointer flex items-center gap-2">
            <span v-if="saving">A guardar...</span>
            <span v-else>Guardar Alterações</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import Swal from 'sweetalert2'

const router = useRouter()
const loading = ref(true)
const saving = ref(false)

const perfil = ref<any>({})
const form = ref({
  nome: '',
  email: '',
  senha: '',
  confirmar_senha: ''
})

const avatarInicial = computed(() => {
  if (!perfil.value.nome) return 'U'
  return perfil.value.nome.charAt(0).toUpperCase()
})

const authHeader = () => {
  const token = localStorage.getItem('token')
  return { headers: { Authorization: `Bearer ${token}` } }
}

function voltar() {
  router.back() 
}

async function carregarPerfil() {
  loading.value = true
  try {
    const response = await api.get('/usuario/meus-dados/', authHeader())
    const dados = response.data.dados || response.data
    perfil.value = dados
    form.value.nome = dados.nome
    form.value.email = dados.email
  } catch (error) {
    Swal.fire({ title: 'Erro', text: 'Não foi possível carregar os dados do perfil.', icon: 'error' })
  } finally {
    loading.value = false
  }
}

async function salvarAlteracoes() {
  if (!form.value.nome || !form.value.email) {
    return Swal.fire({ title: 'Atenção', text: 'O nome e o e-mail são obrigatórios.', icon: 'warning' })
  }

  if (form.value.senha && form.value.senha !== form.value.confirmar_senha) {
    return Swal.fire({ title: 'Atenção', text: 'As senhas não coincidem.', icon: 'warning' })
  }

  saving.value = true
  try {
    const payload: any = {
      nome: form.value.nome,
      email: form.value.email
    }
   
    if (form.value.senha) {
      payload.senha = form.value.senha
    }

    await api.patch('/usuario/meus-dados/', payload, authHeader())
    
    Swal.fire({ title: 'Sucesso!', text: 'O seu perfil foi atualizado.', icon: 'success', confirmButtonColor: '#2563eb' })

    form.value.senha = ''
    form.value.confirmar_senha = ''

    carregarPerfil()
    
  } catch (error: any) {
    let msgErro = 'Falha ao atualizar o perfil.'
    
    if (error.response?.data?.errors) {
      const erros = error.response.data.errors
      msgErro = Object.values(erros).flat().join('\n')
    }
    
    Swal.fire({ title: 'Erro', text: msgErro, icon: 'error' })
  } finally {
    saving.value = false
  }
}

onMounted(() => carregarPerfil())
</script>