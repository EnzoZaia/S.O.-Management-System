<template>
  <div class="min-h-screen flex">
    <div class="hidden md:flex w-2/5 bg-blue-800 flex-col items-center justify-center gap-6 p-8 shrink-0">
      <img src="@/assets/img/FHO.png" alt="Logo da FHO" class="w-24 h-24 object-contain" />
      <div class="text-center">
        <h1 class="text-white text-2xl font-bold">Fundação Hermínio Ometto</h1>
        <p class="text-blue-200 text-sm mt-2">Sistema de Ordem de Serviço</p>
      </div>
    </div>

    <div class="flex-1 flex flex-col items-center justify-center px-6 py-10 bg-white">
      <div class="w-full max-w-md">
        <!-- Estado: cadastro enviado (conta pendente) -->
        <div v-if="cadastroEnviado" class="text-center space-y-5" data-testid="cadastro-enviado">
          <div class="w-20 h-20 mx-auto bg-blue-100 rounded-full flex items-center justify-center border border-blue-200">
            <span class="text-4xl">📧</span>
          </div>
          <h2 class="text-blue-800 text-2xl font-bold">Confirme seu e-mail</h2>
          <p class="text-sm text-gray-500 leading-relaxed">
            Enviamos um link de confirmação para
            <strong class="text-gray-800">{{ emailCadastrado }}</strong>.
            Sua conta ficará pendente até a confirmação. O link expira em 24 horas.
          </p>

          <p v-if="reenvio.sucesso.value" class="text-sm font-semibold text-emerald-600">
            Novo e-mail enviado! Verifique também a caixa de spam.
          </p>
          <p v-if="reenvio.erro.value" class="text-sm font-semibold text-red-600">{{ reenvio.erro.value }}</p>

          <button
            type="button"
            @click="reenvio.reenviar(emailCadastrado)"
            :disabled="reenvio.enviando.value || reenvio.segundosRestantes.value > 0"
            class="w-full border border-blue-800 text-blue-800 py-3 rounded-lg font-semibold hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {{
              reenvio.enviando.value
                ? 'Enviando...'
                : reenvio.segundosRestantes.value > 0
                  ? `Reenviar em ${reenvio.segundosRestantes.value}s`
                  : 'Reenviar e-mail de confirmação'
            }}
          </button>
          <button type="button" @click="router.push('/')" class="w-full bg-blue-800 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 cursor-pointer">
            Voltar para o login
          </button>
        </div>

        <!-- Estado: formulário -->
        <template v-else>
          <h2 class="text-blue-800 text-2xl font-bold mb-1">Criar conta</h2>
          <p class="text-gray-400 text-sm mb-6">Cadastre-se para abrir e acompanhar solicitações de manutenção</p>

          <div v-if="erroGeral" role="alert" class="mb-4 bg-red-50 border border-red-200 text-red-700 text-sm font-medium rounded-lg px-4 py-3">
            {{ erroGeral }}
          </div>

          <form @submit.prevent="enviar" novalidate class="flex flex-col gap-4">
            <div class="flex flex-col gap-1">
              <label for="nome" class="text-xs font-semibold text-gray-600 uppercase tracking-wide">Nome completo</label>
              <input id="nome" v-model="form.nome" @blur="validarCampo('nome')" type="text" autocomplete="name" placeholder="Ex: João da Silva"
                :class="classeInput('nome')" />
              <p v-if="erros.nome" class="text-xs font-medium text-red-600">{{ erros.nome }}</p>
            </div>

            <div class="flex flex-col gap-1">
              <label for="email" class="text-xs font-semibold text-gray-600 uppercase tracking-wide">E-mail</label>
              <input id="email" v-model="form.email" @blur="validarCampo('email')" type="email" autocomplete="email" placeholder="seu.email@fho.edu.br"
                :class="classeInput('email')" />
              <p v-if="erros.email" class="text-xs font-medium text-red-600">{{ erros.email }}</p>
            </div>

            <div class="flex flex-col gap-1">
              <label for="senha" class="text-xs font-semibold text-gray-600 uppercase tracking-wide">Senha inicial</label>
              <div class="relative">
                <input id="senha" v-model="form.senha" @blur="validarCampo('senha')" :type="mostrarSenha ? 'text' : 'password'" autocomplete="new-password"
                  placeholder="Mínimo de 8 caracteres" :class="[classeInput('senha'), 'pr-12']" />
                <button type="button" @click="mostrarSenha = !mostrarSenha" class="absolute inset-y-0 right-0 px-3 text-xs font-bold text-gray-500 hover:text-blue-700 cursor-pointer"
                  :aria-label="mostrarSenha ? 'Ocultar senha' : 'Mostrar senha'">
                  {{ mostrarSenha ? 'Ocultar' : 'Mostrar' }}
                </button>
              </div>
              <p v-if="erros.senha" class="text-xs font-medium text-red-600">{{ erros.senha }}</p>
            </div>

            <div class="flex flex-col gap-1">
              <label for="confirmarSenha" class="text-xs font-semibold text-gray-600 uppercase tracking-wide">Confirmar senha</label>
              <input id="confirmarSenha" v-model="form.confirmarSenha" @blur="validarCampo('confirmarSenha')" :type="mostrarSenha ? 'text' : 'password'"
                autocomplete="new-password" placeholder="Repita a senha" :class="classeInput('confirmarSenha')" />
              <p v-if="erros.confirmarSenha" class="text-xs font-medium text-red-600">{{ erros.confirmarSenha }}</p>
            </div>

            <button type="submit" :disabled="carregando"
              class="bg-blue-800 text-white py-3 rounded-lg font-semibold mt-2 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer">
              {{ carregando ? 'Cadastrando...' : 'Criar conta' }}
            </button>

            <button type="button" @click="router.push('/')"
              class="border border-blue-800 text-blue-800 py-3 rounded-lg font-semibold hover:bg-blue-50 cursor-pointer">
              Já tenho conta
            </button>
          </form>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { cadastrarSolicitante, normalizarErroApi } from '@/services/cadastroService'
import { useReenvioConfirmacao } from '@/composables/useReenvioConfirmacao'
import { normalizarEmail, validarCadastro } from '@/utils/validacaoCadastro'
import type { CampoCadastro, ErrosCadastro, FormularioCadastro } from '@/types/cadastro'

const router = useRouter()
const reenvio = useReenvioConfirmacao()

const form = reactive<FormularioCadastro>({ nome: '', email: '', senha: '', confirmarSenha: '' })
const erros = ref<ErrosCadastro>({})
const erroGeral = ref('')
const carregando = ref(false)
const mostrarSenha = ref(false)
const cadastroEnviado = ref(false)
const emailCadastrado = ref('')

function classeInput(campo: CampoCadastro) {
  return [
    'border rounded-lg px-4 py-3 text-sm outline-none w-full focus:border-blue-600',
    erros.value[campo] ? 'border-red-500 focus:border-red-500' : 'border-gray-300',
  ]
}

function validarCampo(campo: CampoCadastro) {
  const resultado = validarCadastro(form)
  const proximo = { ...erros.value }
  if (resultado[campo]) proximo[campo] = resultado[campo]
  else delete proximo[campo]
  erros.value = proximo
}

async function enviar() {
  erroGeral.value = ''
  erros.value = validarCadastro(form)
  if (Object.keys(erros.value).length > 0) return

  carregando.value = true
  try {
    const email = normalizarEmail(form.email)
    await cadastrarSolicitante({ nome: form.nome.trim(), email, senha: form.senha })
    emailCadastrado.value = email
    cadastroEnviado.value = true
    form.senha = ''
    form.confirmarSenha = ''
  } catch (e) {
    const erro = normalizarErroApi(e, 'Não foi possível concluir o cadastro. Tente novamente.')
    erros.value = erro.campos
    // Sem erro por campo (ex.: falha de rede/servidor), mostra a mensagem geral.
    if (Object.keys(erro.campos).length === 0) erroGeral.value = erro.mensagem
  } finally {
    carregando.value = false
  }
}
</script>