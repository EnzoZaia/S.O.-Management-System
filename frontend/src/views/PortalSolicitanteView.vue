<template>
  <div class="p-8">
    <div class="mb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Minhas Solicitações</h1>
        <p class="text-sm text-gray-500 mt-1">Acompanhe a situação de cada atendimento</p>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="ultimaAtualizacao" class="text-[11px] text-gray-400 font-semibold">Atualizado às {{ ultimaAtualizacao }}</span>
        <button @click="router.push('/abrir-os')" class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-lg shadow-md transition-colors cursor-pointer">+ Nova Solicitação</button>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex flex-wrap items-center gap-3 mb-6">
      <button v-for="f in filtros" :key="f.valor" @click="filtro = f.valor"
        :class="filtro === f.valor ? 'bg-blue-600 text-white border-blue-600' : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'"
        class="px-4 py-2 text-xs font-bold rounded-full border transition-colors cursor-pointer">
        {{ f.rotulo }}
        <span class="ml-1 opacity-80">({{ contagem(f.valor) }})</span>
      </button>
      <div class="relative flex-1 min-w-[200px]">
        <span class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400 text-sm">🔍</span>
        <input v-model="busca" type="text" placeholder="Buscar por nº, local ou descrição..." class="w-full bg-gray-50 border border-gray-200 text-gray-700 placeholder-gray-400 text-xs font-medium rounded-lg pl-9 pr-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
    </div>

    <div v-if="loading && ordens.length === 0" class="bg-white rounded-xl border border-gray-100 p-12 text-center text-gray-400 font-medium">A carregar solicitações...</div>
    <div v-else-if="erro" class="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
      <p class="text-sm font-semibold text-red-700 mb-3">{{ erro }}</p>
      <button @click="carregar(true)" class="px-4 py-2 text-xs font-bold text-red-700 bg-white border border-red-200 rounded-lg hover:bg-red-100 cursor-pointer">Tentar novamente</button>
    </div>
    <div v-else-if="ordensFiltradas.length === 0" class="bg-white rounded-xl border border-gray-100 p-12 text-center">
      <span class="text-5xl block mb-3 opacity-50">📭</span>
      <p class="text-gray-500 font-semibold">{{ ordens.length === 0 ? 'Você ainda não tem solicitações.' : 'Nenhuma solicitação com os filtros atuais.' }}</p>
    </div>

    <div v-else class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <button v-for="os in ordensFiltradas" :key="os.id_ordem_servico" @click="abrirDetalhes(os)"
        class="text-left bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:border-blue-200 transition-all p-5 cursor-pointer">
        <div class="flex items-start justify-between gap-3 mb-3">
          <div class="flex items-center gap-2">
            <span class="text-xs font-black px-2 py-0.5 bg-gray-100 text-gray-700 rounded-md">OS #{{ os.id_ordem_servico }}</span>
            <span v-if="os.prioridade_urgencia === 'SIM'" class="text-[10px] font-bold px-2 py-0.5 bg-red-100 text-red-700 rounded-md">🚨 Urgente</span>
            <span v-if="os.vinculo_presenciei" class="text-[10px] font-bold px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-md">👁️ Presenciei</span>
          </div>
          <span :class="infoStatus(os.status_ordem_servico).classes" class="px-3 py-1 rounded-full text-[11px] font-bold border whitespace-nowrap">
            {{ infoStatus(os.status_ordem_servico).icone }} {{ infoStatus(os.status_ordem_servico).rotulo }}
          </span>
        </div>
        <p class="text-sm font-bold text-gray-800 truncate">{{ os.predio_nome || 'Local não informado' }} <span class="font-medium text-gray-500">- {{ os.localizacao_nome || 'N/I' }}</span></p>
        <p class="text-xs text-gray-600 mt-1 line-clamp-2">{{ extrairProblema(os.descricao_servico) }}</p>
        <div class="flex items-center justify-between mt-4 pt-3 border-t border-gray-100 text-[11px] text-gray-500 font-semibold">
          <span>Aberta em {{ formatarData(os.dt_abertura) }}</span>
          <span v-if="nomeTecnico(os)">👷 {{ nomeTecnico(os) }}</span>
          <span v-else class="text-gray-400">Sem técnico atribuído</span>
        </div>
        <p v-if="acoesPermitidas(os).validar" class="mt-3 text-[11px] font-bold text-blue-700 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">Ação necessária: valide o serviço executado.</p>
      </button>
    </div>

    <div v-if="selecionada" @click.self="fecharDetalhes" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 animate-fade-in">
      <div class="bg-white rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50 shrink-0">
          <div>
            <p class="text-xs font-bold text-gray-400 uppercase tracking-wider">Acompanhamento</p>
            <h2 class="text-2xl font-bold text-gray-800 mt-1">OS #{{ selecionada.id_ordem_servico }}</h2>
          </div>
          <button @click="fecharDetalhes" class="text-gray-400 hover:text-gray-700 p-2 rounded-full hover:bg-gray-200 transition-colors cursor-pointer" aria-label="Fechar">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>

        <div class="p-6 overflow-y-auto space-y-6">
          <div :class="infoStatus(selecionada.status_ordem_servico).classes" class="rounded-xl border p-4 flex items-start gap-3">
            <span class="text-2xl">{{ infoStatus(selecionada.status_ordem_servico).icone }}</span>
            <div>
              <p class="text-sm font-black">{{ infoStatus(selecionada.status_ordem_servico).rotulo }}</p>
              <p class="text-xs mt-0.5">{{ infoStatus(selecionada.status_ordem_servico).descricao }}</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
              <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Local</p>
              <p class="text-sm font-bold text-gray-800">{{ selecionada.predio_nome || 'N/I' }} - {{ selecionada.localizacao_nome || 'N/I' }}</p>
            </div>
            <div class="bg-white p-4 rounded-xl border border-blue-100 shadow-sm">
              <p class="text-[11px] font-bold text-blue-600 uppercase tracking-wider mb-1">Técnico responsável</p>
              <p v-if="nomeTecnico(selecionada)" class="text-sm font-bold text-gray-800">{{ nomeTecnico(selecionada) }}</p>
              <p v-else class="text-sm font-medium text-gray-400">Será exibido após a atribuição</p>
            </div>
            <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
              <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Aberta em</p>
              <p class="text-sm font-bold text-gray-800">{{ formatarDataHora(selecionada.dt_abertura) }}</p>
            </div>
            <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
              <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Prioridade</p>
              <p class="text-sm font-bold text-gray-800">{{ selecionada.prioridade_urgencia === 'SIM' ? '🚨 Urgente' : 'Normal' }}</p>
            </div>
          </div>

          <div>
            <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Problema reportado</p>
            <div class="p-4 bg-gray-50 rounded-xl border border-gray-100 text-sm text-gray-700 whitespace-pre-wrap">{{ extrairProblema(selecionada.descricao_servico) }}</div>
          </div>

          <div>
            <h3 class="text-sm font-bold text-gray-700 mb-4">⏱️ Histórico</h3>
            <div class="bg-gray-50/50 rounded-2xl border border-gray-100 p-5">
              <div v-if="loadingHistorico" class="text-center text-gray-400 font-medium py-6">A buscar registos...</div>
              <div v-else-if="erroHistorico" class="text-center text-sm text-red-600 font-semibold py-6">{{ erroHistorico }}</div>
              <div v-else-if="historico.length === 0" class="text-center text-gray-400 font-medium py-6">Nenhum registo para esta solicitação.</div>
              <div v-else class="relative border-l-2 border-blue-200 ml-3 pl-6 space-y-5">
                <div v-for="ev in historico" :key="ev.id_historico_ordem_servico" class="relative">
                  <div class="absolute w-3 h-3 rounded-full bg-blue-500 border-2 border-white -left-[31px] top-1.5 shadow-sm"></div>
                  <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <p class="text-[10px] font-bold text-gray-500 mb-1">{{ formatarDataHora(ev.data_registro) }}</p>
                    <p class="text-sm font-semibold text-gray-800">{{ formatarEvento(ev).principal }}</p>
                    <p v-if="formatarEvento(ev).detalhe" class="mt-2 text-xs text-gray-600 italic">"{{ formatarEvento(ev).detalhe }}"</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="p-5 border-t border-gray-100 bg-gray-50 shrink-0 space-y-3">
          <div v-if="acoes.validar" class="flex flex-col sm:flex-row gap-3">
            <button @click="reprovarServico" :disabled="enviando" class="flex-1 px-5 py-2.5 text-sm font-bold text-red-600 bg-red-50 border border-red-200 hover:bg-red-100 rounded-xl transition-colors cursor-pointer disabled:opacity-50">👎 Reprovar serviço</button>
            <button @click="aprovarServico" :disabled="enviando" class="flex-1 px-5 py-2.5 text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition-colors shadow-sm cursor-pointer disabled:opacity-50">👍 Aprovar serviço</button>
          </div>
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex flex-wrap gap-2">
              <button v-if="acoes.evidencia" @click="emBreve('Envio de evidências')" class="px-4 py-2 text-xs font-bold text-indigo-600 bg-white border border-indigo-200 hover:bg-indigo-50 rounded-lg cursor-pointer">📎 Anexar evidência</button>
              <button v-if="acoes.avaliar" @click="emBreve('Avaliação do atendimento')" class="px-4 py-2 text-xs font-bold text-amber-600 bg-white border border-amber-200 hover:bg-amber-50 rounded-lg cursor-pointer">⭐ Avaliar atendimento</button>
            </div>
            <button @click="fecharDetalhes" class="px-5 py-2 text-sm font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl cursor-pointer">Fechar</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import Swal from 'sweetalert2'
import { buscarHistoricoOrdem, listarMinhasOrdens, validarOrdem } from '@/services/portalService'
import type { EventoHistorico, FiltroStatusPortal, OrdemPortal } from '@/types/portal'
import {
  acoesPermitidas, extrairProblema, formatarData, formatarDataHora, formatarEvento,
  infoStatus, nomeTecnico, pertenceAoFiltro,
} from '@/utils/statusOrdem'

const INTERVALO_ATUALIZACAO_MS = 30_000

const router = useRouter()
const ordens = ref<OrdemPortal[]>([])
const loading = ref(true)
const erro = ref('')
const ultimaAtualizacao = ref('')
const filtro = ref<FiltroStatusPortal>('TODOS')
const busca = ref('')

const selecionada = ref<OrdemPortal | null>(null)
const historico = ref<EventoHistorico[]>([])
const loadingHistorico = ref(false)
const erroHistorico = ref('')
const enviando = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

const filtros: { valor: FiltroStatusPortal; rotulo: string }[] = [
  { valor: 'TODOS', rotulo: 'Todas' },
  { valor: 'EM_ANDAMENTO', rotulo: 'Em andamento' },
  { valor: 'AGUARDANDO_VOCE', rotulo: 'Aguardando validação' },
  { valor: 'FINALIZADAS', rotulo: 'Finalizadas' },
]

const acoes = computed(() => (selecionada.value ? acoesPermitidas(selecionada.value) : { validar: false, evidencia: false, avaliar: false }))

function contagem(f: FiltroStatusPortal) {
  return ordens.value.filter((o) => pertenceAoFiltro(o, f)).length
}

const ordensFiltradas = computed(() => {
  const termo = busca.value.trim().toLowerCase()
  return ordens.value.filter((o) => {
    if (!pertenceAoFiltro(o, filtro.value)) return false
    if (!termo) return true
    return (
      String(o.id_ordem_servico).includes(termo) ||
      (o.predio_nome || '').toLowerCase().includes(termo) ||
      (o.localizacao_nome || '').toLowerCase().includes(termo) ||
      (o.descricao_servico || '').toLowerCase().includes(termo)
    )
  })
})

async function carregar(manual = false) {
  if (manual) loading.value = true
  try {
    ordens.value = await listarMinhasOrdens()
    erro.value = ''
    ultimaAtualizacao.value = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })

    // CA2: se há uma OS aberta no modal, reflete o novo status e histórico.
    if (selecionada.value) {
      const atual = ordens.value.find((o) => o.id_ordem_servico === selecionada.value!.id_ordem_servico)
      if (atual) {
        const mudou = atual.status_ordem_servico !== selecionada.value.status_ordem_servico
        selecionada.value = atual
        if (mudou) await carregarHistorico(atual.id_ordem_servico)
      }
    }
  } catch (e) {
    console.error('Erro ao carregar solicitações', e)
    if (ordens.value.length === 0) erro.value = 'Não foi possível carregar suas solicitações. Tente novamente.'
  } finally {
    loading.value = false
  }
}

async function carregarHistorico(id: number) {
  loadingHistorico.value = true
  erroHistorico.value = ''
  try {
    historico.value = await buscarHistoricoOrdem(id)
  } catch (e) {
    console.error('Erro ao carregar histórico', e)
    historico.value = []
    erroHistorico.value = 'Não foi possível carregar o histórico.'
  } finally {
    loadingHistorico.value = false
  }
}

async function abrirDetalhes(os: OrdemPortal) {
  selecionada.value = os
  historico.value = []
  await carregarHistorico(os.id_ordem_servico)
}

function fecharDetalhes() {
  selecionada.value = null
  historico.value = []
}

// CA4 — o endpoint de validação virá com as US06/US07; o tratamento de erro já está pronto.
async function aprovarServico() {
  if (!selecionada.value) return
  const r = await Swal.fire({ title: 'Aprovar serviço?', text: 'Confirma que o problema foi resolvido?', icon: 'question', showCancelButton: true, confirmButtonColor: '#059669', confirmButtonText: 'Sim, aprovar', cancelButtonText: 'Cancelar' })
  if (r.isConfirmed) await enviarValidacao(true)
}

async function reprovarServico() {
  if (!selecionada.value) return
  const r = await Swal.fire({ title: 'Reprovar serviço', input: 'textarea', inputLabel: 'Explique o que ainda não foi resolvido', inputValidator: (v) => (!v?.trim() ? 'Informe o motivo da reprovação.' : null), showCancelButton: true, confirmButtonColor: '#dc2626', confirmButtonText: 'Reprovar', cancelButtonText: 'Cancelar' })
  if (r.isConfirmed) await enviarValidacao(false, String(r.value).trim())
}

async function enviarValidacao(aprovada: boolean, justificativa?: string) {
  if (!selecionada.value) return
  enviando.value = true
  try {
    await validarOrdem(selecionada.value.id_ordem_servico, { aprovada, justificativa })
    await Swal.fire({ title: aprovada ? 'Serviço aprovado!' : 'Serviço reprovado', text: aprovada ? 'Obrigado pela confirmação.' : 'A ordem retornará ao técnico responsável.', icon: 'success', timer: 2500, showConfirmButton: false })
    await carregar()
    if (selecionada.value) await carregarHistorico(selecionada.value.id_ordem_servico)
  } catch (e) {
    console.error('Erro na validação', e)
    Swal.fire({ title: 'Erro', text: 'Não foi possível registrar a validação. Tente novamente.', icon: 'error' })
  } finally {
    enviando.value = false
  }
}

function emBreve(nome: string) {
  Swal.fire({ title: nome, text: 'Esta funcionalidade estará disponível em breve.', icon: 'info', confirmButtonColor: '#2563eb' })
}

onMounted(() => {
  carregar(true)
  timer = setInterval(() => carregar(), INTERVALO_ATUALIZACAO_MS)
})
onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.animate-fade-in { animation: fadeIn 0.2s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
</style>