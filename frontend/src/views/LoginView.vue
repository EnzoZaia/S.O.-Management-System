<template>
    <div class="min-h-screen h-screen flex relative">

        <div class="w-3/8 bg-blue-800 flex flex-col items-center justify-center gap-6">
            <img src="@/assets/img/fho.png" alt="Logo da FHO" class="w-24 h-24 object-contain" />
            <div class="text-center">
                <h1 class="text-white text-2xl font-bold">Fundação Hermínio Ometto</h1>
                <p class="text-blue-200 text-sm mt-2">Sistema de Ordem de Serviço</p>
            </div>
        </div>

        <div v-if="erro" class="absolute top-4 left-0 right-0 flex justify-center z-50">
            <div class="bg-red-500 text-white px-5 py-4 rounded-lg flex items-center gap-3">
                <span>X</span>
                <p class="text-sm font-medium">{{ erro }}</p>
            </div>
        </div>

        <div class="flex-1 flex flex-col items-center justify-center h-full">
            <div class="w-full max-w-md px-8">
                <h2 class="text-blue-800 text-2xl font-bold mb-1">Bem-vindos</h2>
                <p class="text-gray-400 text-sm mb-8">Acesse com suas credenciais institucionais</p>

                <form @submit.prevent="fazerLogin" class="flex flex-col gap-4">
                    <div class="flex flex-col gap-1">
                        <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">Email</label>
                        <input v-model="email" type="email" placeholder="seu.email@fho.edu.br" :class="['border rounded-lg px-4 py-3 text-sm outline-none w-full',
                            erro ? 'border-red-500 focus:border-red-500'
                                : 'border-gray-300', 'focus:border-blue-600']" />
                    </div>

                    <div class="flex flex-col gap-1">
                        <label class="text-xs font-semibold text-gray-600 uppercase tracking-wide">Senha</label>
                        <input v-model="senha" type="password" placeholder="********" :class="['border rounded-lg px-4 py-3 text-sm outline-none w-full',
                            erro ? 'border-red-500 focus:border-red-500'
                                : 'border-gray-300', 'focus:border-blue-600']" />
                    </div>

                    <button type="submit" :disabled="carregando"
                        class="bg-blue-800 text-white py-3 rounded-lg font-semibold mt-2 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer">
                        {{ carregando ? 'Entrando...' : 'Entrar' }}
                    </button>

                    <div class="flex items-center gap-3 my-1">
                        <div class="flex-1 h-px bg-gray-200"></div>
                        <span class="text-xs text-gray-500">ou</span>
                        <div class="flex-1 h-px bg-gray-200"></div>
                    </div>

                    <button type="button" @click="router.push('/abrir-os')"
                        class="border border-blue-800 text-blue-800 py-3 rounded-lg font-semibold hover:bg-blue-50 cursor-pointer">
                        Abrir Ordem de Serviço
                    </button>
                </form>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const senha = ref('')
const carregando = ref(false)
const erro = ref('')

async function fazerLogin() {
    carregando.value = true
    erro.value = ''

    try {
        const resposta = await api.post('/authentication/token/', {
            email: email.value,
            senha: senha.value
        })

        const dadosUsuario = resposta.data.usuario 

        authStore.salvarLogin(resposta.data.access, dadosUsuario)

        console.log("Login realizado com sucesso! Usuário:", dadosUsuario.nome)

        if (dadosUsuario.grupos.includes('GERENTE')) {
            router.push('/dashboard-gerente/indicadores')
        } else if (dadosUsuario.grupos.includes('GESTOR')) {
            router.push('/dashboard-gestor/indicadores')
        } else if (dadosUsuario.grupos.includes('TECNICO')) {
            router.push('/dashboard-tecnico/ordens')
        } else {
            router.push('/dashboard')
        }

    } catch (e: any) {
        console.error("Erro ao processar login:", e)
        erro.value = e.response?.data?.erro || 'Erro ao entrar no sistema'
        setTimeout(() => { erro.value = '' }, 3000)
        carregando.value = false
    }
}
</script>

<style></style>
