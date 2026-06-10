<template>
  <div class="h-full flex flex-col p-6 bg-gray-100/50">
    <div class="mb-4 shrink-0">
      <div class="flex justify-between items-end mb-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">Minhas Ordens de Serviço</h1>
          <p class="text-sm text-gray-500 mt-1">Gerencie a execução dos serviços que lhe foram atribuídos</p>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex flex-wrap items-end gap-3 mb-6">
        <div class="flex flex-col">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider">A partir de:</label>
          <input type="date" v-model="filtroDataInicio" class="bg-gray-50 border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer" />
        </div>
        <div class="flex flex-col">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider">Até:</label>
          <input type="date" v-model="filtroDataFim" class="bg-gray-50 border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer" />
        </div>
        <div class="flex flex-col min-w-[150px]">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider">Status:</label>
          <select v-model="filtroStatus" class="bg-gray-50 border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer">
            <option value="TODOS">Todos os status</option>
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
        <div class="flex flex-col min-w-[130px]">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider">Prioridade:</label>
          <select v-model="filtroPrioridade" class="bg-gray-50 border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer">
            <option value="TODAS">Todas</option>
            <option value="SIM">Urgente</option>
            <option value="NAO">Normal</option>
          </select>
        </div>
        <div class="flex flex-col min-w-[150px] flex-1">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider">Prédio:</label>
          <select v-model="filtroPredio" class="bg-gray-50 border border-gray-200 text-gray-700 text-xs font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer truncate">
            <option value="TODOS">Todos os Prédios</option>
            <option v-for="predio in prediosUnicos" :key="predio" :value="predio">{{ predio }}</option>
          </select>
        </div>
        <div class="flex flex-col flex-1 min-w-[200px]">
          <label class="text-[10px] text-gray-500 font-bold ml-1 mb-1 uppercase tracking-wider text-transparent">Busca</label>
          <div class="relative w-full">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400 text-sm">🔍</span>
            <input v-model="termoBusca" type="text" placeholder="Buscar OS, Prédio..." class="w-full bg-white border border-gray-200 text-gray-700 placeholder-gray-400 text-xs font-medium rounded-lg pl-9 pr-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-text" />
          </div>
        </div>
        <button @click="limparFiltros" class="px-5 py-2.5 text-xs font-bold text-gray-600 bg-gray-100 border border-gray-200 hover:bg-gray-200 hover:text-gray-800 rounded-lg transition-colors cursor-pointer ml-auto shadow-sm">
          Limpar Filtros
        </button>
      </div>

      <div class="flex border-b border-gray-200 mb-6 bg-white rounded-t-xl">
        <button @click="abaAtiva = 'CORRETIVA'" 
                :class="abaAtiva === 'CORRETIVA' ? 'border-blue-600 text-blue-700 bg-blue-50/40 font-bold' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                class="px-8 py-3.5 border-b-2 font-semibold text-sm transition-all focus:outline-none uppercase tracking-wider cursor-pointer">
          Manutenções Corretivas
        </button>
        <button @click="abaAtiva = 'PREVENTIVA'" 
                :class="abaAtiva === 'PREVENTIVA' ? 'border-blue-600 text-blue-700 bg-blue-50/40 font-bold' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                class="px-8 py-3.5 border-b-2 font-semibold text-sm transition-all focus:outline-none uppercase tracking-wider cursor-pointer">
          Cronograma Preventivo
        </button>
      </div>
    </div>

    <div class="flex-1 bg-white rounded-b-xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-y-auto h-full">
        <table class="w-full text-left border-collapse">
          <thead class="sticky top-0 bg-gray-50 z-10">
            <tr class="border-b border-gray-100 text-xs text-gray-500 uppercase tracking-wider">
              <th class="p-4 font-semibold">Ordem</th>
              <th class="p-4 font-semibold">Local / Prédio</th>
              <th class="p-4 font-semibold">Descrição do Serviço / Planejamento</th>
              <th class="p-4 font-semibold text-center">Status</th>
              <th class="p-4 font-semibold text-center">Prioridade</th>
              <th class="p-4 font-semibold text-center">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading" class="border-b border-gray-50">
              <td colspan="6" class="p-8 text-center text-gray-400 font-medium">A carregar ordens...</td>
            </tr>
            <tr v-else-if="ordensFiltradas.length === 0" class="border-b border-gray-50">
              <td colspan="6" class="p-8 text-center text-gray-400 font-medium">Nenhuma ordem nesta categoria.</td>
            </tr>
            <tr v-else v-for="os in ordensFiltradas" :key="os.id_ordem_servico" class="border-b border-gray-50 hover:bg-gray-50 transition-colors">
              <td class="p-4">
                <div class="text-sm font-bold text-gray-800">#{{ os.id_ordem_servico }}</div>
              </td>
              <td class="p-4 text-sm text-gray-600 truncate max-w-[200px]">{{ os.predio_nome || 'N/I' }} - {{ os.localizacao_nome || 'N/I' }}</td>
              <td class="p-4">
                <div v-if="os.tipo_manutencao === 'PREVENTIVA'">
                  <p class="text-sm font-bold text-gray-800">
                    Inspeção: {{ os.ativo_nome || 'Equipamento' }}
                    <span class="text-[10px] bg-purple-100 text-purple-700 font-bold px-1.5 py-0.5 rounded ml-1 border border-purple-200">PAT: {{ os.ativo_patrimonio || 'N/I' }}</span>
                  </p>
                  <div class="flex items-center gap-3 mt-1 text-[11px] text-gray-500">
                    <p><span class="font-semibold text-gray-400">Última:</span> {{ os.ativo_ultima_preventiva ? formatarDataSimples(os.ativo_ultima_preventiva) : 'N/I' }}</p>
                    <p><span class="font-bold text-blue-600">Agendada para:</span> {{ os.ativo_proxima_preventiva ? formatarDataSimples(os.ativo_proxima_preventiva) : 'N/I' }}</p>
                  </div>
                </div>
                <div v-else>
                  <p class="text-sm text-gray-600 truncate max-w-[250px]" :title="extrairProblema(os.descricao_servico)">
                    {{ extrairProblema(os.descricao_servico) }}
                  </p>
                </div>
              </td>
              <td class="p-4 text-center"><span :class="getStatusClass(os.status_ordem_servico)" class="px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap">{{ formatarStatus(os.status_ordem_servico) }}</span></td>
              <td class="p-4 text-center"><span :class="os.prioridade_urgencia === 'SIM' ? 'text-red-600 bg-red-100' : 'text-gray-600 bg-gray-100'" class="px-3 py-1 rounded-full text-xs font-bold">{{ os.prioridade_urgencia === 'SIM' ? 'Urgente' : 'Normal' }}</span></td>
              <td class="p-4 text-center">
                <button @click="abrirModalDetalhes(os)" class="text-blue-600 hover:text-white hover:bg-blue-600 font-bold border border-blue-200 px-3 py-1.5 rounded-lg transition-all shadow-sm cursor-pointer">
                  Abrir Ordem
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="modalAberto" @click.self="fecharModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 animate-fade-in">
      <div class="bg-white rounded-2xl w-full max-w-4xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50 shrink-0">
          <div>
            <p class="text-xs font-bold text-gray-400 uppercase tracking-wider">Execução do Serviço</p>
            <h2 class="text-2xl font-bold text-gray-800 mt-1">#{{ osSelecionada?.id_ordem_servico }}</h2>
          </div>
          <button @click="fecharModal" class="text-gray-400 hover:text-gray-700 p-2 rounded-full hover:bg-gray-200 transition-colors cursor-pointer">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>

        <div class="p-6 overflow-y-auto">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
              <span :class="getStatusClass(osSelecionada?.status_ordem_servico)" class="px-4 py-1.5 rounded-full text-sm font-bold border">{{ formatarStatus(osSelecionada?.status_ordem_servico) }}</span>
              <span :class="osSelecionada?.tipo_manutencao === 'PREVENTIVA' ? 'bg-purple-100 text-purple-700 border-purple-200' : 'bg-gray-100 text-gray-600 border-gray-200'" class="px-4 py-1.5 rounded-full text-sm font-bold border uppercase tracking-wider">
                {{ osSelecionada?.tipo_manutencao === 'PREVENTIVA' ? 'Preventiva' : 'Corretiva' }}
              </span>
            </div>
            
            <div class="relative">
              <select :value="osSelecionada?.prioridade_urgencia" @change="alterarPrioridade($event.target.value)"
                class="pl-4 pr-8 py-1.5 rounded-full text-sm font-bold outline-none cursor-pointer appearance-none border transition-colors bg-gray-50 border-gray-200 hover:bg-gray-100 text-gray-700"
                :class="osSelecionada?.prioridade_urgencia === 'SIM' ? 'text-red-700 bg-red-50 border-red-200 hover:bg-red-100' : ''">
                <option value="NAO">Prioridade: Normal</option>
                <option value="SIM">🚨 Urgente</option>
              </select>
              <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3" :class="osSelecionada?.prioridade_urgencia === 'SIM' ? 'text-red-500' : 'text-gray-500'">
                <svg class="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
              <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Local (Prédio / Sala)</p>
              <p class="text-sm font-bold text-gray-800">{{ osSelecionada?.predio_nome || 'N/I' }} - {{ osSelecionada?.localizacao_nome || 'N/I' }}</p>
            </div>
            <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
              <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Solicitante</p>
              <p class="text-sm font-bold text-gray-800">{{ extrairSolicitante(osSelecionada) }}</p>
            </div>
          </div>
          
          <div class="mt-6">
            <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Descrição do Problema Reportado</p>
            <div class="p-4 bg-gray-50 rounded-xl border border-gray-100 text-sm text-gray-700 whitespace-pre-wrap">{{ extrairProblema(osSelecionada?.descricao_servico) }}</div>
          </div>
        </div>

        <div class="p-6 border-t border-gray-100 bg-gray-50 flex flex-col rounded-b-2xl shrink-0">
          <div v-if="!mostrandoFormConclusao" class="flex flex-col sm:flex-row items-center justify-between gap-4 w-full">
            <div class="w-full sm:w-auto">
              <p class="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1">Ações de Execução</p>
              <p class="text-xs font-semibold text-gray-600">
                {{ osSelecionada?.status_ordem_servico === 'APROVADA' ? 'Ordem liberada para início.' : (osSelecionada?.status_ordem_servico === 'EM_EXECUCAO' ? 'Serviço em andamento.' : 'Sem ações pendentes.') }}
              </p>
            </div>

            <div class="flex flex-wrap gap-3 w-full sm:w-auto justify-end">
              <button @click="fecharModal" class="px-5 py-2.5 text-sm font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl transition-colors cursor-pointer shadow-sm">
                Fechar
              </button>
              
              <button v-if="osSelecionada?.status_ordem_servico === 'EM_EXECUCAO'" @click="pausarOS" class="px-5 py-2.5 text-sm font-bold text-orange-600 bg-orange-50 border border-orange-200 hover:bg-orange-100 rounded-xl transition-colors shadow-sm cursor-pointer flex items-center gap-2">
                <span>⏸️</span> Pausar
              </button>

              <button v-if="['APROVADA', 'AGUARDANDO_MATERIAL', 'AGUARDANDO_TERCEIRO'].includes(osSelecionada?.status_ordem_servico)" @click="iniciarOS" class="px-5 py-2.5 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-colors shadow-sm cursor-pointer flex items-center gap-2">
                <span>▶️</span> {{ osSelecionada?.status_ordem_servico === 'APROVADA' ? 'Iniciar Execução' : 'Retomar Serviço' }}
              </button>

              <button v-if="osSelecionada?.status_ordem_servico === 'EM_EXECUCAO'" @click="mostrandoFormConclusao = true" class="px-5 py-2.5 text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition-colors shadow-sm cursor-pointer flex items-center gap-2">
                <span>✅</span> Concluir Ordem
              </button>
            </div>
          </div>

          <div v-else class="w-full animate-fade-in bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <h3 class="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2"><span>📝</span> Relatório de Conclusão</h3>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 relative">
              <div>
                <label class="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1 block">O que foi consertado?</label>
                <select v-model="formConclusao.tipo" class="w-full bg-gray-50 border border-gray-200 text-gray-700 text-sm font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer">
                  <option value="" disabled>Selecione...</option>
                  <option value="AR_CONDICIONADO">❄️ Ar Condicionado</option>
                  <option value="OUTROS">🔧 Outros Equipamentos / Geral</option>
                </select>
              </div>

              <div v-if="formConclusao.tipo === 'AR_CONDICIONADO'" class="relative">
                <label class="text-[11px] font-bold text-emerald-600 uppercase tracking-wider mb-1 block">Qual Ar Condicionado? *</label>
                
                <div @click="dropdownAberto = !dropdownAberto" 
                     class="w-full bg-emerald-50/30 border border-emerald-200 text-gray-800 text-sm font-bold rounded-lg px-3 py-2.5 cursor-pointer flex justify-between items-center transition-all hover:bg-emerald-100/50">
                  <span class="truncate pr-2">
                    {{ formConclusao.patrimonio 
                        ? ativosDoPredio.find(a => a.codigo_patrimonial === formConclusao.patrimonio)?.nomeLimpo 
                        : 'Selecione o equipamento...' }}
                  </span>
                  <span class="text-xs text-emerald-600">▼</span>
                </div>
                
                <div v-if="dropdownAberto" class="absolute z-50 w-full mt-1 bg-white border border-emerald-200 rounded-lg shadow-2xl max-h-48 overflow-y-auto">
                  <div v-if="ativosDoPredio.length === 0" class="px-3 py-3 text-sm text-gray-500 font-medium">Nenhum ar-condicionado cadastrado.</div>
                  <div v-else 
                       v-for="ativo in ativosDoPredio" :key="ativo.id_ativo" 
                       @click="formConclusao.patrimonio = ativo.codigo_patrimonial; formConclusao.id_ativo = ativo.id_ativo || ativo.id; dropdownAberto = false" 
                       class="px-3 py-2.5 text-sm font-bold text-gray-700 hover:bg-emerald-50 cursor-pointer border-b border-gray-50 last:border-0 truncate">
                    {{ ativo.nomeLimpo }}
                  </div>
                </div>
              </div>
            </div>

            <div class="mb-5">
              <label class="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-1 block">Resumo do Serviço Realizado *</label>
              <textarea v-model="formConclusao.descricao" rows="2" placeholder="Descreva brevemente o que foi feito..." class="w-full bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg p-3 outline-none focus:ring-2 focus:ring-emerald-500 resize-none"></textarea>
            </div>
            
            <div class="flex justify-end gap-3 pt-4 border-t border-gray-100">
              <button @click="mostrandoFormConclusao = false; dropdownAberto = false" class="px-5 py-2.5 text-sm font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl transition-colors cursor-pointer">Voltar</button>
              <button @click="enviarConclusao" class="px-5 py-2.5 text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition-colors shadow-sm cursor-pointer flex items-center gap-2">
                <span>💾</span> Salvar e Encerrar OS
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import Swal from 'sweetalert2'

const abaAtiva = ref('CORRETIVA')
const dropdownAberto = ref(false)

const ordens = ref<any[]>([])
const ativos = ref<any[]>([])
const listaPredios = ref<any[]>([])
const listaLocalizacoes = ref<any[]>([])
const loading = ref(true)

const filtroDataInicio = ref('')
const filtroDataFim = ref('')
const filtroStatus = ref('TODOS')
const filtroPrioridade = ref('TODAS')
const filtroPredio = ref('TODOS')
const termoBusca = ref('')

const modalAberto = ref(false)
const osSelecionada = ref<any>(null)

const mostrandoFormConclusao = ref(false)
const formConclusao = ref({ tipo: '', patrimonio: '', id_ativo: null as any, descricao: '' })

const prediosUnicos = computed(() => {
  const nomes = new Set(ordens.value.map(os => os.predio_nome).filter(Boolean))
  return Array.from(nomes).sort()
})

const ativosDoPredio = computed(() => {
  if (!osSelecionada.value) return [];
  const locIdDaOS = osSelecionada.value.localizacao_id || osSelecionada.value.localizacao;
  const filtrados = ativos.value.filter(ativo => {
    const locIdAtivo = ativo.localizacao || ativo.id_localizacao || ativo.localizacao_id;
    if (!locIdAtivo || !locIdDaOS) return false;
    return String(locIdAtivo) === String(locIdDaOS);
  });
  return filtrados.map(ativo => {
    const locId = ativo.localizacao || ativo.id_localizacao || ativo.localizacao_id;
    const loc = listaLocalizacoes.value.find(l => String(l.id_localizacao || l.id) === String(locId));
    const nomeLocal = loc ? (loc.desc_localizacao || loc.nome || 'Local N/I') : 'Local N/I';
    const marca = (ativo.marca || '').replace(/\*/g, '').trim();
    const modelo = (ativo.modelo || '').replace(/\*/g, '').trim();
    const pat = (ativo.codigo_patrimonial || '').replace(/\*/g, '').trim() || 'S/N';
    return { ...ativo, nomeLimpo: `${nomeLocal} | ${marca} ${modelo}`.trim() + ` (PAT: ${pat})` };
  }).sort((a, b) => a.nomeLimpo.localeCompare(b.nomeLimpo));
});

const extrairSolicitante = (os: any) => {
  if (!os) return ''
  if (os.tipo_manutencao === 'PREVENTIVA') return 'Sistema (Automático)'
  const match = os.descricao_servico?.match(/\[(.*?)\]/)
  return match ? match[1] : (os.solicitante_nome || 'Totem')
}

const extrairProblema = (descricao: string) => {
  if (!descricao) return 'Sem descrição detalhada.'
  return descricao.replace(/\[.*?\]\s*(-\s*Local:.*?\s*)?-\s*(Problema:\s*)?/, '').trim()
}

const formatarDataSimples = (dataIso: string) => {
  if (!dataIso) return 'N/I'
  return new Date(dataIso).toLocaleDateString('pt-BR')
}

const authHeader = () => {
  const token = localStorage.getItem('token')
  return { headers: { Authorization: `Bearer ${token}` } }
}

const ordensFiltradas = computed(() => {
  let resultado = ordens.value.filter(os => (os.tipo_manutencao || 'CORRETIVA').toUpperCase() === abaAtiva.value)
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
      String(os.id_ordem_servico).includes(termo) || (os.predio_nome || '').toLowerCase().includes(termo) ||
      (os.localizacao_nome || '').toLowerCase().includes(termo) || (os.descricao_servico || '').toLowerCase().includes(termo)
    )
  }
  return resultado
})

const formatarStatus = (status: string) => {
  const mapa: Record<string, string> = {
    'ABERTA': 'Aberta', 'APROVADA': 'Para Iniciar', 'EM_EXECUCAO': 'Em Execução', 'AGUARDANDO_MATERIAL': 'Falta Material', 'AGUARDANDO_TERCEIRO': 'Aguard. Terceiro',
    'CONCLUIDA': 'Concluída', 'ENCERRADA': 'Encerrada', 'CANCELADA': 'Cancelada', 'REPROVADA': 'Reprovada'
  }
  return mapa[status] || status
}

const getStatusClass = (status: string) => {
  const mapa: Record<string, string> = {
    'ABERTA': 'bg-slate-100 text-slate-700 border-slate-200', 'APROVADA': 'bg-emerald-100 text-emerald-700 border-emerald-200',
    'EM_EXECUCAO': 'bg-amber-100 text-amber-700 border-amber-200', 'AGUARDANDO_MATERIAL': 'bg-orange-100 text-orange-700 border-orange-200',
    'AGUARDANDO_TERCEIRO': 'bg-purple-100 text-purple-700 border-purple-200', 'CONCLUIDA': 'bg-teal-100 text-teal-700 border-teal-200',
    'ENCERRADA': 'bg-gray-100 text-gray-500 border-gray-200', 'CANCELADA': 'bg-red-100 text-red-700 border-red-200', 'REPROVADA': 'bg-red-100 text-red-700 border-red-200'
  }
  return mapa[status] || 'bg-gray-100 text-gray-500 border-gray-200'
}

async function carregarOrdens() {
  loading.value = true
  try {
    const response = await api.get('/ordem-servico/', authHeader())
    ordens.value = response.data.dados || response.data
  } catch (error) { console.error(error) } finally { loading.value = false }
}

async function carregarAtivos() {
  try {
    const [resAtivos, resPredios, resLoc] = await Promise.all([
      api.get('/ativo/', authHeader()), api.get('/predio/', authHeader()), api.get('/localizacao/', authHeader())
    ])
    ativos.value = resAtivos.data.dados || resAtivos.data || []
    listaPredios.value = resPredios.data.dados || resPredios.data || []
    listaLocalizacoes.value = resLoc.data.dados || resLoc.data || []
  } catch (error) { console.error(error) }
}

function abrirModalDetalhes(os: any) {
  osSelecionada.value = os
  mostrandoFormConclusao.value = false
  dropdownAberto.value = false
  formConclusao.value = { tipo: '', patrimonio: '', id_ativo: null, descricao: '' }
  modalAberto.value = true
}

function fecharModal() { modalAberto.value = false; osSelecionada.value = null; dropdownAberto.value = false }

async function alterarPrioridade(novaPrioridade: string) {
  try {
    await api.patch(`/ordem-servico/${osSelecionada.value.id_ordem_servico}/`, { prioridade_urgencia: novaPrioridade }, authHeader())
    osSelecionada.value.prioridade_urgencia = novaPrioridade
    Swal.mixin({ toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, timerProgressBar: true }).fire({ icon: 'success', title: 'Prioridade alterada!' })
    carregarOrdens()
  } catch (error) { console.error(error) }
}

async function iniciarOS() {
  try {
    await api.patch(`/ordem-servico/${osSelecionada.value.id_ordem_servico}/`, { status_ordem_servico: 'EM_EXECUCAO', observacao: 'Técnico iniciou o serviço.' }, authHeader())
    osSelecionada.value.status_ordem_servico = 'EM_EXECUCAO'
    carregarOrdens()
  } catch (error) { console.error(error) }
}

async function pausarOS() {
  const { value: statusEscolhido } = await Swal.fire({
    title: 'Motivo da Pausa', input: 'select',
    inputOptions: { 'AGUARDANDO_MATERIAL': 'Falta de Material', 'AGUARDANDO_TERCEIRO': 'Aguardando Terceiros' },
    showCancelButton: true, confirmButtonText: 'Próximo', cancelButtonText: 'Cancelar',
    customClass: { confirmButton: 'cursor-pointer', cancelButton: 'cursor-pointer' }
  })
  if (statusEscolhido) {
    let tituloDetalhe = statusEscolhido === 'AGUARDANDO_MATERIAL' ? 'Quais materiais faltam?' : 'Qual terceiro/empresa?'
    const { value: justificativa } = await Swal.fire({ 
      title: tituloDetalhe, input: 'text', showCancelButton: true, confirmButtonText: 'Confirmar Pausa', cancelButtonText: 'Cancelar',
      customClass: { confirmButton: 'cursor-pointer', cancelButton: 'cursor-pointer' }
    })
    if (justificativa) {
      try {
        await api.patch(`/ordem-servico/${osSelecionada.value.id_ordem_servico}/`, { status_ordem_servico: statusEscolhido, observacao: justificativa }, authHeader())
        fecharModal()
        carregarOrdens()
      } catch (error) { console.error(error) }
    }
  }
}

async function enviarConclusao() {
  if (!formConclusao.value.tipo) return Swal.fire({ title: 'Atenção', text: 'Selecione o que foi consertado.', icon: 'warning' })
  if (formConclusao.value.tipo === 'AR_CONDICIONADO' && !formConclusao.value.patrimonio) return Swal.fire({ title: 'Atenção', text: 'Selecione o Ar Condicionado.', icon: 'warning' })
  if (!formConclusao.value.descricao) return Swal.fire({ title: 'Atenção', text: 'Preencha o resumo do serviço.', icon: 'warning' })

  try {
    const patrim = formConclusao.value.tipo === 'AR_CONDICIONADO' ? 'PAT: ' + formConclusao.value.patrimonio : 'Diversos/Outros'
    const textoHistorico = `Serviço concluído (${patrim}). Justificativa: ${formConclusao.value.descricao}`

    const payload: any = { 
      status_ordem_servico: 'CONCLUIDA',
      observacao: textoHistorico,
      justificativa: textoHistorico,
      motivo: textoHistorico,
      desc_historico: textoHistorico
    }

    if (formConclusao.value.tipo === 'AR_CONDICIONADO' && formConclusao.value.id_ativo) {
       payload.ativo = formConclusao.value.id_ativo;
       payload.ativo_id = formConclusao.value.id_ativo;
    }

    await api.patch(`/ordem-servico/${osSelecionada.value.id_ordem_servico}/`, payload, authHeader())
    
    Swal.fire({ title: 'Serviço Concluído!', text: 'A ordem foi encerrada com sucesso.', icon: 'success', timer: 3000, showConfirmButton: false })
    
    fecharModal()
    carregarOrdens()
  } catch (error) { 
    console.error(error)
    Swal.fire({ title: 'Erro', text: 'Falha ao encerrar a ordem de serviço.', icon: 'error' })
  }
}

function limparFiltros() {
  filtroDataInicio.value = ''; filtroDataFim.value = ''; filtroStatus.value = 'TODOS'; filtroPrioridade.value = 'TODAS'; filtroPredio.value = 'TODOS'; termoBusca.value = ''
}

onMounted(() => { carregarOrdens(); carregarAtivos() })
</script>

<style scoped> 
.animate-fade-in { animation: fadeIn 0.2s ease-out; } 
@keyframes fadeIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } } 
</style>