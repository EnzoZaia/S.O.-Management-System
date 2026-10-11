<template>
  <div class="p-8 max-w-2xl mx-auto">
    <div class="mb-8 flex items-center gap-4">
      <button @click="voltar"
        class="p-2.5 bg-white border border-gray-200 hover:bg-gray-50 hover:border-blue-300 text-gray-600 hover:text-blue-600 rounded-full shadow-sm transition-all cursor-pointer"
        title="Voltar às solicitações" aria-label="Voltar">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"></path></svg>
      </button>
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Avaliar atendimento</h1>
        <p class="text-sm text-gray-500 mt-1">Sua opinião ajuda a melhorar os serviços de manutenção</p>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center p-12">
      <p class="text-gray-400 font-medium animate-pulse">A carregar...</p>
    </div>

    <div v-else-if="erroCarga" class="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
      <p class="text-sm font-semibold text-red-700 mb-3">{{ erroCarga }}</p>
      <button @click="carregar" class="px-4 py-2 text-xs font-bold text-red-700 bg-white border border-red-200 rounded-lg hover:bg-red-100 cursor-pointer">Tentar novamente</button>
    </div>

    <div v-else-if="ordem" class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="p-6 border-b border-gray-100 bg-gray-50">
        <p class="text-xs font-bold text-gray-400 uppercase tracking-wider">OS #{{ ordem.id_ordem_servico }}</p>
        <p class="text-sm font-bold text-gray-800 mt-1">{{ ordem.predio_nome || 'Local não informado' }} <span class="font-medium text-gray-500">- {{ ordem.localizacao_nome || 'N/I' }}</span></p>
        <p class="text-xs text-gray-600 mt-1">{{ extrairProblema(ordem.descricao_servico) }}</p>
        <p v-if="nomeTecnico(ordem)" class="text-[11px] font-semibold text-gray-500 mt-2">👷 Técnico: {{ nomeTecnico(ordem) }}</p>
      </div>

      <!-- Avaliação já enviada (CA3): somente leitura -->
      <div v-if="modo === 'avaliada' && avaliacao" class="p-6 space-y-4 text-center" data-testid="avaliacao-registrada">
        <p class="text-[11px] font-black text-emerald-700 uppercase tracking-wider">Avaliação registrada</p>
        <EstrelasAvaliacao :model-value="avaliacao.nota" readonly />
        <p class="text-sm font-bold text-gray-800">{{ ROTULOS_NOTA[avaliacao.nota] }}</p>
        <p v-if="avaliacao.comentario" class="text-sm text-gray-600 italic">"{{ avaliacao.comentario }}"</p>
        <p class="text-xs text-gray-400 font-semibold">
          por {{ avaliacao.avaliado_por_nome || 'solicitante' }} em {{ formatarDataHora(avaliacao.dt_avaliacao) }}
        </p>
        <p class="text-xs text-gray-500">Cada atendimento pode ser avaliado uma única vez.</p>
        <button @click="voltar" class="px-5 py-2.5 text-sm font-bold text-gray-700 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl cursor-pointer">Voltar às solicitações</button>
      </div>

      <!-- Ordem sem avaliação disponível -->
      <div v-else-if="modo === 'indisponivel'" class="p-8 text-center space-y-3" data-testid="avaliacao-indisponivel">
        <span class="text-5xl block opacity-60">🔒</span>
        <p class="text-sm font-bold text-gray-800">Avaliação indisponível</p>
        <p class="text-xs text-gray-500">A avaliação só é liberada depois que você aprova a resolução do serviço.</p>
        <button @click="voltar" class="px-5 py-2.5 text-sm font-bold text-gray-700 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl cursor-pointer">Voltar às solicitações</button>
      </div>

      <!-- Formulário (CA1/CA2) -->
      <div v-else class="p-6 space-y-6" data-testid="avaliacao-formulario">
        <div class="text-center space-y-3">
          <p class="text-sm font-bold text-gray-800">Como foi o atendimento?</p>
          <EstrelasAvaliacao v-model="nota" @update:model-value="erroNota = ''" />
          <p class="text-sm font-bold h-5" :class="nota ? 'text-amber-600' : 'text-transparent'">{{ nota ? ROTULOS_NOTA[nota] : '-' }}</p>
          <p v-if="erroNota" role="alert" class="text-xs font-medium text-red-600">{{ erroNota }}</p>
        </div>

        <div class="space-y-1.5">
          <label for="comentario" class="text-xs font-bold text-gray-500 uppercase tracking-wider">Comentário (opcional)</label>
          <textarea id="comentario" v-model="comentario" @blur="validarCom" rows="3" :maxlength="COMENTARIO_MAX"
            placeholder="Conte como foi sua experiência..."
            :class="erroComentario ? 'border-red-500 focus:ring-red-400' : 'border-gray-200 focus:ring-blue-500'"
            class="w-full bg-gray-50 border text-gray-700 text-sm rounded-lg p-3 outline-none focus:ring-2 resize-none"></textarea>
          <div class="flex justify-between text-[11px]">
            <span class="text-red-600 font-medium">{{ erroComentario }}</span>
            <span class="text-gray-400 font-semibold">{{ comentario.trim().length }}/{{ COMENTARIO_MAX }}</span>
          </div>
        </div>

        <div class="bg-blue-50 border border-blue-100 rounded-xl p-4 text-xs text-blue-800 font-semibold">
          Ao enviar, a ordem será encerrada e a sua nota passará a compor os indicadores de satisfação.
        </div>

        <div class="flex justify-end gap-3">
          <button @click="voltar" :disabled="enviando" class="px-5 py-2.5 text-sm font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl cursor-pointer disabled:opacity-50">Agora não</button>
          <button @click="enviar" :disabled="enviando"
            class="px-5 py-2.5 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
            {{ enviando ? 'Enviando...' : 'Enviar avaliação' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Swal from 'sweetalert2'
import EstrelasAvaliacao from '@/components/EstrelasAvaliacao.vue'
import { AvaliacaoError, buscarAvaliacao, buscarOrdem, enviarAvaliacao } from '@/services/portalService'
import type { AvaliacaoRegistrada, ErroAvaliacao, OrdemPortal } from '@/types/portal'
import { extrairProblema, formatarDataHora, nomeTecnico, podeAvaliar } from '@/utils/statusOrdem'
import { COMENTARIO_MAX, ROTULOS_NOTA, validarComentario, validarNota } from '@/utils/validacaoAvaliacao'

const route = useRoute()
const router = useRouter()

const idOrdem = computed(() => Number(route.params.id))
const ordem = ref<OrdemPortal | null>(null)
const avaliacao = ref<AvaliacaoRegistrada | null>(null)
const loading = ref(true)
const erroCarga = ref('')

const nota = ref<number | null>(null)
const comentario = ref('')
const erroNota = ref('')
const erroComentario = ref('')
const enviando = ref(false)

const modo = computed<'avaliada' | 'formulario' | 'indisponivel'>(() => {
  if (avaliacao.value) return 'avaliada'
  if (ordem.value && podeAvaliar(ordem.value)) return 'formulario'
  return 'indisponivel'
})

function voltar() {
  router.push('/dashboard-solicitante/portal')
}

function validarCom() {
  erroComentario.value = validarComentario(comentario.value) ?? ''
}

async function carregar() {
  loading.value = true
  erroCarga.value = ''
  if (!Number.isInteger(idOrdem.value) || idOrdem.value <= 0) {
    erroCarga.value = 'Ordem de serviço inválida.'
    loading.value = false
    return
  }
  try {
    const [os, av] = await Promise.all([buscarOrdem(idOrdem.value), buscarAvaliacao(idOrdem.value)])
    ordem.value = os
    avaliacao.value = av
  } catch (e) {
    console.error('Erro ao carregar avaliação', e)
    erroCarga.value = 'Não foi possível carregar a ordem. Tente novamente.'
  } finally {
    loading.value = false
  }
}

const MENSAGENS_BLOQUEIO: Record<ErroAvaliacao['tipo'], { titulo: string; texto: string }> = {
  JA_AVALIADA: { titulo: 'Atendimento já avaliado', texto: 'Esta ordem já foi avaliada e não pode ser avaliada novamente. A avaliação registrada está exibida.' },
  STATUS_INVALIDO: { titulo: 'Ação indisponível', texto: 'A avaliação só é liberada depois da aprovação da resolução do serviço.' },
  SEM_PERMISSAO: { titulo: 'Sem permissão', texto: 'Somente o solicitante pode avaliar este atendimento.' },
  GENERICO: { titulo: 'Erro', texto: 'Não foi possível registrar a avaliação. Tente novamente.' },
}

// CA3: bloqueio. Sincroniza a tela com o que já está registrado e explica o motivo.
async function tratarBloqueio(info: ErroAvaliacao) {
  if (info.tipo === 'JA_AVALIADA') {
    avaliacao.value = info.avaliacao ?? (await buscarAvaliacao(idOrdem.value))
  }
  if (info.tipo !== 'GENERICO' && info.tipo !== 'SEM_PERMISSAO') {
    try { ordem.value = await buscarOrdem(idOrdem.value) } catch { /* mantém o que já está na tela */ }
  }
  const { titulo, texto } = MENSAGENS_BLOQUEIO[info.tipo]
  await Swal.fire({
    title: titulo,
    text: info.tipo === 'GENERICO' ? info.mensagem || texto : texto,
    icon: info.tipo === 'GENERICO' ? 'error' : 'info',
    confirmButtonColor: '#2563eb',
  })
}

async function enviar() {
  if (enviando.value) return
  const valorNota = nota.value
  erroNota.value = validarNota(valorNota) ?? '' // CA2
  erroComentario.value = validarComentario(comentario.value) ?? ''
  if (valorNota === null || erroNota.value || erroComentario.value) return

  enviando.value = true
  try {
    const texto = comentario.value.trim()
    const resposta = await enviarAvaliacao(idOrdem.value, { nota: valorNota, comentario: texto || undefined })
    avaliacao.value = resposta.avaliacao ?? (await buscarAvaliacao(idOrdem.value))
    await Swal.fire({
      title: 'Obrigado pela avaliação!',
      text: 'Sua avaliação foi registrada e a ordem foi encerrada.',
      icon: 'success',
      timer: 2500,
      showConfirmButton: false,
    }) // CA1
    voltar()
  } catch (e) {
    if (e instanceof AvaliacaoError) await tratarBloqueio(e.info)
    else {
      console.error('Erro ao enviar avaliação', e)
      Swal.fire({ title: 'Erro', text: 'Não foi possível registrar a avaliação. Tente novamente.', icon: 'error' })
    }
  } finally {
    enviando.value = false
  }
}

onMounted(carregar)
</script>