<template>
  <div class="p-8">
    <div class="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Preventivas por Prédio</h1>
        <p class="text-sm text-gray-500 mt-1">Agrupe ativos pendentes do mesmo prédio em uma única ordem preventiva</p>
      </div>
      <div class="relative w-full md:w-72">
        <span class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400 text-sm">🔍</span>
        <input v-model="busca" type="text" placeholder="Buscar prédio..." class="w-full bg-white border border-gray-200 text-gray-700 placeholder-gray-400 text-sm rounded-lg pl-9 pr-3 py-2.5 outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
    </div>

    <div v-if="loading" class="bg-white rounded-xl border border-gray-100 p-12 text-center text-gray-400 font-medium">A carregar painel...</div>
    <div v-else-if="erro" class="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
      <p class="text-sm font-semibold text-red-700 mb-3">{{ erro }}</p>
      <button @click="carregar" class="px-4 py-2 text-xs font-bold text-red-700 bg-white border border-red-200 rounded-lg hover:bg-red-100 cursor-pointer">Tentar novamente</button>
    </div>

    <template v-else>
      <section v-if="gruposAtivos.length" class="mb-8">
        <h2 class="text-sm font-bold text-gray-700 uppercase tracking-wider mb-3">⚙️ Ordens agrupadas em andamento</h2>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <div v-for="g in gruposAtivos" :key="g.id_ordem_servico" class="bg-white rounded-xl border border-indigo-100 shadow-sm p-4 flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-black text-gray-800">OS #{{ g.id_ordem_servico }} <span class="font-medium text-gray-500">· {{ nomePredio(g.predio) }}</span></p>
              <p class="text-[11px] text-gray-500 mt-0.5">👷 {{ g.tecnico_nome || 'N/I' }} · {{ resolvidos(g) }}/{{ g.itens.length }} com resultado</p>
            </div>
            <button @click="grupoSelecionado = g" class="px-4 py-2 text-xs font-bold text-indigo-600 border border-indigo-200 hover:bg-indigo-600 hover:text-white rounded-lg transition-all cursor-pointer whitespace-nowrap">Registrar resultados</button>
          </div>
        </div>
      </section>

      <div v-if="cardsFiltrados.length === 0" class="bg-white rounded-xl border border-gray-100 p-12 text-center">
        <span class="text-5xl block mb-3 opacity-50">🎉</span>
        <p class="text-gray-500 font-semibold">{{ cards.length === 0 ? 'Nenhum ativo pendente ou atrasado.' : 'Nenhum prédio encontrado.' }}</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <button v-for="c in cardsFiltrados" :key="c.id_predio" @click="cardAberto = c" data-testid="card-predio"
          class="text-left bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:border-purple-200 transition-all p-5 cursor-pointer">
          <div class="flex items-start justify-between gap-3 mb-4">
            <h3 class="text-base font-bold text-gray-800 flex items-center gap-2"><span class="text-blue-600">🏢</span> {{ c.nome_predio }}</h3>
            <span class="text-xs font-bold text-gray-500 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-200">{{ c.ativos.length }} ativo(s)</span>
          </div>
          <div class="grid grid-cols-3 gap-2 text-center">
            <div class="rounded-lg bg-red-50 border border-red-100 py-2"><p class="text-xl font-black text-red-600">{{ c.atrasados }}</p><p class="text-[10px] font-bold text-red-400 uppercase">Atrasados</p></div>
            <div class="rounded-lg bg-orange-50 border border-orange-100 py-2"><p class="text-xl font-black text-orange-500">{{ c.pendentes }}</p><p class="text-[10px] font-bold text-orange-400 uppercase">Pendentes</p></div>
            <div class="rounded-lg bg-amber-50 border border-amber-100 py-2"><p class="text-xl font-black text-amber-600">{{ c.emExecucao }}</p><p class="text-[10px] font-bold text-amber-500 uppercase">Em execução</p></div>
          </div>
          <p class="text-[11px] font-bold text-purple-600 mt-4">{{ c.atrasados + c.pendentes > 0 ? 'Abrir e agrupar ativos →' : 'Ver ativos →' }}</p>
        </button>
      </div>
    </template>

    <GerarOrdemAgrupadaModal v-if="cardAberto" :card="cardAberto" :tecnicos="tecnicos" :enviando="enviando"
      @fechar="cardAberto = null" @confirmar="gerar" />
    <ResultadosGrupoModal v-if="grupoSelecionado" :grupo="grupoSelecionado" :nomes="nomesAtivos" :enviando="enviando"
      @fechar="grupoSelecionado = null" @confirmar="salvarResultados" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Swal from 'sweetalert2'
import GerarOrdemAgrupadaModal from '@/components/GerarOrdemAgrupadaModal.vue'
import ResultadosGrupoModal from '@/components/ResultadosGrupoModal.vue'
import {
  PreventivaGrupoError, carregarDadosPainel, gerarOrdemAgrupada, listarTecnicos, registrarResultados,
} from '@/services/preventivaGrupoService'
import type { CardPredio, DadosGerarOrdem, ErroGrupo, GrupoPreventiva, ResultadoItemEnvio } from '@/types/preventivaGrupo'
import { construirPainel, grupoAtivo } from '@/utils/painelPreventivas'

const cards = ref<CardPredio[]>([])
const grupos = ref<GrupoPreventiva[]>([])
const predios = ref<any[]>([])
const nomesAtivos = ref<Record<number, string>>({})
const tecnicos = ref<any[]>([])
const loading = ref(true)
const erro = ref('')
const busca = ref('')
const enviando = ref(false)
const cardAberto = ref<CardPredio | null>(null)
const grupoSelecionado = ref<GrupoPreventiva | null>(null)

const gruposAtivos = computed(() => grupos.value.filter(grupoAtivo))
const cardsFiltrados = computed(() => {
  const t = busca.value.trim().toLowerCase()
  return t ? cards.value.filter((c) => c.nome_predio.toLowerCase().includes(t)) : cards.value
})

const resolvidos = (g: GrupoPreventiva) => g.itens.filter((i) => i.resultado !== 'PENDENTE').length
const nomePredio = (id: number) => predios.value.find((p) => Number(p.id_predio ?? p.id) === id)?.nome_predio || `Prédio #${id}`

async function carregar() {
  loading.value = true
  erro.value = ''
  try {
    const d = await carregarDadosPainel()
    predios.value = d.predios
    grupos.value = d.grupos
    cards.value = construirPainel(d.ativos, d.predios, d.localizacoes, d.grupos)
    nomesAtivos.value = Object.fromEntries(
      d.ativos.map((a: any) => [Number(a.id_ativo ?? a.id), `${a.marca ?? ''} ${a.modelo ?? ''} (PAT: ${a.codigo_patrimonial || 'N/I'})`.trim()]),
    )
    // mantém o modal aberto sincronizado com os dados novos
    if (cardAberto.value) cardAberto.value = cards.value.find((c) => c.id_predio === cardAberto.value!.id_predio) ?? null
    if (grupoSelecionado.value) grupoSelecionado.value = grupos.value.find((g) => g.id_ordem_servico === grupoSelecionado.value!.id_ordem_servico) ?? null
  } catch (e) {
    console.error('Erro ao carregar painel de preventivas', e)
    erro.value = 'Não foi possível carregar o painel de preventivas.'
  } finally {
    loading.value = false
  }
}

const MENSAGENS: Record<ErroGrupo['tipo'], { titulo: string; texto: string }> = {
  FORA_ESCOPO: { titulo: 'Sem permissão', texto: 'Você não tem permissão para esta ação.' },
  MESMO_PREDIO: { titulo: 'Prédios diferentes', texto: 'Só é possível agrupar ativos do mesmo prédio.' },
  STATUS_INVALIDO: { titulo: 'Ação indisponível', texto: 'Algum ativo já está vinculado a outra ordem. O painel foi atualizado.' },
  VALIDACAO: { titulo: 'Dados inválidos', texto: 'Revise a seleção e o técnico informado.' },
  INDISPONIVEL: { titulo: 'Recurso indisponível', texto: 'O servidor ainda não oferece a ordem preventiva agrupada.' },
  GENERICO: { titulo: 'Erro', texto: 'Não foi possível concluir a operação. Tente novamente.' },
}

async function tratarErro(e: unknown) {
  if (e instanceof PreventivaGrupoError) {
    const { titulo, texto } = MENSAGENS[e.info.tipo]
    await Swal.fire({
      title: titulo, text: e.info.tipo === 'GENERICO' ? e.info.mensagem || texto : texto,
      icon: e.info.tipo === 'GENERICO' ? 'error' : 'info', confirmButtonColor: '#2563eb',
    })
    if (e.info.tipo === 'STATUS_INVALIDO') await carregar()
  } else {
    console.error('Erro nas preventivas agrupadas', e)
    Swal.fire({ title: 'Erro', text: MENSAGENS.GENERICO.texto, icon: 'error' })
  }
}

// CA3: um único código de OS, todos os ativos selecionados vinculados.
async function gerar(dados: DadosGerarOrdem) {
  enviando.value = true
  try {
    const r = await gerarOrdemAgrupada(dados)
    cardAberto.value = null
    await carregar()
    await Swal.fire({
      title: 'Ordem gerada!',
      text: `${r.id_ordem_servico ? `OS #${r.id_ordem_servico}` : 'Ordem'} criada com ${dados.ativos.length} ativo(s). Eles passaram para "Em execução".`,
      icon: 'success', timer: 3000, showConfirmButton: false,
    })
  } catch (e) {
    await tratarErro(e)
  } finally {
    enviando.value = false
  }
}

// CA4: resultados por ativo; o backend encerra a ordem quando todos tiverem resultado.
async function salvarResultados(itens: ResultadoItemEnvio[]) {
  const alvo = grupoSelecionado.value
  if (!alvo) return
  enviando.value = true
  try {
    await registrarResultados(alvo.id_ordem_servico, itens)
    grupoSelecionado.value = null
    await carregar()
    await Swal.fire({ title: 'Resultados registrados!', icon: 'success', timer: 2500, showConfirmButton: false })
  } catch (e) {
    await tratarErro(e)
  } finally {
    enviando.value = false
  }
}

onMounted(async () => {
  tecnicos.value = await listarTecnicos()
  await carregar()
})
</script>