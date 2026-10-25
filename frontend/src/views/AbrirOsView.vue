<template>
  <div class="fixed inset-0 w-screen h-screen min-h-screen flex overflow-hidden bg-white select-none">

    <div class="hidden md:flex w-2/5 bg-blue-800 flex-col items-center justify-center gap-6 p-8 shrink-0">
      <img src="@/assets/img/FHO.png" alt="Logo da FHO" class="w-24 h-24 object-contain" />
      <div class="text-center">
        <h1 class="text-white text-2xl font-bold tracking-wide">Fundação Hermínio Ometto</h1>
        <p class="text-blue-200 text-sm mt-2 opacity-90">Abertura de Ordem de Serviço</p>
      </div>
    </div>

    <div class="flex-1 h-full overflow-y-auto bg-white flex flex-col justify-start md:justify-center items-center px-6 py-12 sm:px-12">
      <div class="w-full max-w-md space-y-6 my-auto">

        <div>
          <h2 class="text-blue-800 text-2xl font-bold mb-1">Nova OS</h2>
          <p class="text-gray-400 text-sm">Preencha os dados da ocorrência</p>
        </div>

        <div v-if="logado" class="bg-blue-50 border border-blue-100 rounded-lg px-4 py-3 text-sm text-blue-800">
          Abrindo como <strong>{{ authStore.usuario?.nome }}</strong>
        </div>

        <div v-else class="grid grid-cols-2 gap-4">
          <button type="button" @click="tipoUsuario = 'aluno'" :class="[
            'py-3 px-4 rounded-lg font-semibold border transition-all duration-200 cursor-pointer text-center text-sm',
            tipoUsuario === 'aluno'
              ? 'bg-blue-800 text-white border-blue-800 shadow-sm'
              : 'bg-white text-blue-800 border-gray-300 hover:bg-gray-50'
          ]">
            Aluno
          </button>

          <button type="button" @click="tipoUsuario = 'funcionario'" :class="[
            'py-3 px-4 rounded-lg font-semibold border transition-all duration-200 cursor-pointer text-center text-sm',
            tipoUsuario === 'funcionario'
              ? 'bg-blue-800 text-white border-blue-800 shadow-sm'
              : 'bg-white text-blue-800 border-gray-300 hover:bg-gray-50'
          ]">
            Funcionário
          </button>
        </div>

        <div class="space-y-4">
          <div v-if="!logado" class="flex flex-col gap-1.5">
            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              {{ tipoUsuario === 'aluno' ? 'RA - Registro do Aluno' : 'F - Número do Funcionário' }}
            </label>
            <input v-model="indentificacao" type="text"
              :placeholder="tipoUsuario === 'aluno' ? 'Ex: 123456' : 'Ex: F1234'"
              class="border border-gray-300 rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 w-full transition-all" />
          </div>

          <div class="flex flex-col gap-1.5 relative">
            <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Local (Prédio / Bloco)
            </label>
            <div @click="toggleDropdownPredio"
                 class="border border-gray-300 rounded-lg px-4 py-2.5 text-sm outline-none w-full cursor-pointer bg-white flex justify-between items-center transition-all min-h-[42px]"
                 :class="{'border-blue-600 ring-1 ring-blue-600': dropdownPredioAberto}">
              <span :class="localNomeSelecionado ? 'text-gray-800' : 'text-gray-400'">
                {{ localNomeSelecionado || 'Selecione o Prédio' }}
              </span>
              <svg class="w-4 h-4 text-gray-400 transition-transform" :class="{'rotate-180': dropdownPredioAberto}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>

            <div v-if="dropdownPredioAberto"
                 class="absolute left-0 right-0 top-[calc(100%+4px)] bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-48 overflow-y-auto">
              <ul class="py-1">
                <li v-for="predio in listaPredios" :key="predio.id_predio" @click="selecionarPredio(predio)"
                    class="px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-800 cursor-pointer transition-colors">
                  {{ predio.nome_predio }}
                </li>
              </ul>
            </div>
          </div>

          <div v-if="idPredioSelecionado" class="space-y-4 pt-1 animate-fade-in">

            <div class="flex flex-col gap-1.5 relative">
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Especifique o local (Sala, Laboratório ou Ambiente)
              </label>
              <div @click="toggleDropdownLocalizacao"
                   class="border border-gray-300 rounded-lg px-4 py-2.5 text-sm outline-none w-full cursor-pointer bg-white flex justify-between items-center transition-all min-h-[42px]"
                   :class="{'border-blue-600 ring-1 ring-blue-600': dropdownLocalAberto}">
                <span :class="salaNomeSelecionada ? 'text-gray-800 font-bold' : 'text-gray-400'">
                  {{ salaNomeSelecionada || 'Escolha a sala/ambiente...' }}
                </span>
                <svg class="w-4 h-4 text-gray-400 transition-transform" :class="{'rotate-180': dropdownLocalAberto}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>

              <div v-if="dropdownLocalAberto"
                   class="absolute left-0 right-0 top-[calc(100%+4px)] bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-48 overflow-y-auto">
                <ul class="py-1">
                  <li v-if="localizacoesFiltradas.length === 0" class="px-4 py-2 text-sm text-gray-400 italic">
                    Nenhum ambiente encontrado neste prédio.
                  </li>
                  <li v-else v-for="loc in localizacoesFiltradas" :key="loc.id_localizacao" @click="selecionarLocalizacao(loc)"
                      class="px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-800 cursor-pointer transition-colors">
                    {{ loc.desc_localizacao }}
                  </li>
                </ul>
              </div>
            </div>

            <!-- Equipamento: obrigatório para quem está logado, opcional na abertura anônima (aluno e funcionário) -->
            <div v-if="idLocalSelecionado" class="flex flex-col gap-1.5">
              <label for="ativo" class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Equipamento com problema{{ logado ? '' : ' (opcional)' }}
              </label>
              <select id="ativo" v-model="idAtivoSelecionado" data-testid="select-ativo"
                class="border border-gray-300 rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 w-full bg-white">
                <option v-if="logado" :value="null" disabled>
                  {{ ativosDoLocal.length ? 'Selecione o equipamento...' : 'Nenhum equipamento cadastrado neste local' }}
                </option>
                <option v-else :value="null">
                  {{ ativosDoLocal.length ? 'Não se aplica / outro problema' : 'Nenhum equipamento cadastrado neste local' }}
                </option>
                <option v-for="a in ativosDoLocal" :key="a.id_ativo" :value="a.id_ativo">
                  {{ ROTULO_TIPO_ATIVO[a.tipo_ativo] || a.tipo_ativo }} — PAT {{ a.codigo_patrimonial }}
                </option>
              </select>
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Observação / Descrição do problema
              </label>
              <textarea v-model="observacao" placeholder="Ex: Arrumar ar condicionado, projetor queimado, cadeira quebrada..."
                rows="3" class="border border-gray-300 rounded-lg px-4 py-2.5 text-sm outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 w-full resize-none transition-all">
              </textarea>
            </div>

            <!-- Evidências (imagens): somente nesta tela de abertura, tanto anônimo quanto logado -->
            <div class="flex flex-col gap-1.5" :data-testid="logado ? 'evidencias-abertura' : 'evidencias-anonimo'">
              <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Evidência (opcional)
              </label>
              <label
                :class="carregando ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:bg-blue-50'"
                class="flex items-center justify-center gap-2 border-2 border-dashed border-gray-300 rounded-lg py-3 text-xs font-bold text-blue-800 transition-colors">
                📎 Anexar foto do problema
                <input type="file" :accept="ACCEPT_IMAGENS" multiple class="hidden" :disabled="carregando" @change="aoEscolherImagens" />
              </label>
              <p class="text-[11px] text-gray-400">
                JPG, PNG ou WEBP, até {{ IMAGEM_TAMANHO_MAX_MB }} MB cada, no máximo {{ EVIDENCIAS_POR_ENVIO_MAX }} imagens.
              </p>

              <ul v-if="imagens.length" class="grid grid-cols-3 gap-2 mt-1">
                <li v-for="(img, i) in imagens" :key="img.url"
                  class="relative border border-gray-200 rounded-lg overflow-hidden bg-gray-50">
                  <img :src="img.url" :alt="img.arquivo.name" class="w-full h-20 object-cover" />
                  <button type="button" @click="removerImagem(i)" :disabled="carregando"
                    class="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/60 text-white text-[10px] font-bold flex items-center justify-center cursor-pointer hover:bg-red-600"
                    :aria-label="`Remover ${img.arquivo.name}`">✕</button>
                  <p class="text-[10px] text-gray-600 truncate px-1.5 py-1" :title="img.arquivo.name">{{ img.arquivo.name }}</p>
                </li>
              </ul>
              <p v-if="erroImagens" role="alert" class="text-[11px] font-medium text-red-600">{{ erroImagens }}</p>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4 pt-2">
          <button type="button" @click="voltar"
            class="py-3 rounded-lg border border-blue-800 text-blue-800 font-semibold hover:bg-blue-50 transition-all cursor-pointer text-center text-sm">
            Voltar
          </button>

          <button type="button" @click="enviarOS" :disabled="carregando"
            class="py-3 rounded-lg bg-blue-800 text-white font-semibold hover:bg-blue-700 transition-all cursor-pointer text-center text-sm disabled:bg-gray-400 disabled:cursor-not-allowed shadow-sm">
            {{ carregando ? 'A enviar...' : 'Enviar OS' }}
          </button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { EvidenciaError, enviarEvidencias } from '@/services/evidenciaService'
import {
  EVIDENCIAS_POR_ENVIO_MAX, IMAGEM_TAMANHO_MAX_MB, TIPOS_IMAGEM,
} from '@/utils/validacaoEvidencia'
import Swal from 'sweetalert2'

interface Ativo {
  id_ativo: number
  codigo_patrimonial: string
  tipo_ativo: string
  localizacao: number
}

interface Predio {
  id_predio: number
  nome_predio: string
}

interface Localizacao {
  id_localizacao: number
  desc_localizacao: string
  predio: number
}

interface ImagemSelecionada {
  arquivo: File
  url: string
}

const ROTULO_TIPO_ATIVO: Record<string, string> = { AR_CONDICIONADO: 'Ar-condicionado', BEBEDOURO: 'Bebedouro' }
const DESCRICAO_TAMANHO_MINIMO = 10
const ACCEPT_IMAGENS = TIPOS_IMAGEM.join(',')

const router = useRouter()
const authStore = useAuthStore()

// Logado, a OS fica vinculada ao solicitante (aparece em "Minhas Solicitações") e o backend exige o ativo.
const logado = computed(() => !!authStore.token && !!authStore.usuario)
const listaAtivos = ref<Ativo[]>([])
const idAtivoSelecionado = ref<number | null>(null)
const ativosDoLocal = computed(() => listaAtivos.value.filter(a => a.localizacao === idLocalSelecionado.value))

const tipoUsuario = ref('aluno')
const indentificacao = ref('')

const idPredioSelecionado = ref<number | null>(null)
const localNomeSelecionado = ref('')
const dropdownPredioAberto = ref(false)

const idLocalSelecionado = ref<number | null>(null)
const salaNomeSelecionada = ref('')
const dropdownLocalAberto = ref(false)

const observacao = ref('')
const carregando = ref(false)

const listaPredios = ref<Predio[]>([])
const listaLocalizacoes = ref<Localizacao[]>([])

// === Evidências (somente imagens, somente na abertura) ===
const imagens = ref<ImagemSelecionada[]>([])
const erroImagens = ref('')

const localizacoesFiltradas = computed(() => {
  if (!idPredioSelecionado.value) return []
  return listaLocalizacoes.value.filter(l => l.predio === idPredioSelecionado.value)
})

function toggleDropdownPredio() {
  dropdownPredioAberto.value = !dropdownPredioAberto.value
  dropdownLocalAberto.value = false
}

function toggleDropdownLocalizacao() {
  dropdownLocalAberto.value = !dropdownLocalAberto.value
  dropdownPredioAberto.value = false
}

function selecionarPredio(predio: Predio) {
  idPredioSelecionado.value = predio.id_predio
  localNomeSelecionado.value = predio.nome_predio
  dropdownPredioAberto.value = false

  idLocalSelecionado.value = null
  salaNomeSelecionada.value = ''
  idAtivoSelecionado.value = null
}

function selecionarLocalizacao(loc: Localizacao) {
  idLocalSelecionado.value = loc.id_localizacao
  salaNomeSelecionada.value = loc.desc_localizacao
  dropdownLocalAberto.value = false
  idAtivoSelecionado.value = null
}

function voltar() {
  router.push(logado.value ? '/dashboard-solicitante/portal' : '/')
}

/** Valida só imagens (JPG, PNG, WEBP), tamanho e quantidade, antes de enviar. */
function validarImagens(arquivos: File[]): string | null {
  if (arquivos.length > EVIDENCIAS_POR_ENVIO_MAX) return `Envie no máximo ${EVIDENCIAS_POR_ENVIO_MAX} imagens.`
  for (const arq of arquivos) {
    if (!TIPOS_IMAGEM.includes(arq.type)) return `"${arq.name}" não é uma imagem aceita (use JPG, PNG ou WEBP).`
    if (arq.size > IMAGEM_TAMANHO_MAX_MB * 1024 * 1024) return `"${arq.name}" passa de ${IMAGEM_TAMANHO_MAX_MB} MB.`
  }
  return null
}

function aoEscolherImagens(evento: Event) {
  const input = evento.target as HTMLInputElement
  const escolhidos = Array.from(input.files ?? [])
  input.value = ''

  const jaSelecionados = imagens.value.map(i => i.arquivo)
  const novos = escolhidos.filter(
    n => !jaSelecionados.some(a => a.name === n.name && a.size === n.size && a.lastModified === n.lastModified),
  )

  const erro = validarImagens([...jaSelecionados, ...novos])
  erroImagens.value = erro ?? ''
  if (erro) return

  imagens.value = [
    ...imagens.value,
    ...novos.map(arquivo => ({ arquivo, url: URL.createObjectURL(arquivo) })),
  ]
}

function removerImagem(indice: number) {
  const alvo = imagens.value[indice]
  if (alvo) URL.revokeObjectURL(alvo.url)
  imagens.value = imagens.value.filter((_, i) => i !== indice)
  erroImagens.value = ''
}

function liberarPreviews() {
  imagens.value.forEach(i => URL.revokeObjectURL(i.url))
  imagens.value = []
}

onBeforeUnmount(liberarPreviews)

async function inicializarDados() {
  try {
    const [resPredios, resLoc] = await Promise.all([
      api.get('/predio/'),
      api.get('/localizacao/'),
    ])
    listaPredios.value = resPredios.data.dados || resPredios.data
    listaLocalizacoes.value = resLoc.data.dados || resLoc.data
  } catch (e) {
    console.error('Erro ao buscar prédios e localizações:', e)
  }

  // Equipamentos: endpoint público e enxuto, usado por quem está logado e por quem não está.
  try {
    const resAtivos = await api.get('/ativo/publico/')
    listaAtivos.value = resAtivos.data.dados || resAtivos.data
  } catch (e) {
    console.error('Erro ao buscar equipamentos públicos:', e)
    // Quem está logado ainda pode usar a listagem autenticada como alternativa.
    if (logado.value) {
      try {
        const resAtivos = await api.get('/ativo/')
        listaAtivos.value = resAtivos.data.dados || resAtivos.data
      } catch (e2) {
        console.error('Erro ao buscar equipamentos:', e2)
      }
    }
  }
}

function mensagemDeErro(e: any): string {
  const dados = e.response?.data
  if (!e.response) return 'Falha ao conectar com o servidor. Tente novamente.'
  const erros = dados?.erros
  if (erros && typeof erros === 'object') {
    const primeiro = Object.values(erros)[0]
    if (primeiro) return Array.isArray(primeiro) ? String(primeiro[0]) : String(primeiro)
  }
  return dados?.mensagem || dados?.detail || 'Não foi possível abrir a ordem de serviço.'
}

/** US05: já existe corretiva em andamento para o ativo — oferece "também presenciei". */
async function tratarDuplicidade(dados: any, mensagem: string) {
  const existente = dados?.ordem_existente
  if (!existente) {
    Swal.fire({ title: 'Ordem já existente', text: mensagem, icon: 'info', confirmButtonColor: '#2563eb' })
    return
  }
  const detalhe = `OS #${existente.id_ordem_servico} (${existente.status_ordem_servico}) — ${existente.descricao_resumida}`

  if (dados.ja_vinculado) {
    await Swal.fire({ title: 'Você já acompanha esta ordem', text: detalhe, icon: 'info', confirmButtonColor: '#2563eb' })
    voltar()
    return
  }
  if (!dados.pode_presenciar) {
    Swal.fire({ title: 'Ordem já existente', html: `${mensagem}<br><br><small>${detalhe}</small>`, icon: 'info', confirmButtonColor: '#2563eb' })
    return
  }

  const escolha = await Swal.fire({
    title: 'Este problema já foi informado',
    html: `${mensagem}<br><br><small>${detalhe}</small>`,
    icon: 'question',
    showCancelButton: true,
    confirmButtonText: 'Também presenciei',
    cancelButtonText: 'Cancelar',
    confirmButtonColor: '#2563eb',
  })
  if (!escolha.isConfirmed) return

  try {
    await api.post(`/ordem-servico/${existente.id_ordem_servico}/presenciei/`)
    await Swal.fire({ title: 'Pronto!', text: 'Você passará a acompanhar esta ordem em "Minhas Solicitações".', icon: 'success', confirmButtonColor: '#2563eb' })
    voltar()
  } catch (e: any) {
    Swal.fire({ title: 'Erro', text: mensagemDeErro(e), icon: 'error', confirmButtonColor: '#ef4444' })
  }
}

/**
 * Anônimo com imagens: o envio vira multipart (campo "arquivos"), tudo numa única requisição.
 * Anônimo sem imagens e logado: segue como JSON (logado envia as imagens depois, na OS já criada).
 */
function montarCorpo(payload: Record<string, unknown>): Record<string, unknown> | FormData {
  if (logado.value || imagens.value.length === 0) return payload
  const form = new FormData()
  for (const [chave, valor] of Object.entries(payload)) {
    if (valor !== null && valor !== undefined) form.append(chave, String(valor))
  }
  imagens.value.forEach(i => form.append('arquivos', i.arquivo))
  return form
}

async function enviarOS() {
  const faltaIdentificacao = !logado.value && !indentificacao.value
  const faltaAtivo = logado.value && !idAtivoSelecionado.value
  if (faltaIdentificacao || faltaAtivo || !idPredioSelecionado.value || !idLocalSelecionado.value || !observacao.value.trim()) {
    const texto = faltaAtivo
      ? 'Selecione o equipamento com problema.'
      : 'Por favor, preencha todos os campos e selecione a Sala/Ambiente.'
    Swal.fire({ title: 'Atenção', text: texto, icon: 'warning', confirmButtonColor: '#2563eb' })
    return
  }
  if (observacao.value.trim().length < DESCRICAO_TAMANHO_MINIMO) {
    Swal.fire({ title: 'Atenção', text: `Descreva o problema com pelo menos ${DESCRICAO_TAMANHO_MINIMO} caracteres.`, icon: 'warning', confirmButtonColor: '#2563eb' })
    return
  }

  const erroImg = validarImagens(imagens.value.map(i => i.arquivo))
  if (erroImg) {
    erroImagens.value = erroImg
    return
  }

  try {
    carregando.value = true

    const payload: Record<string, unknown> = logado.value
      ? {
          localizacao: idLocalSelecionado.value,
          ativo: idAtivoSelecionado.value,
          descricao_servico: observacao.value.trim(),
          prioridade_urgencia: 'NAO'
        }
      : {
          localizacao: idLocalSelecionado.value,
          descricao_servico: `[${tipoUsuario.value.toUpperCase()}: ${indentificacao.value}] - Problema: ${observacao.value.trim()}`,
          prioridade_urgencia: 'NAO',
          // O equipamento é opcional na abertura anônima.
          ...(idAtivoSelecionado.value ? { ativo: idAtivoSelecionado.value } : {}),
        }

    const resposta = await api.post('/ordem-servico/', montarCorpo(payload))

    // Logado: a OS já existe, então as imagens são anexadas a ela agora.
    let avisoEvidencia = ''
    const idOrdem: number | undefined = resposta.data?.dados?.id_ordem_servico
    if (logado.value && imagens.value.length > 0 && idOrdem) {
      try {
        await enviarEvidencias(idOrdem, imagens.value.map(i => i.arquivo))
      } catch (e) {
        avisoEvidencia = e instanceof EvidenciaError
          ? e.info.mensagem
          : 'Não foi possível enviar as imagens.'
      }
    }

    if (avisoEvidencia) {
      await Swal.fire({
        title: 'OS aberta, mas sem as imagens',
        text: `A ordem foi registada, porém as evidências não foram enviadas: ${avisoEvidencia}`,
        icon: 'warning',
        confirmButtonColor: '#2563eb'
      })
    } else {
      await Swal.fire({
        title: 'Sucesso!',
        text: 'A sua Ordem de Serviço foi registada com sucesso.',
        icon: 'success',
        confirmButtonColor: '#2563eb'
      })
    }

    liberarPreviews()
    voltar()

  } catch (e: any) {
    console.error('Erro ao abrir OS:', e)
    if (e.response?.status === 409) {
      await tratarDuplicidade(e.response.data?.dados, e.response.data?.mensagem || '')
      return
    }
    Swal.fire({ title: 'Erro', text: mensagemDeErro(e), icon: 'error', confirmButtonColor: '#ef4444' })
  } finally {
    carregando.value = false
  }
}

onMounted(() => {
  inicializarDados()
})
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>