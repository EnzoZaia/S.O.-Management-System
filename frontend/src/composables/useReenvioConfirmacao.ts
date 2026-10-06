import { onBeforeUnmount, ref } from 'vue'
import { normalizarErroApi, reenviarConfirmacao } from '@/services/cadastroService'
import { validarEmail, normalizarEmail } from '@/utils/validacaoCadastro'

const INTERVALO_SEGUNDOS = 60

/** Reenvio do e-mail de confirmação com validação, estado de envio e intervalo entre tentativas. */
export function useReenvioConfirmacao() {
  const enviando = ref(false)
  const sucesso = ref(false)
  const erro = ref('')
  const segundosRestantes = ref(0)
  let timer: ReturnType<typeof setInterval> | null = null

  function iniciarContagem() {
    segundosRestantes.value = INTERVALO_SEGUNDOS
    if (timer) clearInterval(timer)
    timer = setInterval(() => {
      segundosRestantes.value -= 1
      if (segundosRestantes.value <= 0 && timer) {
        clearInterval(timer)
        timer = null
      }
    }, 1000)
  }

  async function reenviar(email: string) {
    erro.value = ''
    sucesso.value = false

    const erroEmail = validarEmail(email)
    if (erroEmail) {
      erro.value = erroEmail
      return
    }

    enviando.value = true
    try {
      await reenviarConfirmacao(normalizarEmail(email))
      sucesso.value = true
      iniciarContagem()
    } catch (e) {
      erro.value = normalizarErroApi(e, 'Não foi possível reenviar o e-mail de confirmação.').mensagem
    } finally {
      enviando.value = false
    }
  }

  onBeforeUnmount(() => {
    if (timer) clearInterval(timer)
  })

  return { enviando, sucesso, erro, segundosRestantes, reenviar }
}