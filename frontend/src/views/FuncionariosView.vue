<template>
  <div class="p-8">

    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Funcionários</h1>
        <p class="text-sm text-gray-500 mt-1">Gerencie os usuários do sistema e defina níveis de acesso</p>
      </div>
      <button @click="mostrarModal = true"
        class="bg-blue-600 text-white text-sm px-5 py-2.5 rounded-lg font-bold hover:bg-blue-700 shadow-md transition-all cursor-pointer">
        + Novo Funcionário
      </button>
    </div>

    <div class="bg-white border border-gray-100 shadow-sm rounded-xl px-4 py-4 mb-6 flex flex-wrap gap-4 items-center">
      <span class="text-xs text-gray-400 font-bold uppercase tracking-wider shrink-0">Filtrar por</span>
      <select v-model="filtroCargo" class="text-sm bg-gray-50/80 border border-gray-200 text-gray-700 font-semibold rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer transition-all">
        <option value="">Todos os cargos</option>
        <option v-for="g in grupos" :key="g.id_grupo" :value="g.desc_grupo">{{ g.desc_grupo }}</option>
      </select>
      
      <div class="relative flex-1 min-w-[200px]">
        <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400 text-sm">🔍</span>
        <input v-model="busca" type="text" placeholder="Buscar por nome ou email..."
          class="w-full text-sm bg-gray-50/80 border border-gray-200 text-gray-700 font-medium rounded-lg pl-9 pr-3 py-2 outline-none focus:ring-2 focus:ring-blue-500 transition-all" />
      </div>
      
      <button v-if="filtroCargo || busca" @click="filtroCargo = ''; busca = ''"
        class="text-xs text-red-400 font-bold hover:text-red-600 cursor-pointer whitespace-nowrap transition-colors">
        Limpar filtros
      </button>
    </div>

    <div class="bg-white border border-gray-100 shadow-sm rounded-xl overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100">
            <th class="px-5 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wide">Nome</th>
            <th class="px-5 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wide">Email</th>
            <th class="px-5 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wide w-32 text-center">Cargo</th>
            <th class="px-5 py-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wide w-32">Ações</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-if="funcionariosFiltrados.length === 0">
            <td colspan="4" class="px-5 py-12 text-center text-sm font-semibold text-gray-400">Nenhum funcionário encontrado.</td>
          </tr>
          <tr v-for="funcionario in funcionariosFiltrados" :key="funcionario.id_usuario" class="hover:bg-gray-50/80 transition-colors">
            <td class="px-5 py-4 text-sm text-gray-800 font-bold">{{ funcionario.nome }}</td>
            <td class="px-5 py-4 text-sm text-gray-500 font-medium">{{ funcionario.email }}</td>
            <td class="px-5 py-4 text-center">
              <span v-if="funcionario.grupo_descricao" :class="['px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wide', corCargo(funcionario.grupo_descricao)]">
                {{ funcionario.grupo_descricao }}
              </span>
              <span v-else class="text-xs text-gray-300 font-bold">—</span>
            </td>
            <td class="px-5 py-4 text-sm flex justify-center gap-2">
              <button @click="abrirEditar(funcionario)" class="text-blue-600 hover:text-white hover:bg-blue-600 font-bold border border-blue-200 px-3 py-1.5 rounded-lg transition-all shadow-sm cursor-pointer">
                Editar
              </button>
              <button @click="confirmarDelete(funcionario)" class="text-red-500 hover:text-white hover:bg-red-500 font-bold border border-red-200 px-3 py-1.5 rounded-lg transition-all shadow-sm cursor-pointer">
                Deletar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="px-5 py-3 border-t border-gray-100 bg-gray-50/50">
        <span class="text-xs font-semibold text-gray-400">Exibindo {{ funcionariosFiltrados.length }} registros</span>
      </div>
    </div>

    <div v-if="mostrarModal" @click.self="mostrarModal = false" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 animate-fade-in">
      <div class="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50">
          <h2 class="text-lg font-bold text-gray-800">Novo Funcionário</h2>
          <button @click="mostrarModal = false" class="text-gray-400 hover:text-gray-600 hover:bg-gray-200 p-2 rounded-full transition-colors cursor-pointer"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
        </div>
        <div class="px-6 py-6 flex flex-col gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-bold text-gray-500 uppercase tracking-wide">Nome Completo</label>
            <input v-model="novoFuncionario.nome" type="text" placeholder="Ex: João da Silva" class="text-sm bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-bold text-gray-500 uppercase tracking-wide">Email Institucional</label>
            <input v-model="novoFuncionario.email" type="email" placeholder="email@fho.edu.br" class="text-sm bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-bold text-gray-500 uppercase tracking-wide">Senha Inicial</label>
            <input v-model="novoFuncionario.senha" type="password" placeholder="••••••••" class="text-sm bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-bold text-gray-500 uppercase tracking-wide">Nível de Acesso (Cargo)</label>
            <select v-model="novoFuncionario.grupo" class="text-sm bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer">
              <option value="" disabled>Selecione um cargo...</option>
              <option v-for="g in grupos" :key="g.id_grupo" :value="g.id_grupo">{{ g.desc_grupo }}</option>
            </select>
          </div>
        </div>
        <div class="flex gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50">
          <button @click="mostrarModal = false" class="flex-1 py-2.5 text-sm font-bold rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-200 transition-colors cursor-pointer">Cancelar</button>
          <button @click="salvarFuncionario" class="flex-1 py-2.5 text-sm font-bold rounded-lg bg-blue-600 text-white hover:bg-blue-700 shadow-md transition-all cursor-pointer">Salvar Cadastro</button>
        </div>
      </div>
    </div>

    <div v-if="mostrarModalEditar" @click.self="mostrarModalEditar = false" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 animate-fade-in">
      <div class="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50">
          <h2 class="text-lg font-bold text-gray-800">Editar Funcionário</h2>
          <button @click="mostrarModalEditar = false" class="text-gray-400 hover:text-gray-600 hover:bg-gray-200 p-2 rounded-full transition-colors cursor-pointer"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
        </div>
        <div class="px-6 py-6 flex flex-col gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-bold text-gray-500 uppercase tracking-wide">Nome Completo</label>
            <input v-model="funcionarioEditando.nome" type="text" class="text-sm bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-bold text-gray-500 uppercase tracking-wide">Email</label>
            <input v-model="funcionarioEditando.email" type="email" class="text-sm bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-bold text-gray-500 uppercase tracking-wide">Nível de Acesso (Cargo)</label>
            <select v-model="funcionarioEditando.grupo" class="text-sm bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer">
              <option value="" disabled>Selecione um cargo...</option>
              <option v-for="g in grupos" :key="g.id_grupo" :value="g.id_grupo">{{ g.desc_grupo }}</option>
            </select>
          </div>
        </div>
        <div class="flex gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50">
          <button @click="mostrarModalEditar = false" class="flex-1 py-2.5 text-sm font-bold rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-200 transition-colors cursor-pointer">Cancelar</button>
          <button @click="salvarEdicao" class="flex-1 py-2.5 text-sm font-bold rounded-lg bg-blue-600 text-white hover:bg-blue-700 shadow-md transition-all cursor-pointer">Salvar Alterações</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import Swal from 'sweetalert2'

const funcionarios = ref([])
const grupos = ref<any[]>([])
const busca = ref('')
const filtroCargo = ref('')

const mostrarModal = ref(false)
const novoFuncionario = ref({ nome: '', email: '', senha: '', grupo: '' })

const mostrarModalEditar = ref(false)
const funcionarioEditando = ref<any>(null)

const authHeader = () => {
  const token = localStorage.getItem('token')
  return { headers: { Authorization: `Bearer ${token}` } }
}

onMounted(async () => {
  const [resUsuarios, resGrupos] = await Promise.all([
    api.get('/usuario/', authHeader()),
    api.get('/grupo/', authHeader())
  ])
  funcionarios.value = resUsuarios.data.dados || resUsuarios.data
  grupos.value = resGrupos.data.dados || resGrupos.data
})

const funcionariosFiltrados = computed(() => {
  return funcionarios.value.filter((f: any) => {
    const buscaOk = !busca.value || f.nome?.toLowerCase().includes(busca.value.toLowerCase()) || f.email?.toLowerCase().includes(busca.value.toLowerCase())
    const cargoOk = !filtroCargo.value || f.grupo_descricao === filtroCargo.value
    return buscaOk && cargoOk
  })
})

function corCargo(cargo: string) {
  const cores: Record<string, string> = {
    GERENTE: 'bg-blue-100 text-blue-700 border border-blue-200',
    GESTOR: 'bg-purple-100 text-purple-700 border border-purple-200',
    TECNICO: 'bg-yellow-100 text-yellow-700 border border-yellow-200',
    SOLICITANTE: 'bg-gray-100 text-gray-600 border border-gray-200',
  }
  return cores[cargo] || 'bg-gray-100 text-gray-500'
}

async function salvarFuncionario() {
  if (!novoFuncionario.value.nome || !novoFuncionario.value.email || !novoFuncionario.value.grupo) {
    Swal.fire('Atenção', 'Preencha todos os campos obrigatórios!', 'warning')
    return
  }

  try {
    await api.post('/usuario/', {
      nome: novoFuncionario.value.nome,
      email: novoFuncionario.value.email,
      senha: novoFuncionario.value.senha,
      grupo: novoFuncionario.value.grupo,
      email_confirmado: true 
    }, authHeader())
    
    const res = await api.get('/usuario/', authHeader())
    funcionarios.value = res.data.dados || res.data
    
    mostrarModal.value = false
    novoFuncionario.value = { nome: '', email: '', senha: '', grupo: '' }
    
    Swal.fire({ title: 'Cadastrado!', text: 'Funcionário adicionado com sucesso.', icon: 'success', confirmButtonColor: '#2563eb' })
  } catch (e: any) {
    console.error('Erro ao salvar funcionário:', e.response?.data || e)

    let mensagemErro = 'Ocorreu um erro ao cadastrar o funcionário. Verifique os dados.'
    
    if (e.response?.data) {
      if (e.response.data.email) {
        mensagemErro = 'Este email já está registado no sistema.'
      } else if (e.response.data.senha || e.response.data.password) {
        mensagemErro = 'A senha informada não cumpre os requisitos mínimos.'
      } else if (typeof e.response.data === 'string') {
        mensagemErro = e.response.data
      } else if (e.response.data.detail) {
        mensagemErro = e.response.data.detail
      }
    }

    Swal.fire('Erro no Registo', mensagemErro, 'error')
  }
}

async function confirmarDelete(funcionario: any) {
  const result = await Swal.fire({
    title: 'Confirmar Exclusão',
    text: `Deseja remover ${funcionario.nome}? Esta ação não pode ser desfeita.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#ef4444',
    cancelButtonColor: '#6b7280',
    confirmButtonText: 'Sim, remover',
    cancelButtonText: 'Cancelar',
    customClass: { confirmButton: 'cursor-pointer', cancelButton: 'cursor-pointer' }
  })

  if (result.isConfirmed) {
    try {
      await api.delete(`/usuario/${funcionario.id_usuario}/`, authHeader())
      funcionarios.value = funcionarios.value.filter((f: any) => f.id_usuario !== funcionario.id_usuario)
      Swal.fire({ title: 'Removido!', text: 'O funcionário foi excluído.', icon: 'success', confirmButtonColor: '#2563eb' })
    } catch (e) {
      console.error('Erro ao deletar', e)
      Swal.fire('Erro', 'Não foi possível remover este funcionário.', 'error')
    }
  }
}

function abrirEditar(funcionario: any) {
  funcionarioEditando.value = { ...funcionario, grupo: funcionario.id_grupo ? Number(funcionario.id_grupo) : '' }
  mostrarModalEditar.value = true
}

async function salvarEdicao() {
  try {
    await api.patch(`/usuario/${funcionarioEditando.value.id_usuario}/`, {
      nome: funcionarioEditando.value.nome,
      email: funcionarioEditando.value.email,
      grupo: Number(funcionarioEditando.value.grupo)
    }, authHeader())
    
    const res = await api.get('/usuario/', authHeader())
    funcionarios.value = res.data.dados || res.data
    
    mostrarModalEditar.value = false
    funcionarioEditando.value = null
    
    Swal.fire({ title: 'Atualizado!', text: 'As alterações foram salvas.', icon: 'success', confirmButtonColor: '#2563eb' })
  } catch (e) {
    console.error('Erro ao editar', e)
    Swal.fire('Erro', 'Não foi possível salvar as alterações.', 'error')
  }
}
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.2s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
</style>