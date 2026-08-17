import { defineStore } from "pinia"
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
    
    const token = ref(localStorage.getItem('token') || '')
    
    // MEXI AQUI: Verificação extra para evitar o erro de SyntaxError
    const usuarioLocalStorage = localStorage.getItem('usuario')
    const usuario = ref(
        usuarioLocalStorage && usuarioLocalStorage !== "undefined" 
        ? JSON.parse(usuarioLocalStorage) 
        : null
    )

    function salvarLogin(accessToken: string, dadosUsuario: any) {
        token.value = accessToken
        usuario.value = dadosUsuario

        localStorage.setItem('token', accessToken)
        localStorage.setItem('usuario', JSON.stringify(dadosUsuario))
    }

    function logout() {
        token.value = ''
        usuario.value = null

        localStorage.removeItem('token')
        localStorage.removeItem('usuario')
    }

    return { token, usuario, salvarLogin, logout }
})