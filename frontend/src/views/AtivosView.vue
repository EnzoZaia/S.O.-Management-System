<template>
  <div class="p-8">
    <div class="mb-8 flex flex-col justify-between items-start gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Gestão de Ativos</h1>
        <p class="text-sm text-gray-500 mt-1">Registe e gira os equipamentos da instituição para manutenções preventivas</p>
      </div>
      
      <div class="w-full flex flex-col md:flex-row items-center gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        
        <div class="relative w-full md:flex-1">
          <span class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400 text-sm">🔍</span>
          <input v-model="termoBusca" type="text" placeholder="Buscar por código, marca, modelo..." class="w-full bg-gray-50 border border-gray-200 text-gray-700 placeholder-gray-400 text-sm rounded-lg pl-9 pr-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-text" />
        </div>

        <div class="w-full md:w-64">
          <select v-model="filtroPredioBusca" class="w-full bg-gray-50 border border-gray-200 text-gray-700 text-sm font-semibold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer">
            <option value="">Todos os Prédios/Blocos</option>
            <option v-for="predio in listaPredios" :key="predio.id_predio || predio.id" :value="predio.id_predio || predio.id">
              {{ predio.nome_predio || predio.nome }}
            </option>
          </select>
        </div>

        <div class="w-full md:w-56">
          <select v-model="filtroStatusPreventiva" class="w-full bg-gray-50 border border-gray-200 text-gray-700 text-sm font-semibold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer">
            <option value="">Todos os Status</option>
            <option value="atrasada">🔴 Preventiva Atrasada</option>
            <option value="avencer">🟡 Vence em breve (&le; 15 dias)</option>
            <option value="emdia">🟢 Preventiva em Dia</option>
            <option value="semregistro">⚪ Sem Registro</option>
          </select>
        </div>
        
        <button v-if="!ehTecnico" @click="abrirModalNovo" class="w-full md:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-lg shadow-md transition-colors cursor-pointer flex items-center justify-center gap-2 shrink-0">
          <span>+</span> Novo Ativo
        </button>
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden pb-4">
      <div v-if="loading" class="p-8 text-center text-gray-400 font-medium">A carregar ativos...</div>
      <div v-else-if="Object.keys(ativosAgrupados).length === 0" class="p-8 text-center text-gray-400 font-medium">Nenhum ativo encontrado com os filtros atuais.</div>

      <div v-else v-for="(ativosDoPredio, nomePredio) in ativosAgrupados" :key="nomePredio" class="mb-4">
        
        <div class="bg-gray-100/80 px-6 py-3 border-y border-gray-200 flex items-center justify-between sticky top-0 z-10">
           <h3 class="font-bold text-gray-800 flex items-center gap-2 uppercase tracking-wider text-sm">
             <span class="text-blue-600">🏢</span> {{ nomePredio }}
           </h3>
           <span class="text-xs font-bold text-gray-500 bg-white px-3 py-1 rounded-full border border-gray-200 shadow-sm">
             {{ ativosDoPredio.length }} equipamento(s)
           </span>
        </div>

        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="text-[10px] text-gray-400 uppercase tracking-wider hidden sm:table-row">
              <th class="px-6 py-2 font-semibold w-1/3">Equipamento</th>
              <th class="px-6 py-2 font-semibold">Identificação</th>
              <th class="px-6 py-2 font-semibold">Localização Exata</th>
              <th class="px-6 py-2 font-semibold text-center">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ativo in ativosDoPredio" :key="ativo.id_ativo || ativo.id" class="border-b border-gray-50 hover:bg-blue-50/30 transition-colors group">
              
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg border flex items-center justify-center shrink-0 shadow-sm" :class="obterCorStatus(ativo).bg_icon">
                    <span v-if="ativo.tipo_ativo === 'AR_CONDICIONADO'" class="text-xl">❄️</span>
                    <span v-else class="text-xl">🖥️</span>
                  </div>
                  <div>
                    <div class="text-sm font-bold text-gray-800">{{ ativo.marca }} {{ ativo.modelo }}</div>
                    <div class="text-[10px] font-semibold mt-0.5" :class="obterCorStatus(ativo).text">
                      {{ obterCorStatus(ativo).label }}
                    </div>
                  </div>
                </div>
              </td>

              <td class="px-6 py-4">
                <div class="flex flex-col gap-1">
                  <span class="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-[10px] font-bold tracking-wider border border-gray-200 w-fit">
                    PAT: {{ ativo.codigo_patrimonial || 'N/I' }}
                  </span>
                  <span class="text-[11px] text-gray-400 font-medium">SN: {{ ativo.numero_serial || 'N/I' }}</span>
                </div>
              </td>

              <td class="px-6 py-4">
                 <div class="flex items-center gap-2">
                   <span class="text-gray-300">📍</span>
                   <span class="text-sm font-medium text-gray-600">
                     {{ gerarNomeSala(ativo) }}
                   </span>
                 </div>
              </td>

              <td class="px-6 py-4 text-center">
                <div class="flex items-center justify-center gap-2 transition-opacity">
                  <button @click="abrirModalDetalhes(ativo)" class="text-indigo-600 hover:text-white hover:bg-indigo-600 font-bold border border-indigo-200 px-3 py-1.5 rounded-lg transition-all shadow-sm cursor-pointer">Detalhes</button>
                  <button v-if="!ehTecnico" @click="abrirModalEdicao(ativo)" class="text-blue-600 hover:text-white hover:bg-blue-600 font-bold border border-blue-200 px-3 py-1.5 rounded-lg transition-all shadow-sm cursor-pointer">Editar</button>
                  <button v-if="!ehTecnico" @click="excluirAtivo(ativo.id_ativo || ativo.id)" class="text-red-600 hover:text-white hover:bg-red-600 font-bold border border-red-200 px-3 py-1.5 rounded-lg transition-all shadow-sm cursor-pointer">Remover</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="modalAberto" @click.self="fecharModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 animate-fade-in">
      <div class="bg-white rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col">
        <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <div>
            <h2 class="text-xl font-bold text-gray-800">{{ modoEdicao ? 'Editar Ativo' : 'Registar Novo Ativo' }}</h2>
          </div>
          <button @click="fecharModal" class="text-gray-400 hover:text-gray-700 p-2 rounded-full hover:bg-gray-200 transition-colors cursor-pointer"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
        </div>
        
        <div class="p-6 space-y-5 overflow-y-auto max-h-[70vh]">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Tipo de Ativo *</label>
              <select v-model="form.tipo_ativo" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 cursor-pointer">
                <option value="AR_CONDICIONADO">Ar Condicionado</option>
              </select>
            </div>
            
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Código Patrimonial *</label>
              <input v-model="form.codigo_patrimonial" type="text" placeholder="Ex: 63270" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" />
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Marca *</label>
              <input v-model="form.marca" type="text" placeholder="Ex: LG, Carrier" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" />
            </div>
            
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Modelo *</label>
              <input v-model="form.modelo" type="text" placeholder="Ex: Dual Inverter 12000" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" />
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Número Serial</label>
              <input v-model="form.numero_serial" type="text" placeholder="Ex: 4318B14346431" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" />
            </div>
            
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Preventiva (Dias) *</label>
              <input v-model.number="form.periodicidade_preventiva_dias" type="number" min="0" placeholder="Ex: 30" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Última Preventiva Realizada</label>
              <input v-model="form.dt_ultima_preventiva" type="date" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" />
            </div>
          </div>

          <hr class="border-gray-100 my-2" />

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Prédio / Bloco *</label>
              <select v-model="idPredioSelecionado" @change="aoTrocarPredio" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 cursor-pointer">
                <option :value="null" disabled>Selecione o Prédio...</option>
                <option v-for="predio in listaPredios" :key="predio.id_predio || predio.id" :value="predio.id_predio || predio.id">{{ predio.nome_predio || predio.nome }}</option>
              </select>
            </div>

            <div class="space-y-1.5" v-if="idPredioSelecionado">
              <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Sala / Localização Exata *</label>
              <select v-model="form.id_localizacao" class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:bg-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 cursor-pointer">
                <option value="" disabled>Selecione o ambiente...</option>
                <option v-for="loc in localizacoesFiltradas" :key="loc.id_localizacao || loc.id" :value="loc.id_localizacao || loc.id">{{ loc.desc_localizacao || loc.nome }}</option>
              </select>
            </div>
          </div>
        </div>
        
        <div class="p-6 border-t border-gray-100 flex justify-end gap-3 bg-gray-50">
          <button @click="fecharModal" class="px-6 py-2.5 rounded-lg font-bold text-gray-600 hover:bg-gray-200 transition-colors cursor-pointer">Cancelar</button>
          <button @click="salvarAtivo" :disabled="salvando" class="px-6 py-2.5 rounded-lg font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 transition-colors cursor-pointer shadow-md">
            {{ salvando ? 'A guardar...' : 'Guardar Ativo' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="modalDetalhesAberto" @click.self="fecharModalDetalhes" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 animate-fade-in">
      <div class="bg-white rounded-2xl w-full max-w-4xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        
        <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50 shrink-0">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 text-2xl shadow-sm">
              {{ ativoSelecionado?.tipo_ativo === 'AR_CONDICIONADO' ? '❄️' : '🖥️' }}
            </div>
            <div>
              <p class="text-[10px] font-bold text-indigo-500 uppercase tracking-wider mb-0.5">Prontuário do Equipamento</p>
              <h2 class="text-2xl font-black text-gray-800 leading-none">{{ ativoSelecionado?.marca }} {{ ativoSelecionado?.modelo }}</h2>
            </div>
          </div>
          <button @click="fecharModalDetalhes" class="text-gray-400 hover:text-gray-700 p-2 rounded-full hover:bg-gray-200 transition-colors cursor-pointer">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>

        <div class="p-6 overflow-y-auto bg-white space-y-6">
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="md:col-span-2 grid grid-cols-2 gap-4 bg-gray-50 p-5 rounded-2xl border border-gray-100">
              <div>
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Patrimônio / Serial</p>
                <p class="text-sm font-bold text-gray-800">PAT: {{ ativoSelecionado?.codigo_patrimonial }}</p>
                <p class="text-xs text-gray-500">SN: {{ ativoSelecionado?.numero_serial || 'N/I' }}</p>
              </div>
              <div>
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-1">Localização Atual</p>
                <p class="text-sm font-bold text-gray-800">{{ gerarNomeLocalizacao(ativoSelecionado) }}</p>
              </div>
            </div>

            <div class="bg-indigo-50/50 p-5 rounded-2xl border border-indigo-100 flex flex-col justify-center relative overflow-hidden">
              <div class="absolute -right-4 -bottom-4 opacity-10 text-6xl" :class="obterCorStatus(ativoSelecionado).text">
                {{ obterCorStatus(ativoSelecionado).icon }}
              </div>
              <p class="text-[10px] font-black text-indigo-600 uppercase tracking-wider mb-2 z-10">Ciclo Preventivo ({{ ativoSelecionado?.periodicidade_preventiva_dias }} dias)</p>
              <div class="flex justify-between items-end mb-2 z-10">
                <span class="text-xs font-semibold text-gray-600">Última:</span>
                <span class="text-sm font-bold text-gray-800">{{ ativoSelecionado?.dt_ultima_preventiva ? formatarData(ativoSelecionado.dt_ultima_preventiva) : 'Sem registo' }}</span>
              </div>
              <div class="flex justify-between items-end pt-2 border-t border-indigo-100 z-10">
                <span class="text-xs font-semibold text-indigo-700">Próxima:</span>
                <span class="text-sm font-black text-indigo-700">{{ ativoSelecionado?.dt_proxima_preventiva ? formatarData(ativoSelecionado.dt_proxima_preventiva) : 'A calcular...' }}</span>
              </div>
            </div>
          </div>

          <div>
            <h3 class="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
              <span>⏱️</span> Histórico de Manutenções
            </h3>
            
            <div class="bg-gray-50/50 rounded-2xl border border-gray-100 p-6">
              <div v-if="loadingHistorico" class="text-center text-gray-400 font-medium py-8">A buscar registos...</div>
              <div v-else-if="historicoAtivo.length === 0" class="text-center text-gray-400 font-medium py-8">Nenhuma manutenção registada para este equipamento ainda.</div>
              
              <div v-else class="relative border-l-2 border-indigo-200 ml-3 pl-6 space-y-6">
                <div v-for="(evento, index) in historicoAtivo" :key="index" class="relative group">
                  <div :class="evento.tipo_manutencao === 'PREVENTIVA' ? 'bg-purple-500' : 'bg-orange-500'" class="absolute w-3 h-3 rounded-full border-2 border-white -left-[31px] top-1.5 shadow-sm"></div>
                  
                  <div class="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                    <div class="flex justify-between items-start mb-2">
                      <div class="flex items-center gap-2">
                        <span :class="evento.tipo_manutencao === 'PREVENTIVA' ? 'bg-purple-100 text-purple-700' : 'bg-orange-100 text-orange-700'" class="text-[9px] font-black px-2 py-0.5 rounded uppercase tracking-wider">
                          {{ evento.tipo_manutencao || 'MANUTENÇÃO' }}
                        </span>
                        <span class="text-xs font-bold text-gray-800">OS #{{ evento.id_ordem_servico || evento.ordem_servico || 'N/I' }}</span>
                      </div>
                      <span class="text-[10px] font-bold text-gray-500 bg-gray-50 border border-gray-100 px-2 py-1 rounded-md">
                        {{ formatarData(evento.data_conclusao || evento.dt_alteracao || evento.data_registro || evento.dt_abertura) }}
                      </span>
                    </div>
                    
                    <p class="text-sm text-gray-700 mt-2 italic">"{{ extrairTextoHistorico(evento) }}"</p>
                    
                    <div class="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2">
                      <span class="bg-gray-100 p-1 rounded text-gray-500 text-xs">👤</span>
                      <span class="text-xs font-semibold text-gray-600">Técnico/Responsável: {{ evento.tecnico_nome || evento.usuario_nome || 'N/I' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import Swal from 'sweetalert2'

const route = useRoute()

const ehTecnico = computed(() => {
  const urlTecnico = route.path.includes('tecnico')
  const grupoTecnico = localStorage.getItem('grupo') === 'TECNICO'
  return urlTecnico || grupoTecnico
})

const ativos = ref<any[]>([])
const loading = ref(true)

const termoBusca = ref('')
const filtroPredioBusca = ref('')
const filtroStatusPreventiva = ref('')

const modalAberto = ref(false)
const modoEdicao = ref(false)
const salvando = ref(false)

const modalDetalhesAberto = ref(false)
const ativoSelecionado = ref<any>(null)
const historicoAtivo = ref<any[]>([])
const loadingHistorico = ref(false)

const listaPredios = ref<any[]>([])
const listaLocalizacoes = ref<any[]>([])
const idPredioSelecionado = ref<number | null>(null)

const form = ref({
  id_ativo: null,
  codigo_patrimonial: '',
  tipo_ativo: 'AR_CONDICIONADO',
  marca: '',
  modelo: '',
  numero_serial: '',
  periodicidade_preventiva_dias: 30,
  dt_ultima_preventiva: '', 
  id_localizacao: '' as number | string
})

const authHeader = () => {
  const token = localStorage.getItem('token')
  return { headers: { Authorization: `Bearer ${token}` } }
}

const formatarData = (data: string) => {
  if (!data) return ''
  const safeData = data.includes('T') ? data : `${data}T12:00:00`
  return new Date(safeData).toLocaleDateString('pt-BR')
}

// === EXTRATOR BLINDADO DE JUSTIFICATIVA ===
const extrairTextoHistorico = (evento: any) => {
  if (!evento) return 'Manutenção registrada no sistema.';
  if (typeof evento === 'string') return evento;

  let textoBruto = evento.observacao || evento.justificativa || evento.desc_historico || evento.motivo || '';

  const match = String(textoBruto).match(/(.*?)(?:Detalhes:|Justificativa:)(.*)/i);
  if (match && match[2]) {
     return match[2].trim();
  }

  if (!textoBruto || textoBruto.trim() === 'Sem detalhes fornecidos.' || textoBruto.trim() === 'None') {
     textoBruto = evento.descricao_servico || evento.descricao || 'Manutenção registrada no sistema (Detalhes adicionais não salvos).';
  }
  
  return textoBruto;
}

function obterCorStatus(ativo: any) {
  if (!ativo.dt_proxima_preventiva) {
    return { bg_icon: 'bg-gray-50 border-gray-200 text-gray-400', text: 'text-gray-400', label: 'Sem Registro', icon: '⚪', status: 'semregistro' }
  }

  const dataProxima = new Date(`${ativo.dt_proxima_preventiva}T12:00:00`).getTime()
  const hoje = new Date().getTime()
  const diffDias = Math.ceil((dataProxima - hoje) / (1000 * 60 * 60 * 24))

  if (diffDias < 0) {
    return { bg_icon: 'bg-red-50 border-red-200 text-red-600', text: 'text-red-600', label: `Atrasada (${Math.abs(diffDias)} dias)`, icon: '🔴', status: 'atrasada' }
  } else if (diffDias <= 15) {
    return { bg_icon: 'bg-orange-50 border-orange-200 text-orange-500', text: 'text-orange-500', label: `Vence em ${diffDias} dias`, icon: '🟡', status: 'avencer' }
  } else {
    return { bg_icon: 'bg-emerald-50 border-emerald-200 text-emerald-600', text: 'text-emerald-500', label: 'Preventiva em dia', icon: '🟢', status: 'emdia' }
  }
}

const gerarNomePredio = (ativo: any) => {
  const locId = ativo.localizacao || ativo.id_localizacao || ativo.localizacao_id;
  if (!locId) return 'Sem Localização';
  const loc = listaLocalizacoes.value.find(l => String(l.id_localizacao || l.id) === String(locId));
  if (!loc) return 'Sala Não Encontrada';
  const predioId = loc.predio || loc.id_predio;
  const predio = listaPredios.value.find(p => String(p.id_predio || p.id) === String(predioId));
  return predio ? (predio.nome_predio || predio.nome) : 'Prédio Desconhecido';
}

const gerarNomeSala = (ativo: any) => {
  const locId = ativo.localizacao || ativo.id_localizacao || ativo.localizacao_id;
  if (!locId) return 'N/I';
  const loc = listaLocalizacoes.value.find(l => String(l.id_localizacao || l.id) === String(locId));
  return loc ? (loc.desc_localizacao || loc.nome) : 'Sala Desconhecida';
}

const gerarNomeLocalizacao = (ativo: any) => {
  return `${gerarNomePredio(ativo)} - ${gerarNomeSala(ativo)}`
}

const ativosFiltrados = computed(() => {
  let resultado = ativos.value

  if (termoBusca.value) {
    const termo = termoBusca.value.toLowerCase()
    resultado = resultado.filter(a => {
      const busca = `${a.codigo_patrimonial} ${a.marca} ${a.modelo} ${a.tipo_ativo}`.toLowerCase()
      return busca.includes(termo)
    })
  }

  if (filtroPredioBusca.value) {
    resultado = resultado.filter(a => {
      const locId = a.localizacao || a.id_localizacao || a.localizacao_id
      const loc = listaLocalizacoes.value.find(l => String(l.id_localizacao || l.id) === String(locId))
      if (!loc) return false
      return String(loc.predio || loc.id_predio) === String(filtroPredioBusca.value)
    })
  }

  if (filtroStatusPreventiva.value) {
    resultado = resultado.filter(a => obterCorStatus(a).status === filtroStatusPreventiva.value)
  }

  return resultado
})

const ativosAgrupados = computed(() => {
  const agrupado: Record<string, any[]> = {}
  
  ativosFiltrados.value.forEach(ativo => {
    const nomePredio = gerarNomePredio(ativo)
    if (!agrupado[nomePredio]) {
      agrupado[nomePredio] = []
    }
    agrupado[nomePredio].push(ativo)
  })

  return Object.keys(agrupado).sort().reduce((obj: Record<string, any[]>, key) => {
    obj[key] = agrupado[key]
    return obj
  }, {})
})

const localizacoesFiltradas = computed(() => {
  if (!idPredioSelecionado.value) return []
  return listaLocalizacoes.value.filter(l => String(l.predio || l.id_predio) === String(idPredioSelecionado.value))
})

async function carregarDados() {
  loading.value = true
  try {
    const [resAtivos, resPredios, resLoc] = await Promise.all([
      api.get('/ativo/', authHeader()),
      api.get('/predio/', authHeader()),
      api.get('/localizacao/', authHeader())
    ])
    ativos.value = resAtivos.data.dados || resAtivos.data || []
    listaPredios.value = resPredios.data.dados || resPredios.data || []
    listaLocalizacoes.value = resLoc.data.dados || resLoc.data || []
  } catch (error) {
    console.error('Erro ao buscar dados:', error)
  } finally {
    loading.value = false
  }
}

function aoTrocarPredio() {
  form.value.id_localizacao = '' 
}

function resetarForm() {
  form.value = { id_ativo: null, codigo_patrimonial: '', tipo_ativo: 'AR_CONDICIONADO', marca: '', modelo: '', numero_serial: '', periodicidade_preventiva_dias: 30, dt_ultima_preventiva: '', id_localizacao: '' }
  idPredioSelecionado.value = null
}

function abrirModalNovo() {
  resetarForm()
  modoEdicao.value = false
  modalAberto.value = true
}

function abrirModalEdicao(ativo: any) {
  modoEdicao.value = true
  const idAtivoReal = ativo.id_ativo || ativo.id;
  const locIdReal = ativo.localizacao || ativo.id_localizacao || ativo.localizacao_id;

  form.value = { 
    id_ativo: idAtivoReal, codigo_patrimonial: ativo.codigo_patrimonial || '', tipo_ativo: ativo.tipo_ativo || 'AR_CONDICIONADO',
    marca: ativo.marca || '', modelo: ativo.modelo || '', numero_serial: ativo.numero_serial || '',
    periodicidade_preventiva_dias: ativo.periodicidade_preventiva_dias || 30, dt_ultima_preventiva: ativo.dt_ultima_preventiva || '', id_localizacao: locIdReal || ''
  }
  
  const locEncontrada = listaLocalizacoes.value.find(l => String(l.id_localizacao || l.id) === String(locIdReal))
  if (locEncontrada) idPredioSelecionado.value = locEncontrada.predio || locEncontrada.id_predio
  
  modalAberto.value = true
}

function fecharModal() { modalAberto.value = false }

// === O FILTRO SUPREMO PARA O HISTÓRICO DO ATIVO ===
async function abrirModalDetalhes(ativo: any) {
  ativoSelecionado.value = ativo
  modalDetalhesAberto.value = true
  loadingHistorico.value = true
  historicoAtivo.value = []
  
  try {
    const id = ativo.id_ativo || ativo.id
    const pat = String(ativo.codigo_patrimonial || 'SEM_PAT').trim().toUpperCase()
    const locIdAtivo = ativo.localizacao || ativo.id_localizacao || ativo.localizacao_id

    let response = await api.get(`/ativo/${id}/historico/`, authHeader()).catch(() => null)
    let hist = response?.data?.dados || response?.data || []
    
    // SE O BACKEND FALHOU, O VUE ASSUME O CONTROLE!
    if (!Array.isArray(hist) || hist.length === 0) {
        const resOs = await api.get(`/ordem-servico/`, authHeader()).catch(() => null)
        const todasOrdens = resOs?.data?.dados || resOs?.data || []
        
        hist = todasOrdens.filter((os: any) => {
            const taConcluida = os.status_ordem_servico === 'CONCLUIDA' || os.status_ordem_servico === 'ENCERRADA'
            if (!taConcluida) return false;

            const osLocId = os.localizacao || os.localizacao_id || os.id_localizacao
            const stringDaOs = JSON.stringify(os).toUpperCase()
            
            const ehDoAtivoPeloId = String(os.ativo) === String(id) || String(os.ativo_id) === String(id)
            const ehDoAtivoPeloPat = pat !== 'SEM_PAT' && stringDaOs.includes(pat)
            
            // O FILTRO APELÃO: Se a OS foi concluída na mesma sala do Ar Condicionado, PODE MOSTRAR!
            const ehDoAtivoPelaSala = osLocId && locIdAtivo && String(osLocId) === String(locIdAtivo)

            return ehDoAtivoPeloId || ehDoAtivoPeloPat || ehDoAtivoPelaSala
        })
    }
    
    historicoAtivo.value = hist
  } catch (error) {
    console.error("Erro histórico:", error)
  } finally {
    loadingHistorico.value = false
  }
}

function fecharModalDetalhes() { modalDetalhesAberto.value = false; ativoSelecionado.value = null }

async function salvarAtivo() {
  if (!form.value.codigo_patrimonial || !form.value.marca || !form.value.modelo || !form.value.id_localizacao) {
    return Swal.fire({ title: 'Atenção', text: 'Preencha todos os campos obrigatórios (*).', icon: 'warning' })
  }

  salvando.value = true
  try {
    const payload = {
      codigo_patrimonial: form.value.codigo_patrimonial, tipo_ativo: form.value.tipo_ativo, marca: form.value.marca, modelo: form.value.modelo,
      numero_serial: form.value.numero_serial, periodicidade_preventiva_dias: form.value.periodicidade_preventiva_dias,
      dt_ultima_preventiva: form.value.dt_ultima_preventiva || null, id_localizacao: form.value.id_localizacao, localizacao: form.value.id_localizacao 
    }

    if (modoEdicao.value) {
      if (!form.value.id_ativo) throw new Error("ID não encontrado.");
      await api.put(`/ativo/${form.value.id_ativo}/`, payload, authHeader())
      Swal.fire({ title: 'Atualizado!', text: 'Ativo atualizado.', icon: 'success', timer: 2000, showConfirmButton: false })
    } else {
      await api.post('/ativo/', payload, authHeader())
      Swal.fire({ title: 'Criado!', text: 'Novo ativo registado.', icon: 'success', timer: 2000, showConfirmButton: false })
    }

    fecharModal()
    await carregarDados()
  } catch (error: any) {
    Swal.fire({ title: 'Erro ao salvar', text: "Falha na comunicação com o servidor.", icon: 'error', customClass: { popup: 'rounded-2xl' } })
  } finally {
    salvando.value = false
  }
}

async function excluirAtivo(id: number) {
  const result = await Swal.fire({ title: 'Remover Ativo?', text: 'Deseja remover este equipamento?', icon: 'warning', showCancelButton: true, confirmButtonColor: '#ef4444', confirmButtonText: 'Remover', cancelButtonText: 'Cancelar' })
  if (!result.isConfirmed) return

  try {
    await api.delete(`/ativo/${id}/`, authHeader())
    Swal.fire({ title: 'Removido!', text: 'Ativo excluído.', icon: 'success', timer: 2000, showConfirmButton: false })
    carregarDados()
  } catch (error) { Swal.fire({ title: 'Erro', text: 'Não foi possível remover.', icon: 'error' }) }
}

onMounted(() => carregarDados())
</script>

<style scoped> .animate-fade-in { animation: fadeIn 0.2s ease-out; } @keyframes fadeIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } } </style>