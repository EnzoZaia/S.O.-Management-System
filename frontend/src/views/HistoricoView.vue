<template>
  <div class="h-full flex flex-col p-6 bg-gray-100/50">
    
    <div class="mb-4 shrink-0">
      <div class="flex justify-between items-end mb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">Auditoria e Histórico</h1>
          <p class="text-sm text-gray-500 mt-1">Selecione uma Ordem de Serviço para rastrear toda a sua linha do tempo</p>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex flex-wrap items-end gap-4">
        
        <div class="flex flex-col">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider">Abertas a partir de:</label>
          <input type="date" v-model="filtroDataInicio" class="appearance-none bg-gray-50/50 border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-4 py-2.5 outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 hover:border-blue-300 transition-all cursor-pointer shadow-sm" />
        </div>
        
        <div class="flex flex-col">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider">Até:</label>
          <input type="date" v-model="filtroDataFim" class="appearance-none bg-gray-50/50 border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-4 py-2.5 outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 hover:border-blue-300 transition-all cursor-pointer shadow-sm" />
        </div>

        <div class="flex flex-col relative min-w-[140px]">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider">Tipo:</label>
          <select v-model="filtroTipo" class="appearance-none w-full bg-gray-50/50 border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-4 py-2.5 pr-8 outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 hover:border-blue-300 transition-all cursor-pointer shadow-sm bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%239CA3AF%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E')] bg-[length:16px_16px] bg-[position:right_12px_center] bg-no-repeat">
            <option value="TODOS">Todos</option>
            <option value="CORRETIVA">Corretiva</option>
            <option value="PREVENTIVA">Preventiva</option>
          </select>
        </div>

        <div class="flex flex-col relative min-w-[160px]">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider">Status:</label>
          <select v-model="filtroStatus" class="appearance-none w-full bg-gray-50/50 border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-4 py-2.5 pr-8 outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 hover:border-blue-300 transition-all cursor-pointer shadow-sm bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%239CA3AF%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E')] bg-[length:16px_16px] bg-[position:right_12px_center] bg-no-repeat">
            <option value="TODOS">Todos</option>
            <option value="ABERTA">Aberta</option>
            <option value="APROVADA">Para Iniciar</option>
            <option value="EM_EXECUCAO">Em Execução</option>
            <option value="AGUARDANDO_MATERIAL">Aguard. Material</option>
            <option value="AGUARDANDO_TERCEIRO">Aguard. Terceiro</option>
            <option value="CONCLUIDA">Concluída</option>
            <option value="ENCERRADA">Encerrada</option>
            <option value="CANCELADA">Cancelada</option>
            <option value="REPROVADA">Reprovada</option>
          </select>
        </div>

        <div class="flex flex-col relative min-w-[140px]">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider">Prioridade:</label>
          <select v-model="filtroPrioridade" class="appearance-none w-full bg-gray-50/50 border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-4 py-2.5 pr-8 outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 hover:border-blue-300 transition-all cursor-pointer shadow-sm bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%239CA3AF%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E')] bg-[length:16px_16px] bg-[position:right_12px_center] bg-no-repeat">
            <option value="TODAS">Todas</option>
            <option value="SIM">Urgente</option>
            <option value="NAO">Normal</option>
          </select>
        </div>

        <div class="flex flex-col relative min-w-[150px]">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider">Prédio:</label>
          <select v-model="filtroPredio" class="appearance-none w-full bg-gray-50/50 border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-4 py-2.5 pr-8 outline-none focus:bg-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 hover:border-blue-300 transition-all cursor-pointer shadow-sm truncate bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%239CA3AF%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E')] bg-[length:16px_16px] bg-[position:right_12px_center] bg-no-repeat">
            <option value="TODOS">Todos</option>
            <option v-for="predio in prediosUnicos" :key="predio" :value="predio">{{ predio }}</option>
          </select>
        </div>

        <button @click="limparFiltros" class="px-5 py-2.5 text-xs font-bold text-gray-600 bg-gray-100 border border-gray-200 hover:bg-gray-200 hover:text-gray-800 rounded-lg transition-colors cursor-pointer ml-auto shadow-sm">
          Limpar Filtros
        </button>
      </div>
    </div>

    <div class="flex-1 flex gap-6 min-h-0">
      
      <div class="w-1/3 max-w-sm flex flex-col bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        
        <div class="p-4 border-b border-gray-100 bg-gray-50 shrink-0">
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400 text-sm">🔍</span>
            <input v-model="termoBusca" type="text" placeholder="Buscar OS, Prédio ou Técnico..." class="w-full bg-white border border-gray-200 text-gray-700 placeholder-gray-400 text-xs font-medium rounded-lg pl-9 pr-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 transition-all" />
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-2 space-y-1 bg-gray-50/30">
          <div v-if="loadingOS" class="p-8 text-center text-gray-400 font-medium text-sm">A carregar ordens...</div>
          <div v-else-if="ordensFiltradas.length === 0" class="p-8 text-center text-gray-400 font-medium text-sm">Nenhuma OS encontrada com os filtros atuais.</div>
          
          <button 
            v-else 
            v-for="os in ordensFiltradas" :key="os.id_ordem_servico"
            @click="selecionarOS(os)"
            :class="[
              'w-full text-left p-4 rounded-xl border-l-4 transition-all duration-200 cursor-pointer',
              osSelecionada?.id_ordem_servico === os.id_ordem_servico 
                ? 'bg-blue-50 border-blue-600 shadow-sm' 
                : 'bg-white border-transparent hover:border-blue-300 hover:shadow-sm border border-gray-100'
            ]"
          >
            <div class="flex justify-between items-start mb-2">
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-black px-2 py-0.5 bg-gray-100 text-gray-700 rounded-md">OS #{{ os.id_ordem_servico }}</span>
                <span :class="os.tipo_manutencao === 'PREVENTIVA' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-500'" class="text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider">
                  {{ os.tipo_manutencao === 'PREVENTIVA' ? 'Prev' : 'Corr' }}
                </span>
              </div>
              <span :class="getStatusClass(os.status_ordem_servico)" class="text-[10px] font-bold px-2 py-0.5 rounded-full whitespace-nowrap">{{ formatarStatus(os.status_ordem_servico) }}</span>
            </div>
            <p class="text-sm font-bold text-gray-800 truncate mb-1">{{ os.predio_nome || 'Local não informado' }}</p>
            <p class="text-[10px] text-gray-500 mb-2 font-medium">Aberta em: {{ formatarDataSimples(os.dt_abertura) }}</p>
            <p class="text-xs text-gray-600 truncate" :title="extrairProblema(os.descricao_servico)">{{ extrairProblema(os.descricao_servico) }}</p>
          </button>
        </div>
      </div>

      <div class="flex-1 flex flex-col bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        
        <div v-if="!osSelecionada" class="flex-1 flex flex-col items-center justify-center text-gray-400 bg-gray-50/30">
          <span class="text-6xl mb-4 opacity-50">📋</span>
          <h3 class="text-lg font-bold text-gray-600">Nenhuma OS selecionada</h3>
          <p class="text-sm">Clique em uma Ordem de Serviço na lista ao lado para ver o seu histórico.</p>
        </div>

        <template v-else>
          <div class="p-6 border-b border-gray-100 bg-white shrink-0 shadow-sm z-10">
            <div class="flex justify-between items-center mb-5">
              <div>
                <p class="text-[10px] font-bold text-blue-600 uppercase tracking-wider mb-1">Rastreamento de Ordem</p>
                <h2 class="text-2xl font-black text-gray-800 flex items-center gap-3">
                  OS #{{ osSelecionada.id_ordem_servico }}
                  <span :class="getStatusClass(osSelecionada.status_ordem_servico)" class="text-xs font-bold px-3 py-1 rounded-full border bg-opacity-10">{{ formatarStatus(osSelecionada.status_ordem_servico) }}</span>
                  <span :class="osSelecionada.tipo_manutencao === 'PREVENTIVA' ? 'bg-purple-100 text-purple-700 border-purple-200' : 'bg-gray-100 text-gray-600 border-gray-200'" class="px-3 py-1 rounded-full text-xs font-bold border">
                    {{ osSelecionada.tipo_manutencao === 'PREVENTIVA' ? 'Preventiva' : 'Corretiva' }}
                  </span>
                </h2>
              </div>
              
              <span :class="osSelecionada.prioridade_urgencia === 'SIM' ? 'bg-red-100 text-red-700 border-red-200' : 'bg-gray-100 text-gray-600 border-gray-200'" class="px-4 py-1.5 rounded-full text-xs font-extrabold border shadow-sm">
                {{ osSelecionada.prioridade_urgencia === 'SIM' ? ' URGENTE' : 'Prioridade: Normal' }}
              </span>
            </div>
            
            <div v-if="osSelecionada.tipo_manutencao === 'PREVENTIVA'" class="space-y-4">
              <div class="grid grid-cols-2 gap-4 bg-purple-50/50 p-4 rounded-xl border border-purple-100 shadow-sm">
                <div>
                  <p class="text-[10px] font-black text-purple-600 uppercase tracking-wider mb-1">Última Preventiva Realizada</p>
                  <p class="text-sm font-bold text-gray-800">{{ osSelecionada?.ativo_ultima_preventiva ? formatarDataSimples(osSelecionada.ativo_ultima_preventiva) : 'Nenhum registo anterior' }}</p>
                </div>
                <div>
                  <p class="text-[10px] font-black text-purple-600 uppercase tracking-wider mb-1">Próxima Preventiva Agendada</p>
                  <p class="text-sm font-bold text-purple-700">{{ osSelecionada?.ativo_proxima_preventiva ? formatarDataSimples(osSelecionada.ativo_proxima_preventiva) : 'Não agendada' }}</p>
                </div>
              </div>
              
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 bg-gray-50 p-4 rounded-xl border border-gray-100">
                <div class="col-span-2">
                  <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">Equipamento Alvo</p>
                  <p class="text-sm font-bold text-gray-800">❄️ {{ osSelecionada?.ativo_nome || 'N/I' }}</p>
                  <p class="text-[10px] text-gray-500 font-mono mt-0.5">PAT: {{ osSelecionada?.ativo_patrimonio || 'N/I' }}</p>
                </div>
                <div>
                  <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">Localização / Prédio</p>
                  <p class="text-sm font-bold text-gray-800">{{ osSelecionada?.predio_nome || 'N/I' }}</p>
                  <p class="text-[10px] text-gray-500">{{ osSelecionada?.localizacao_nome || 'N/I' }}</p>
                </div>
                <div>
                  <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">Técnico / Gestor</p>
                  <p class="text-sm font-bold text-gray-800">T: {{ osSelecionada?.tecnico_nome || 'Nenhum' }}</p>
                  <p class="text-[10px] text-gray-500">G: {{ osSelecionada?.gestor_nome || 'Sistema' }}</p>
                </div>
                <div class="col-span-2 md:col-span-4 pt-2 border-t border-gray-200/60 mt-1">
                  <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Roteiro de Inspeção</p>
                  <p class="text-sm text-gray-700">{{ extrairProblema(osSelecionada.descricao_servico) }}</p>
                </div>
              </div>
            </div>

            <div v-else class="grid grid-cols-2 md:grid-cols-4 gap-4 bg-gray-50 p-5 rounded-xl border border-gray-100">
              <div>
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">Localização / Prédio</p>
                <p class="text-sm font-bold text-gray-800">{{ osSelecionada?.predio_nome || 'N/I' }}</p>
                <p class="text-xs text-gray-500">{{ osSelecionada?.localizacao_nome || 'N/I' }}</p>
              </div>
              <div>
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">Técnico Atribuído</p>
                <p class="text-sm font-bold text-gray-800">{{ osSelecionada?.tecnico_nome || 'Aguardando atribuição' }}</p>
              </div>
              <div>
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">Solicitante</p>
                <p class="text-sm font-semibold text-gray-800">{{ extrairSolicitante(osSelecionada) }}</p>
              </div>
              <div>
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">Gestor</p>
                <p class="text-sm font-semibold text-gray-800">{{ osSelecionada.gestor_nome || 'Sem gestor' }}</p>
              </div>
              <div class="col-span-2 md:col-span-4 pt-2 border-t border-gray-200/60 mt-1">
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Problema Reportado</p>
                <p class="text-sm text-gray-700">{{ extrairProblema(osSelecionada.descricao_servico) }}</p>
              </div>
            </div>
          </div>

          <div class="flex-1 overflow-y-auto p-6 bg-gray-50/50">
            <h3 class="text-sm font-bold text-gray-700 mb-6 flex items-center gap-2">
              <span>⏱️</span> Linha do Tempo de Atividades
            </h3>
            
            <div v-if="loadingHistorico" class="text-center text-gray-400 font-medium py-8">A buscar registos...</div>
            <div v-else-if="historicoAtual.length === 0" class="text-center text-gray-400 font-medium py-8">Nenhum histórico registado para esta OS.</div>
            
            <div v-else class="relative border-l-2 border-blue-200 ml-3 pl-6 space-y-6">
              <div v-for="(evento, index) in historicoAtual" :key="index" class="relative group">
                <div class="absolute w-3 h-3 rounded-full bg-blue-500 border-2 border-white -left-[31px] top-1.5 shadow-sm"></div>
                
                <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                  <div class="flex justify-between items-start mb-3">
                    <span class="text-xs font-bold text-gray-800 flex items-center gap-2">
                      <span class="bg-gray-100 p-1 rounded text-gray-500">👤</span> 
                      {{ evento.usuario_nome || 'Sistema Automático' }}
                    </span>
                    <span class="text-[10px] font-bold text-gray-500 bg-gray-50 border border-gray-100 px-2 py-1 rounded-md">
                      {{ formatarDataHora(evento.data_registro || evento.dt_alteracao) }}
                    </span>
                  </div>
                  
                  <div class="mt-1">
                    <p class="text-sm font-semibold text-gray-800">
                      {{ formatarHistorico(evento).principal }}
                    </p>
                    
                    <div v-if="formatarHistorico(evento).detalhe" class="mt-3 p-3 bg-blue-50/50 border border-blue-100 rounded-lg">
                      <p class="text-[10px] font-black text-blue-600 uppercase tracking-wider mb-1">Justificativa / Motivo</p>
                      <p class="text-sm text-gray-700 italic">"{{ formatarHistorico(evento).detalhe }}"</p>
                    </div>
                  </div>

                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'

const ordens = ref<any[]>([])
const loadingOS = ref(true)
const termoBusca = ref('')

const filtroDataInicio = ref('')
const filtroDataFim = ref('')
const filtroTipo = ref('TODOS')
const filtroStatus = ref('TODOS')
const filtroPrioridade = ref('TODAS')
const filtroPredio = ref('TODOS')

const osSelecionada = ref<any>(null)
const historicoAtual = ref<any[]>([])
const loadingHistorico = ref(false)

const authHeader = () => {
  const token = localStorage.getItem('token')
  return { headers: { Authorization: `Bearer ${token}` } }
}

async function carregarOrdens() {
  loadingOS.value = true
  try {
    const response = await api.get('/ordem-servico/', authHeader())
    let lista = response.data.dados || response.data
    ordens.value = lista.sort((a: any, b: any) => {
      const dateA = a.dt_abertura ? new Date(a.dt_abertura).getTime() : 0;
      const dateB = b.dt_abertura ? new Date(b.dt_abertura).getTime() : 0;
      return dateB - dateA;
    })
  } catch (error) {
    console.error("Erro ao carregar OS", error)
  } finally {
    loadingOS.value = false
  }
}

async function selecionarOS(os: any) {
  osSelecionada.value = os
  loadingHistorico.value = true
  historicoAtual.value = []
  
  try {
    const response = await api.get(`/ordem-servico/${os.id_ordem_servico}/historico/`, authHeader())
    let hist = response.data.dados || response.data
    historicoAtual.value = hist.sort((a: any, b: any) => {
      const dateA = (a.data_registro || a.dt_alteracao) ? new Date(a.data_registro || a.dt_alteracao).getTime() : 0;
      const dateB = (b.data_registro || b.dt_alteracao) ? new Date(b.data_registro || b.dt_alteracao).getTime() : 0;
      return dateB - dateA;
    })
  } catch (error) {
    console.error(`Erro histórico OS #${os.id_ordem_servico}`, error)
  } finally {
    loadingHistorico.value = false
  }
}

const prediosUnicos = computed(() => {
  const nomes = new Set(ordens.value.map(os => os.predio_nome).filter(Boolean))
  return Array.from(nomes).sort()
})

const ordensFiltradas = computed(() => {
  let resultado = [...ordens.value]

  if (filtroTipo.value !== 'TODOS') resultado = resultado.filter(os => os.tipo_manutencao === filtroTipo.value)
  if (filtroStatus.value !== 'TODOS') resultado = resultado.filter(os => os.status_ordem_servico === filtroStatus.value)
  if (filtroPrioridade.value !== 'TODAS') resultado = resultado.filter(os => os.prioridade_urgencia === filtroPrioridade.value)
  if (filtroPredio.value !== 'TODOS') resultado = resultado.filter(os => os.predio_nome === filtroPredio.value)

  if (filtroDataInicio.value) {
    const dataInicio = new Date(filtroDataInicio.value).getTime()
    resultado = resultado.filter(os => new Date(os.dt_abertura).getTime() >= dataInicio)
  }
  if (filtroDataFim.value) {
    const dataFim = new Date(filtroDataFim.value).getTime() + 86400000 
    resultado = resultado.filter(os => new Date(os.dt_abertura).getTime() < dataFim)
  }

  if (termoBusca.value.trim() !== '') {
    const termo = termoBusca.value.toLowerCase()
    resultado = resultado.filter(os => 
      String(os.id_ordem_servico).includes(termo) ||
      (os.predio_nome || '').toLowerCase().includes(termo) ||
      (os.tecnico_nome || '').toLowerCase().includes(termo) ||
      (os.descricao_servico || '').toLowerCase().includes(termo)
    )
  }

  return resultado
})

function limparFiltros() {
  filtroDataInicio.value = ''
  filtroDataFim.value = ''
  filtroTipo.value = 'TODOS'
  filtroStatus.value = 'TODOS'
  filtroPrioridade.value = 'TODAS'
  filtroPredio.value = 'TODOS'
  termoBusca.value = ''
}

const formatarDataSimples = (dataIso: string) => {
  if (!dataIso) return 'N/I'
  return new Date(dataIso).toLocaleDateString('pt-BR')
}

const formatarDataHora = (dataIso: string) => {
  if (!dataIso) return 'N/I'
  const data = new Date(dataIso)
  return data.toLocaleDateString('pt-BR') + ' às ' + data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

const extrairSolicitante = (os: any) => {
  if (!os) return ''
  if (os.tipo_manutencao === 'PREVENTIVA') return 'Sistema (Automático)'
  const match = os.descricao_servico?.match(/\[(.*?)\]/);
  return match ? match[1] : (os.solicitante_nome || 'Usuário Anônimo');
}

const extrairProblema = (descricao: string) => {
  if (!descricao) return 'Sem descrição.'
  return descricao.replace(/\[.*?\]\s*(-\s*Local:.*?\s*)?-\s*(Problema:\s*)?/, '').trim();
}

const formatarStatus = (status: string) => {
  const mapa: Record<string, string> = { 
    'ABERTA': 'Aberta', 
    'APROVADA': 'Para Iniciar', 
    'EM_EXECUCAO': 'Em Execução', 
    'AGUARDANDO_MATERIAL': 'Falta Material', 
    'AGUARDANDO_TERCEIRO': 'Aguard. Terceiro', 
    'CONCLUIDA': 'Concluída', 
    'ENCERRADA': 'Encerrada',
    'CANCELADA': 'Cancelada',
    'REPROVADA': 'Reprovada'
  }
  return mapa[status] || status
}

const getStatusClass = (status: string) => {
  const mapa: Record<string, string> = { 
    'ABERTA': 'bg-slate-100 text-slate-700 border-slate-200',
    'APROVADA': 'bg-emerald-100 text-emerald-700 border-emerald-200', 
    'EM_EXECUCAO': 'bg-amber-100 text-amber-700 border-amber-200', 
    'AGUARDANDO_MATERIAL': 'bg-orange-100 text-orange-700 border-orange-200', 
    'AGUARDANDO_TERCEIRO': 'bg-purple-100 text-purple-700 border-purple-200',
    'CONCLUIDA': 'bg-teal-100 text-teal-700 border-teal-200',
    'ENCERRADA': 'bg-gray-100 text-gray-500 border-gray-200',
    'CANCELADA': 'bg-red-100 text-red-700 border-red-200',
    'REPROVADA': 'bg-red-100 text-red-700 border-red-200'
  }
  return mapa[status] || 'bg-gray-100 text-gray-500 border-gray-200'
}

const formatarHistorico = (evento: any) => {
  if (!evento) return { principal: 'Atualização de sistema.', detalhe: '' };

  let textoOriginal = '';
  if (typeof evento === 'string') {
    textoOriginal = evento;
  } else {
    textoOriginal = evento.desc_historico || evento.descricao || evento.observacao || evento.justificativa || evento.texto_historico || '';
  }

  if (!textoOriginal) {
    return { principal: 'Ação registrada no sistema.', detalhe: '' };
  }

  const regex = /(.*?)(?:Detalhes:|Justificativa:)(.*)/i;
  const match = String(textoOriginal).match(regex);

  if (match) {
    return {
      principal: match[1].trim() || 'Status alterado.',
      detalhe: match[2].trim()
    };
  }

  return { principal: String(textoOriginal).trim(), detalhe: '' };
}

onMounted(() => carregarOrdens())
</script>