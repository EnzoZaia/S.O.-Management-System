<template>
  <div class="p-8">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-800">Ordens de Serviço</h1>
      <p class="text-sm text-gray-500 mt-1">Gerencie, aprove e atribua técnicos às ordens sob sua responsabilidade</p>
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
          <option value="AGUARDANDO_VALIDACAO">Aguard. Validação</option>
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
          <input v-model="termoBusca" type="text" placeholder="Buscar por descrição ou local..." class="w-full bg-white border border-gray-200 text-gray-700 placeholder-gray-400 text-xs font-medium rounded-lg pl-9 pr-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-text" />
        </div>
      </div>
      <button @click="limparFiltros" class="px-5 py-2.5 text-xs font-bold text-gray-600 bg-gray-100 border border-gray-200 hover:bg-gray-200 hover:text-gray-800 rounded-lg transition-colors cursor-pointer shadow-sm">
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

    <div class="bg-white rounded-b-xl shadow-sm border border-gray-100 overflow-hidden">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-gray-50 border-b border-gray-100 text-xs text-gray-500 uppercase tracking-wider">
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
            <td colspan="6" class="p-8 text-center text-gray-400 font-medium">Carregando ordens...</td>
          </tr>
          <tr v-else-if="ordensFiltradas.length === 0" class="border-b border-gray-50">
            <td colspan="6" class="p-8 text-center text-gray-400 font-medium">Nenhuma ordem nesta categoria.</td>
          </tr>
          <tr v-else v-for="os in ordensFiltradas" :key="os.id_ordem_servico" class="border-b border-gray-50 hover:bg-gray-50 transition-colors">
            <td class="p-4">
              <div class="text-sm font-bold text-gray-800 mb-1">#{{ os.id_ordem_servico }}</div>
            </td>
            <td class="p-4 text-sm text-gray-600 truncate max-w-[200px]">{{ os.predio_nome || 'N/I' }} - {{ os.localizacao_nome || 'N/I' }}</td>
            <td class="p-4">
              <div v-if="os.tipo_manutencao === 'PREVENTIVA'">
                <p class="text-sm font-bold text-gray-800 flex items-center gap-1">
                  Inspeção: {{ os.ativo_nome || 'Equipamento' }}
                  <span class="text-[10px] bg-purple-100 text-purple-700 font-bold px-1.5 py-0.5 rounded ml-1 border border-purple-200">PAT: {{ os.ativo_patrimonio || 'N/I' }}</span>
                </p>
                <div class="flex items-center gap-3 mt-1 text-[11px] text-gray-500">
                  <p><span class="font-bold text-gray-400">Última:</span> {{ os.ativo_ultima_preventiva ? formatarDataSimples(os.ativo_ultima_preventiva) : 'N/I' }}</p>
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

    <div v-if="modalAberto" @click.self="fecharModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4 animate-fade-in">
      <div class="bg-white rounded-2xl w-full max-w-4xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50 shrink-0">
          <div>
            <p class="text-xs font-bold text-gray-400 uppercase tracking-wider">Ordem de Serviço</p>
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

            <!-- US09: durante a triagem a prioridade é definida no painel de triagem -->
            <div v-if="osSelecionada?.status_ordem_servico !== 'ABERTA'" class="relative">
              <select :value="osSelecionada?.prioridade_urgencia" @change="alterarPrioridade(($event.target as HTMLSelectElement).value)"
                class="pl-4 pr-8 py-1.5 rounded-full text-sm font-bold outline-none cursor-pointer appearance-none border transition-colors bg-gray-50 border-gray-200 hover:bg-gray-100 text-gray-700"
                :class="osSelecionada?.prioridade_urgencia === 'SIM' ? 'text-red-700 bg-red-50 border-red-200 hover:bg-red-100' : ''">
                <option value="NAO">Prioridade: Normal</option>
                <option value="SIM"> Urgente</option>
              </select>
              <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3" :class="osSelecionada?.prioridade_urgencia === 'SIM' ? 'text-red-500' : 'text-gray-500'">
                <svg class="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"> <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" /> </svg>
              </div>
            </div>
          </div>

          <div v-if="osSelecionada?.tipo_manutencao === 'PREVENTIVA'" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 bg-purple-50/50 p-5 rounded-2xl border border-purple-100 shadow-sm">
              <div>
                <p class="text-[10px] font-black text-purple-600 uppercase tracking-wider mb-1">Última Preventiva Realizada</p>
                <p class="text-base font-bold text-gray-800">{{ osSelecionada?.ativo_ultima_preventiva ? formatarDataSimples(osSelecionada.ativo_ultima_preventiva) : 'Nenhum registro anterior' }}</p>
              </div>
              <div>
                <p class="text-[10px] font-black text-purple-600 uppercase tracking-wider mb-1">Próxima Preventiva Agendada</p>
                <p class="text-base font-bold text-purple-700">{{ osSelecionada?.ativo_proxima_preventiva ? formatarDataSimples(osSelecionada.ativo_proxima_preventiva) : 'Não agendada' }}</p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 md:col-span-2">
                <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Equipamento Alvo</p>
                <p class="text-sm font-bold text-gray-800">❄️ {{ osSelecionada?.ativo_nome || 'Ar Condicionado Não Especificado' }}</p>
                <p class="text-[10px] text-gray-500 font-mono mt-0.5">PAT: {{ osSelecionada?.ativo_patrimonio || 'N/I' }}</p>
              </div>
              <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Localização (Prédio / Sala)</p>
                <p class="text-sm font-bold text-gray-800">{{ osSelecionada?.predio_nome }} - {{ osSelecionada?.localizacao_nome }}</p>
              </div>
              <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Técnico Atribuído</p>
                <p class="text-sm font-bold text-gray-800">{{ osSelecionada?.tecnico_nome || 'Aguardando atribuição' }}</p>
              </div>
              <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Solicitante</p>
                <p class="text-sm font-bold text-gray-800">{{ extrairSolicitante(osSelecionada) }}</p>
              </div>
              <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Gestor do Cronograma</p>
                <p class="text-sm font-bold text-gray-800">{{ osSelecionada?.gestor_nome || 'Sem gestor' }}</p>
              </div>
            </div>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
              <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Local (Prédio / Sala)</p>
              <p class="text-sm font-bold text-gray-800">{{ osSelecionada?.predio_nome || 'N/I' }} - {{ osSelecionada?.localizacao_nome || 'N/I' }}</p>
            </div>
            <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
              <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Solicitante</p>
              <p class="text-sm font-bold text-gray-800">{{ extrairSolicitante(osSelecionada) }}</p>
            </div>
            <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
              <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">Gestor Responsável</p>
              <p class="text-sm font-bold text-gray-800">{{ osSelecionada?.gestor_nome || 'Na fila de triagem (Sem gestor)' }}</p>
            </div>
            <div class="bg-white p-4 rounded-xl border border-blue-100 shadow-sm">
              <p class="text-[11px] font-bold text-blue-600 mb-1 uppercase tracking-wider">Técnico Atribuído</p>
              <p class="text-sm font-bold text-gray-800">{{ osSelecionada?.tecnico_nome || 'Nenhum técnico atribuído' }}</p>
            </div>
          </div>

          <!-- US09: painel de triagem -->
          <div v-if="osSelecionada?.status_ordem_servico === 'ABERTA'" data-testid="painel-triagem"
            class="mt-6 rounded-2xl border border-blue-100 bg-blue-50/40 p-5 space-y-4">
            <div>
              <p class="text-[11px] font-black text-blue-600 uppercase tracking-wider">Triagem da ordem</p>
              <p class="text-xs text-gray-500 mt-0.5">Classifique e decida. A decisão fica registrada no histórico.</p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <button v-for="d in DECISOES" :key="d.valor" type="button" @click="escolherDecisao(d.valor)"
                :class="triagem.decisao === d.valor ? d.ativo : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'"
                class="py-2.5 rounded-xl border text-sm font-bold transition-all cursor-pointer">{{ d.rotulo }}</button>
            </div>
            <p v-if="errosTriagem.decisao" role="alert" class="text-xs font-medium text-red-600">{{ errosTriagem.decisao }}</p>

            <div v-if="triagem.decisao === 'APROVAR'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Categoria técnica *</label>
                <select v-model="triagem.categoria" @change="errosTriagem.categoria = ''"
                  :class="errosTriagem.categoria ? 'border-red-500' : 'border-gray-200'"
                  class="w-full bg-white border text-gray-700 text-sm font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer">
                  <option value="" disabled>Selecione...</option>
                  <option v-for="c in CATEGORIAS" :key="c.valor" :value="c.valor">{{ c.rotulo }}</option>
                </select>
                <p v-if="errosTriagem.categoria" role="alert" class="text-[11px] font-medium text-red-600">{{ errosTriagem.categoria }}</p>
              </div>
              <div class="space-y-1.5">
                <label class="text-xs font-bold text-gray-500 uppercase tracking-wider">Prioridade *</label>
                <select v-model="triagem.prioridade" @change="errosTriagem.prioridade = ''"
                  :class="errosTriagem.prioridade ? 'border-red-500' : 'border-gray-200'"
                  class="w-full bg-white border text-gray-700 text-sm font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer">
                  <option value="NAO">Normal</option>
                  <option value="SIM">🚨 Urgente</option>
                </select>
                <p v-if="errosTriagem.prioridade" role="alert" class="text-[11px] font-medium text-red-600">{{ errosTriagem.prioridade }}</p>
              </div>
            </div>

            <div v-if="triagem.decisao === 'REPROVAR' || triagem.decisao === 'CANCELAR'" class="space-y-1.5">
              <label for="just-triagem" class="text-xs font-bold text-gray-500 uppercase tracking-wider">Justificativa *</label>
              <textarea id="just-triagem" v-model="triagem.justificativa" @blur="validarJustificativaCampo" rows="3"
                :maxlength="JUSTIFICATIVA_TRIAGEM_MAX"
                :placeholder="triagem.decisao === 'CANCELAR' ? 'Por que esta ordem está sendo cancelada?' : 'Por que a triagem está sendo reprovada?'"
                :class="errosTriagem.justificativa ? 'border-red-500 focus:ring-red-400' : 'border-gray-200 focus:ring-blue-500'"
                class="w-full bg-white border text-gray-700 text-sm rounded-lg p-3 outline-none focus:ring-2 resize-none"></textarea>
              <div class="flex justify-between text-[11px]">
                <span class="text-red-600 font-medium">{{ errosTriagem.justificativa }}</span>
                <span class="text-gray-400 font-semibold">{{ triagem.justificativa.trim().length }}/{{ JUSTIFICATIVA_TRIAGEM_MAX }}</span>
              </div>
            </div>
          </div>

          <div class="mt-6">
            <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">
              {{ osSelecionada?.tipo_manutencao === 'PREVENTIVA' ? 'Roteiro de Inspeção Programada' : 'Descrição do Problema Reportado' }}
            </p>
            <div class="p-4 bg-gray-50 rounded-xl border border-gray-100 text-sm text-gray-700 whitespace-pre-wrap">{{ extrairProblema(osSelecionada?.descricao_servico) }}</div>
          </div>
        </div>

        <div class="p-6 border-t border-gray-100 bg-gray-50 flex flex-col sm:flex-row items-center justify-between gap-4 rounded-b-2xl shrink-0">
          <div class="w-full sm:w-auto" v-if="osSelecionada?.status_ordem_servico === 'ABERTA' || osSelecionada?.status_ordem_servico === 'APROVADA'">
            <div class="flex items-center gap-3">
              <label class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">{{ osSelecionada?.status_ordem_servico === 'ABERTA' ? 'Atribuir a (opcional):' : 'Atribuir a:' }}</label>
              <select v-model="tecnicoSelecionado" class="bg-white border border-gray-200 text-gray-700 text-sm font-bold rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500 shadow-sm cursor-pointer min-w-[180px]">
                <option value="" disabled>Selecione um técnico...</option>
                <option v-for="tec in tecnicosDisponiveis" :key="tec.id_usuario" :value="tec.id_usuario">{{ tec.nome }}</option>
              </select>
            </div>
          </div>
          <div v-else class="text-xs font-bold text-gray-400">
            Ações limitadas pelo status atual ({{ formatarStatus(osSelecionada?.status_ordem_servico) }})
          </div>

          <div class="flex gap-3 w-full sm:w-auto justify-end">
            <button @click="fecharModal" class="px-5 py-2.5 text-sm font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl transition-colors cursor-pointer">Fechar</button>

            <button v-if="osSelecionada?.status_ordem_servico === 'ABERTA'" @click="confirmarTriagem"
              :disabled="salvandoTriagem || !triagem.decisao"
              :class="triagem.decisao === 'APROVAR' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-red-600 hover:bg-red-700'"
              class="px-5 py-2.5 text-sm font-bold text-white rounded-xl transition-colors shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
              {{ salvandoTriagem ? 'Salvando...' : rotuloConfirmar }}
            </button>

            <button v-if="osSelecionada?.status_ordem_servico === 'APROVADA'" @click="confirmarAtribuicao"
              class="px-5 py-2.5 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-colors shadow-sm cursor-pointer flex items-center gap-2">
              <span>✅</span> Salvar Atribuição
            </button>
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
import { TriagemError, decidirTriagem } from '@/services/triagemService'
import type { DecisaoTriagem, ErroTriagem, ErrosTriagem, FormularioTriagem } from '@/types/triagem'
import {
  CATEGORIAS, JUSTIFICATIVA_TRIAGEM_MAX, validarJustificativaTriagem, validarTriagem,
} from '@/utils/validacaoTriagem'

const abaAtiva = ref('CORRETIVA')
const ordens = ref<any[]>([])
const loading = ref(true)

const filtroDataInicio = ref('')
const filtroDataFim = ref('')
const filtroStatus = ref('TODOS')
const filtroPrioridade = ref('TODAS')
const filtroPredio = ref('TODOS')
const termoBusca = ref('')

const modalAberto = ref(false)
const osSelecionada = ref<any>(null)
const tecnicosDisponiveis = ref<any[]>([])
const tecnicoSelecionado = ref('')

// === US09: triagem ===
const DECISOES: { valor: DecisaoTriagem; rotulo: string; ativo: string }[] = [
  { valor: 'APROVAR', rotulo: '✅ Aprovar', ativo: 'bg-blue-600 text-white border-blue-600 shadow-md' },
  { valor: 'REPROVAR', rotulo: '🚫 Reprovar', ativo: 'bg-orange-500 text-white border-orange-500 shadow-md' },
  { valor: 'CANCELAR', rotulo: '❌ Cancelar', ativo: 'bg-red-600 text-white border-red-600 shadow-md' },
]

const triagem = ref<FormularioTriagem>({ decisao: null, categoria: '', prioridade: 'NAO', justificativa: '' })
const errosTriagem = ref<ErrosTriagem>({})
const salvandoTriagem = ref(false)

const rotuloConfirmar = computed(() => {
  if (triagem.value.decisao === 'APROVAR') return tecnicoSelecionado.value ? 'Aprovar e Atribuir' : 'Aprovar ordem'
  if (triagem.value.decisao === 'REPROVAR') return 'Confirmar reprovação'
  if (triagem.value.decisao === 'CANCELAR') return 'Confirmar cancelamento'
  return 'Selecione uma decisão'
})

function resetarTriagem(os?: any) {
  triagem.value = {
    decisao: null,
    categoria: CATEGORIAS.some((c) => c.valor === os?.categoria_manutencao) ? os.categoria_manutencao : '',
    prioridade: os?.prioridade_urgencia === 'SIM' ? 'SIM' : 'NAO',
    justificativa: '',
  }
  errosTriagem.value = {}
}

function escolherDecisao(decisao: DecisaoTriagem) {
  triagem.value.decisao = decisao
  errosTriagem.value = {}
}

function validarJustificativaCampo() {
  const d = triagem.value.decisao
  if (d !== 'REPROVAR' && d !== 'CANCELAR') return
  errosTriagem.value = { ...errosTriagem.value, justificativa: validarJustificativaTriagem(triagem.value.justificativa, d) ?? '' }
}

const prediosUnicos = computed(() => {
  const nomes = new Set(ordens.value.map(os => os.predio_nome).filter(Boolean))
  return Array.from(nomes).sort()
})

const extrairSolicitante = (os: any) => {
  if (!os) return ''
  if (os.tipo_manutencao === 'PREVENTIVA') return 'Sistema (Automático)'
  const match = os.descricao_servico?.match(/\[(.*?)\]/);
  if (match) return match[1];
  return os.solicitante_nome || 'Usuário Anônimo / Totem';
}

const extrairProblema = (descricao: string) => {
  if (!descricao) return 'Sem descrição detalhada.'
  return descricao.replace(/\[.*?\]\s*(-\s*Local:.*?\s*)?-\s*(Problema:\s*)?/, '').trim();
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
  let resultado = ordens.value.filter(os => os.tipo_manutencao === abaAtiva.value)

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
      (os.localizacao_nome || '').toLowerCase().includes(termo) ||
      (os.descricao_servico || '').toLowerCase().includes(termo)
    )
  }
  return resultado
})

const formatarStatus = (status: string) => {
  const mapa: Record<string, string> = {
    'ABERTA': 'Aberta', 'APROVADA': 'Para Iniciar', 'EM_EXECUCAO': 'Em Execução', 'AGUARDANDO_MATERIAL': 'Falta Material',
    'AGUARDANDO_TERCEIRO': 'Aguard. Terceiro', 'CONCLUIDA': 'Concluída', 'ENCERRADA': 'Encerrada', 'CANCELADA': 'Cancelada', 'REPROVADA': 'Reprovada'
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

async function carregarTecnicos() {
  try {
    const response = await api.get('/usuario/', authHeader())
    const listaUsuarios = response.data.dados || response.data
    tecnicosDisponiveis.value = listaUsuarios.filter((u: any) => u.grupo_descricao === 'TECNICO' || u.cargo === 'TECNICO')
  } catch (error) { console.error("Erro ao carregar técnicos:", error) }
}

function abrirModalDetalhes(os: any) {
  osSelecionada.value = os
  tecnicoSelecionado.value = os.tecnico_id || ''
  resetarTriagem(os)
  modalAberto.value = true
  if (tecnicosDisponiveis.value.length === 0) carregarTecnicos()
}

function fecharModal() {
  modalAberto.value = false
  osSelecionada.value = null
  resetarTriagem()
}

async function alterarPrioridade(novaPrioridade: string) {
  try {
    await api.patch(`/ordem-servico/${osSelecionada.value.id_ordem_servico}/`, { prioridade_urgencia: novaPrioridade }, authHeader())
    osSelecionada.value.prioridade_urgencia = novaPrioridade
    Swal.mixin({ toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, timerProgressBar: true }).fire({ icon: 'success', title: 'Prioridade alterada!' })
    carregarOrdens()
  } catch (error) { Swal.fire({ title: 'Erro', text: 'Não foi possível alterar a prioridade.', icon: 'error' }) }
}

// === US09: decisão de triagem (aprovar / reprovar / cancelar) ===
const MENSAGENS_TRIAGEM: Record<ErroTriagem['tipo'], { titulo: string; texto: string }> = {
  FORA_ESCOPO: { titulo: 'Sem acesso', texto: 'Esta ordem não pertence ao seu escopo de responsabilidade.' },
  STATUS_INVALIDO: { titulo: 'Ação indisponível', texto: 'Esta ordem não está mais em triagem. A lista foi atualizada.' },
  VALIDACAO: { titulo: 'Dados inválidos', texto: 'Revise os campos destacados.' },
  GENERICO: { titulo: 'Erro', texto: 'Não foi possível registrar a decisão. Tente novamente.' },
}

async function confirmarTriagem() {
  const os = osSelecionada.value
  if (!os || salvandoTriagem.value) return

  errosTriagem.value = validarTriagem(triagem.value) // CA1 / CA2
  if (Object.keys(errosTriagem.value).length > 0) return

  const decisao = triagem.value.decisao as DecisaoTriagem
  if (decisao !== 'APROVAR') {
    const r = await Swal.fire({
      title: decisao === 'CANCELAR' ? 'Cancelar esta ordem?' : 'Reprovar a triagem?',
      text: 'A decisão ficará registrada no histórico e não poderá ser desfeita.',
      icon: 'warning', showCancelButton: true, confirmButtonColor: '#ef4444', cancelButtonColor: '#6b7280',
      confirmButtonText: decisao === 'CANCELAR' ? 'Sim, cancelar' : 'Sim, reprovar', cancelButtonText: 'Voltar',
      customClass: { confirmButton: 'cursor-pointer', cancelButton: 'cursor-pointer' },
    })
    if (!r.isConfirmed) return
  }

  salvandoTriagem.value = true
  try {
    await decidirTriagem(os.id_ordem_servico, {
      decisao,
      categoria: triagem.value.categoria || undefined,
      prioridade: triagem.value.prioridade,
      justificativa: triagem.value.justificativa,
    })

    let avisoAtribuicao = ''
    if (decisao === 'APROVAR' && tecnicoSelecionado.value) {
      try {
        await api.patch(`/ordem-servico/${os.id_ordem_servico}/atribuir-tecnico/`, { tecnico: tecnicoSelecionado.value }, authHeader())
      } catch {
        avisoAtribuicao = ' A atribuição do técnico falhou: faça-a pela ordem aprovada.'
      }
    }

    const texto = {
      APROVAR: 'Ordem aprovada e disponível para atribuição.',
      REPROVAR: 'Triagem reprovada e registrada no histórico.',
      CANCELAR: 'Ordem cancelada e registrada no histórico.',
    }[decisao] + avisoAtribuicao
    await Swal.fire({ title: 'Decisão registrada!', text: texto, icon: avisoAtribuicao ? 'warning' : 'success', timer: 3000, showConfirmButton: false })
    fecharModal()
    await carregarOrdens()
  } catch (e) {
    if (e instanceof TriagemError) {
      errosTriagem.value = e.info.campos
      const { titulo, texto } = MENSAGENS_TRIAGEM[e.info.tipo]
      await Swal.fire({
        title: titulo, text: e.info.tipo === 'GENERICO' ? e.info.mensagem || texto : texto,
        icon: e.info.tipo === 'GENERICO' ? 'error' : 'info', confirmButtonColor: '#2563eb',
      })
      if (e.info.tipo === 'FORA_ESCOPO' || e.info.tipo === 'STATUS_INVALIDO') { fecharModal(); await carregarOrdens() } // CA3
    } else {
      console.error('Erro na triagem', e)
      Swal.fire({ title: 'Erro', text: 'Não foi possível registrar a decisão. Tente novamente.', icon: 'error' })
    }
  } finally {
    salvandoTriagem.value = false
  }
}

// Atribuição de técnico para ordens já APROVADAS
async function confirmarAtribuicao() {
  if (!tecnicoSelecionado.value) {
    Swal.fire({ title: 'Atenção', text: 'Selecione um técnico antes de salvar a atribuição.', icon: 'warning' })
    return
  }
  try {
    await api.patch(`/ordem-servico/${osSelecionada.value.id_ordem_servico}/atribuir-tecnico/`, { tecnico: tecnicoSelecionado.value }, authHeader())
    Swal.fire({ title: 'Atribuída!', text: 'Técnico definido com sucesso.', icon: 'success', confirmButtonColor: '#2563eb', customClass: { confirmButton: 'cursor-pointer' } })
    fecharModal(); carregarOrdens()
  } catch (error: any) { Swal.fire({ title: 'Erro', text: 'Falha ao atribuir técnico.', icon: 'error' }) }
}

function limparFiltros() {
  filtroDataInicio.value = ''; filtroDataFim.value = ''; filtroStatus.value = 'TODOS'; filtroPrioridade.value = 'TODAS'; filtroPredio.value = 'TODOS'; termoBusca.value = ''
}

onMounted(() => carregarOrdens())
</script>

<style scoped> .animate-fade-in { animation: fadeIn 0.2s ease-out; } @keyframes fadeIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } } </style>