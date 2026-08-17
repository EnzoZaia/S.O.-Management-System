<template>
  <div 
    @mouseenter="isExpanded = true" 
    @mouseleave="isExpanded = false"
    :class="[
      'h-full bg-[#1e3a8a] flex flex-col shrink-0 transition-all duration-300 ease-in-out z-50 shadow-xl relative border-r border-blue-800',
      isExpanded ? 'w-64' : 'w-20'
    ]"
  >
    <div class="h-24 flex items-center justify-start px-5 border-b border-blue-800/60">
      <img src="@/assets/img/fho.png" alt="Logo FHO" class="w-10 h-10 object-contain shrink-0 transition-transform duration-300" :class="isExpanded ? 'scale-105' : ''" />
      <div 
        class="ml-4 flex flex-col justify-center overflow-hidden whitespace-nowrap transition-all duration-300"
        :class="isExpanded ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4 w-0'"
      >
        <p class="text-white text-sm font-extrabold tracking-wide">FHO</p>
        <p class="text-blue-300 text-[10px] uppercase font-semibold tracking-widest mt-0.5">Painel do Técnico</p>
      </div>
    </div>

    <nav class="flex-1 px-3 py-6 flex flex-col gap-1.5 overflow-x-hidden">
      <button @click="router.push('/dashboard-tecnico/ordens')"
        :class="[
          'flex items-center gap-4 px-3 py-3 rounded-xl cursor-pointer transition-all duration-200 group',
          route.path.includes('ordens') ? 'bg-blue-600/50 text-white font-semibold shadow-inner' : 'text-blue-200 hover:bg-blue-800/50 hover:text-white'
        ]">
        <span class="text-xl w-8 text-center shrink-0">🔧</span>
        <span class="text-sm whitespace-nowrap transition-all duration-300" :class="isExpanded ? 'opacity-100' : 'opacity-0 w-0'">Minhas Ordens</span>
      </button>

      <button @click="router.push('/dashboard-tecnico/ativos')"
        :class="[
          'flex items-center gap-4 px-3 py-3 rounded-xl cursor-pointer transition-all duration-200 group',
          route.path.includes('ativos') ? 'bg-blue-600/50 text-white font-semibold shadow-inner' : 'text-blue-200 hover:bg-blue-800/50 hover:text-white'
        ]">
        <span class="text-xl w-8 text-center shrink-0">🖥️</span>
        <span class="text-sm whitespace-nowrap transition-all duration-300" :class="isExpanded ? 'opacity-100' : 'opacity-0 w-0'">Ativos</span>
      </button>

      <button @click="router.push('/dashboard-tecnico/historico')"
        :class="[
          'flex items-center gap-4 px-3 py-3 rounded-xl cursor-pointer transition-all duration-200 group',
          route.path.includes('historico') ? 'bg-blue-600/50 text-white font-semibold shadow-inner' : 'text-blue-200 hover:bg-blue-800/50 hover:text-white'
        ]">
        <span class="text-xl w-8 text-center shrink-0">⏱️</span>
        <span class="text-sm whitespace-nowrap transition-all duration-300" :class="isExpanded ? 'opacity-100' : 'opacity-0 w-0'">Histórico</span>
      </button>
    </nav>
    <div class="p-4 border-t border-blue-800/60 relative">
      <div v-if="menuAberto && isExpanded" class="absolute bottom-[calc(100%-10px)] left-4 right-4 bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden z-50 py-1 origin-bottom transition-all">
        <button @click="irParaPerfil" class="w-full flex items-center gap-3 px-4 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 hover:text-blue-600 transition-colors text-left cursor-pointer">
          <span class="text-lg">👤</span> Editar meu perfil
        </button>
        <button @click="fazerLogout" class="w-full flex items-center gap-3 px-4 py-3 text-sm font-semibold text-red-600 hover:bg-red-50 transition-colors text-left cursor-pointer">
          <span class="text-lg">🚪</span> Sair do sistema
        </button>
      </div>

      <div @click="toggleMenu" class="flex items-center bg-blue-900/40 border border-blue-800/50 rounded-2xl p-2 cursor-pointer hover:bg-blue-800/50 transition-all duration-300">
        <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-blue-400 flex items-center justify-center text-white text-sm font-bold shrink-0 shadow-md">
          {{ iniciaisUsuario }}
        </div>
        <div class="flex flex-col justify-center ml-3 overflow-hidden whitespace-nowrap transition-all duration-300" :class="isExpanded ? 'w-[100px] opacity-100' : 'w-0 opacity-0'">
          <p class="text-white text-xs font-semibold truncate">{{ nomeUsuario }}</p>
          <p class="text-blue-300 text-[10px] uppercase font-medium mt-0.5">Técnico</p>
        </div>
        <div v-if="isExpanded" class="ml-auto text-blue-300 mr-2 transition-transform duration-200" :class="menuAberto ? 'rotate-180' : ''">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path></svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Swal from 'sweetalert2'

const router = useRouter()
const authStore = useAuthStore()
const route = useRoute()
const isExpanded = ref(false)

const menuAberto = ref(false)

function toggleMenu() {
  if (isExpanded.value) {
    menuAberto.value = !menuAberto.value
  }
}

function irParaPerfil() {
  menuAberto.value = false
  router.push('/perfil')
}

watch(isExpanded, (newVal) => {
  if (!newVal) menuAberto.value = false
})

const getUserData = () => {
  const storeUser = authStore.usuario as any
  if (storeUser && storeUser.nome) return storeUser
  const userStorage = localStorage.getItem('usuario')
  if (userStorage) {
    try { return JSON.parse(userStorage) } catch (e) { return null }
  }
  return null
}

const nomeUsuario = computed(() => {
  const user = getUserData()
  return user?.nome || user?.name || 'Usuário Logado'
})

const iniciaisUsuario = computed(() => {
  const nome = nomeUsuario.value
  if (nome === 'Usuário Logado') return 'US'
  return nome.substring(0, 2).toUpperCase()
})

function fazerLogout() {
  menuAberto.value = false
  Swal.fire({
    title: 'Sair do Sistema?', text: "Você precisará fazer login novamente.", icon: 'question',
    showCancelButton: true, confirmButtonColor: '#2563eb', cancelButtonColor: '#dc2626', confirmButtonText: 'Sim, sair', cancelButtonText: 'Cancelar',
    customClass: { popup: 'rounded-2xl', confirmButton: 'rounded-xl px-4 py-2 font-semibold', cancelButton: 'rounded-xl px-4 py-2 font-semibold' }
  }).then((result) => {
    if (result.isConfirmed) { authStore.logout(); router.push('/') }
  })
}
</script>